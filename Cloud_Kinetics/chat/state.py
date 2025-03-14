import os
import reflex as rx
import boto3
import logging
import json
from datetime import datetime
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv
from typing import List, Dict, Any
from Cloud_Kinetics.chat.upload_to_s3 import upload_to_s3
from fastapi import UploadFile

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Starting state.py execution")
if not load_dotenv():
    logger.error("Failed to load .env file - ensure it exists in the project root")
else:
    logger.debug(f"Environment variables loaded: AWS_REGION={os.getenv('AWS_DEFAULT_REGION')}")

# Initialize boto3 with static credentials from .env
try:
    boto3.setup_default_session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    )
    dynamodb = boto3.resource('dynamodb')
    chat_table = dynamodb.Table('ChatSession')

    # Fetch caller identity
    sts_client = boto3.client('sts')
    identity = sts_client.get_caller_identity()
    aws_user_id = identity['Arn']
    logger.debug(f"Fetched AWS identity: {identity}")
    logger.debug("Successfully initialized boto3 with static credentials")
except Exception as e:
    logger.error(f"Failed to initialize boto3 with static credentials: {str(e)}", exc_info=True)
    raise

# def create_chat_session_table():
#     try:
#         dynamodb_client = boto3.client('dynamodb')
#         dynamodb_client.describe_table(TableName='ChatSession')
#         logger.debug("Table 'ChatSession' already exists")
#     except dynamodb_client.exceptions.ResourceNotFoundException:
#         dynamodb.create_table(
#             TableName='ChatSession',
#             KeySchema=[
#                 {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
#                 {'AttributeName': 'session_id', 'KeyType': 'RANGE'}  # Sort key
#             ],
#             AttributeDefinitions=[
#                 {'AttributeName': 'user_id', 'AttributeType': 'S'},
#                 {'AttributeName': 'session_id', 'AttributeType': 'S'}
#             ],
#             BillingMode='PAY_PER_REQUEST'
#         )
#         dynamodb.meta.client.get_waiter('table_exists').wait(TableName='ChatSession')
#         logger.info("Created 'ChatSession' table in DynamoDB")

# create_chat_session_table()

class QA(rx.Base):
    """A question and answer pair."""
    question: str
    answer: str

DEFAULT_CHATS = {
    "Intros": [],
}

class State(rx.State):
    """The app state."""
    chats: Dict[str, List[QA]] = DEFAULT_CHATS
    current_chat: str = "Intros"
    question: str = ""
    processing: bool = False
    new_chat_name: str = ""
    uploaded_files: List[str] = []
    upload_error: str = ""
    uploading: bool = False
    progress: int = 0
    total_bytes: int = 0
    user_id: str = aws_user_id
    session_ids: Dict[str, str] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{k: v for k, v in kwargs.items() if k != 'parent_state'})
        self.load_session()

    def create_chat(self):
        logger.debug(f"Attempting to create chat with name: {self.new_chat_name}")
        if not self.new_chat_name.strip():
            logger.warning("New chat name is empty")
            return
        chat_name = self.new_chat_name.strip()
        if chat_name in self.chats:
            logger.warning(f"Chat '{chat_name}' already exists")
            return
        self.chats[chat_name] = []
        self.current_chat = chat_name
        self.new_chat_name = ""
        logger.info(f"Created new chat in state: {chat_name}")

        session_id = f"Session#{datetime.utcnow().isoformat()}Z"
        item = {
            "user_id": self.user_id,
            "session_id": session_id,
            "chat_name": chat_name,
            "messages": []  # Start with empty message list
        }
        try:
            chat_table.put_item(Item=item)
            self.session_ids[chat_name] = session_id  # Track session_id
            logger.info(f"Saved new chat '{chat_name}' to DynamoDB with session_id: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save chat to DynamoDB: {str(e)}", exc_info=True)
            raise

    def delete_chat(self):
        logger.debug(f"Attempting to delete chat: {self.current_chat}")
        if self.current_chat not in self.chats:
            logger.warning(f"Attempted to delete non-existent chat: {self.current_chat}")
            return

        chat_titles = list(self.chats.keys())
        current_index = chat_titles.index(self.current_chat)

        try:
            response = chat_table.query(
                KeyConditionExpression="user_id = :uid AND begins_with(session_id, :sid)",
                ExpressionAttributeValues={":uid": self.user_id, ":sid": self.current_chat}
            )
            logger.debug(f"Query response for deletion: {response}")
            for item in response.get("Items", []):
                if item["chat_name"] == self.current_chat:
                    chat_table.delete_item(
                        Key={"user_id": self.user_id, "session_id": item["session_id"]}
                    )
                    logger.info(f"Deleted chat '{self.current_chat}' from DynamoDB")
                    break
        except Exception as e:
            logger.error(f"Failed to delete chat from DynamoDB: {str(e)}", exc_info=True)

        del self.chats[self.current_chat]
        logger.info(f"Deleted chat from state: {self.current_chat}")

        if not self.chats:
            self.chats = DEFAULT_CHATS.copy()
            self.current_chat = "Intros"
            logger.info("No chats remain, created new default 'Intros'")
            session_id = f"Intros#{datetime.utcnow().isoformat()}Z"
            try:
                chat_table.put_item(
                    Item={
                        "user_id": self.user_id,
                        "session_id": session_id,
                        "chat_name": "Intros",
                        "chat_history": [],
                    }
                )
                logger.info("Saved default 'Intros' to DynamoDB")
            except Exception as e:
                logger.error(f"Failed to save default 'Intros' to DynamoDB: {str(e)}", exc_info=True)
        else:
            remaining_chats = list(self.chats.keys())
            new_index = min(current_index, len(remaining_chats) - 1) if current_index < len(remaining_chats) else 0
            self.current_chat = remaining_chats[new_index]
            logger.info(f"Switched to chat: {self.current_chat}")

        self.chats = self.chats

    def set_chat(self, chat_name: str):
        logger.debug(f"Attempting to set chat to: {chat_name}")
        if chat_name not in self.chats:
            logger.warning(f"Chat '{chat_name}' does not exist")
            if not self.chats:
                self.chats = DEFAULT_CHATS.copy()
                self.current_chat = "Intros"
                logger.info("Chat history empty, created new default 'Intros'")
                session_id = f"Intros#{datetime.utcnow().isoformat()}Z"
                try:
                    chat_table.put_item(
                        Item={
                            "user_id": self.user_id,
                            "session_id": session_id,
                            "chat_name": "Intros",
                            "chat_history": [],
                        }
                    )
                    logger.info("Saved default 'Intros' to DynamoDB")
                except Exception as e:
                    logger.error(f"Failed to save default 'Intros' to DynamoDB: {str(e)}", exc_info=True)
            else:
                self.current_chat = list(self.chats.keys())[0]
                logger.info(f"Chat '{chat_name}' deleted or invalid, switched to: {self.current_chat}")
            self.chats = self.chats
            return
        self.current_chat = chat_name
        logger.info(f"Switched to chat: {chat_name}")

    def reset_session(self):
        logger.debug("Attempting to reset session")
        self.chats = DEFAULT_CHATS.copy()
        self.current_chat = "Intros"
        self.processing = False
        logger.info("Session reset to default state in memory")
        try:
            response = chat_table.scan(FilterExpression="user_id = :uid", ExpressionAttributeValues={":uid": self.user_id})
            logger.debug(f"Scan response for reset: {response}")
            for item in response.get("Items", []):
                chat_table.delete_item(Key={"user_id": self.user_id, "session_id": item["session_id"]})
            session_id = f"Intros#{datetime.utcnow().isoformat()}Z"
            chat_table.put_item(
                Item={
                    "user_id": self.user_id,
                    "session_id": session_id,
                    "chat_name": "Intros",
                    "chat_history": [],
                }
            )
            logger.info(f"Reset DynamoDB session for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to reset DynamoDB session: {str(e)}", exc_info=True)
        self.chats = self.chats

    @rx.var(cache=True)
    def chat_titles(self) -> List[str]:
        titles = list(self.chats.keys())
        logger.debug(f"Chat titles retrieved: {titles}")
        return titles

    async def process_question(self, form_data: Dict[str, Any]):
        logger.debug(f"Processing question: {form_data}")
        question = form_data.get("question", "").strip()
        if not question:
            logger.warning("Question is empty, skipping processing")
            return
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)
        self.processing = True
        logger.info(f"Added question to chat '{self.current_chat}': {question}")
        yield

        knowledge_base = await self.get_knowledge_base()
        prompt = (
            "You are a helpful assistant. Use the following information as your knowledge base "
            "to answer the question. If the information below is insufficient, say so and do not "
            "rely on pretrained data.\n\n"
            "Human: Here is the knowledge base:\n"
            f"{knowledge_base}\n\n"
            f"Now, please answer this question: {question}\n\n"
            "Assistant:"
        )

        client = boto3.client("bedrock-runtime", region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'))
        model_id = "anthropic.claude-v2"
        body = json.dumps({"prompt": prompt, "max_tokens_to_sample": 2000, "temperature": 0.7})

        try:
            response = client.invoke_model(
                modelId=model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            response_body = json.loads(response["body"].read())
            answer = response_body.get("completion", "").strip()
            logger.info(f"Received answer from Bedrock: {answer[:50]}...")
        except Exception as e:
            logger.error(f"Error calling AWS Bedrock: {str(e)}", exc_info=True)
            answer = "Sorry, I encountered an error while processing your request."

        self.chats[self.current_chat][-1].answer = answer
        self.processing = False
        logger.info(f"Updated chat '{self.current_chat}' with answer")

        # Update DynamoDB by appending to messages
        session_id = self.session_ids.get(self.current_chat)
        if not session_id:
            logger.warning(f"No session_id found for '{self.current_chat}', creating new session")
            session_id = f"Session#{datetime.utcnow().isoformat()}Z"
            self.session_ids[self.current_chat] = session_id

        try:
            # Fetch existing session
            response = chat_table.get_item(
                Key={"user_id": self.user_id, "session_id": session_id}
            )
            existing_item = response.get("Item", {})
            existing_messages = existing_item.get("messages", [])

            # Append new message
            new_message = {"question": qa.question, "answer": qa.answer}
            existing_messages.append(new_message)

            # Update item
            chat_table.put_item(
                Item={
                    "user_id": self.user_id,
                    "session_id": session_id,
                    "chat_name": self.current_chat,
                    "messages": existing_messages
                }
            )
            logger.info(f"Appended message to session '{session_id}' in DynamoDB")
        except Exception as e:
            logger.error(f"Failed to update session in DynamoDB: {str(e)}", exc_info=True)
            raise

        self.chats = self.chats
        yield

    # async def load_session(self):
    #     logger.debug(f"Loading sessions for user: {self.user_id}")
    #     try:
    #         response = chat_table.query(
    #             KeyConditionExpression="user_id = :uid",
    #             ExpressionAttributeValues={":uid": self.user_id}
    #         )
    #         items = response.get("Items", [])
    #         logger.debug(f"Query response: {items}")
    #         if not items:
    #             self.chats = DEFAULT_CHATS.copy()
    #             self.current_chat = "Intros"
    #             session_id = f"Session#{datetime.utcnow().isoformat()}Z"
    #             chat_table.put_item(
    #                 Item={
    #                     "user_id": self.user_id,
    #                     "session_id": session_id,
    #                     "chat_name": "Intros",
    #                     "messages": []
    #                 }
    #             )
    #             self.session_ids["Intros"] = session_id
    #             logger.info(f"Initialized default 'Intros' session for user {self.user_id}")
    #         else:
    #             self.chats = {}
    #             self.session_ids = {}
    #             for item in items:
    #                 chat_name = item["chat_name"]
    #                 messages = item.get("messages", [])
    #                 self.chats[chat_name] = [QA(question=m["question"], answer=m["answer"]) for m in messages]
    #                 self.session_ids[chat_name] = item["session_id"]
    #             self.current_chat = list(self.chats.keys())[0]
    #             logger.info(f"Loaded sessions for user {self.user_id}: {list(self.chats.keys())}")
    #         self.chats = self.chats
    #     except Exception as e:
    #         logger.error(f"Failed to load sessions from DynamoDB: {str(e)}", exc_info=True)
    #         self.chats = DEFAULT_CHATS.copy()
    #         self.current_chat = "Intros"

    def load_session(self):
        """Load chat sessions from DynamoDB for the current user."""
        logger.debug(f"Loading sessions for user: {self.user_id}")
        try:
            # Query DynamoDB for all items with the user's ID
            response = chat_table.query(
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": self.user_id}
            )
            items = response.get("Items", [])
            logger.debug(f"DynamoDB query response: {items}")

            if not items:
                # No sessions found, initialize with default "Intros" chat
                self.chats = DEFAULT_CHATS.copy()
                self.current_chat = "Intros"
                session_id = f"Session#{datetime.utcnow().isoformat()}Z"
                chat_table.put_item(
                    Item={
                        "user_id": self.user_id,
                        "session_id": session_id,
                        "chat_name": "Intros",
                        "messages": []
                    }
                )
                self.session_ids["Intros"] = session_id
                logger.info(f"Created default 'Intros' session for user {self.user_id}")
            else:
                # Load existing sessions
                self.chats = {}
                self.session_ids = {}
                for item in items:
                    chat_name = item["chat_name"]
                    session_id = item["session_id"]
                    messages = item.get("messages", [])
                    # Avoid duplicate chat names by appending session_id if needed
                    unique_chat_name = chat_name if chat_name not in self.chats else f"{chat_name}_{session_id}"
                    self.chats[unique_chat_name] = [QA(question=m["question"], answer=m["answer"]) for m in messages]
                    self.session_ids[unique_chat_name] = session_id
                    logger.debug(f"Loaded chat '{unique_chat_name}' with {len(messages)} messages")
                self.current_chat = list(self.chats.keys())[0]  # Set to first chat
                logger.info(f"Loaded sessions for user {self.user_id}: {list(self.chats.keys())}")

            # Ensure UI updates with loaded data
            self.chats = self.chats
        except ClientError as e:
            logger.error(f"DynamoDB error: {str(e)}")
            self.chats = DEFAULT_CHATS.copy()
            self.current_chat = "Intros"
            self.session_ids = {"Intros": f"Session#{datetime.utcnow().isoformat()}Z"}
        except Exception as e:
            logger.error(f"Unexpected error loading sessions: {str(e)}")
            self.chats = DEFAULT_CHATS.copy()
            self.current_chat = "Intros"
            self.session_ids = {"Intros": f"Session#{datetime.utcnow().isoformat()}Z"}

    async def get_knowledge_base(self) -> str:
        """Retrieve content from all files under the specified S3 prefix."""
        s3_client = boto3.client('s3')
        bucket_name = os.getenv("S3_BUCKET_NAME")
        prefix = os.getenv("S3_OBJECT_NAME", "")  # e.g., "nhqb-cloud-kinetics-bucket/"
        
        if not bucket_name:
            logger.error("S3_BUCKET_NAME not set in environment variables.")
            return "No S3 bucket configured."
        if not prefix:
            logger.warning("S3_OBJECT_NAME not set; fetching from bucket root.")

        knowledge_base = []
        try:
            # List all objects under the prefix in the bucket
            response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' not in response:
                return f"No files found under {prefix} in S3 bucket {bucket_name}."

            for obj in response['Contents']:
                object_name = obj['Key']
                try:
                    file_response = s3_client.get_object(Bucket=bucket_name, Key=object_name)
                    content = file_response['Body'].read().decode('utf-8')
                    knowledge_base.append(f"File: {object_name}\n{content}")
                except Exception as e:
                    logger.error(f"Error fetching {object_name} from S3: {e}")
        except Exception as e:
            logger.error(f"Error listing objects in S3 bucket {bucket_name} with prefix {prefix}: {e}")
            return "Error accessing S3 bucket."

        return "\n\n".join(knowledge_base) if knowledge_base else "No knowledge base available."
    
    async def bedrock_process_question(self, question: str):
        """Get the response from AWS Bedrock using uploaded resources as knowledge base."""
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)
        self.processing = True
        yield

        # Fetch knowledge base from uploaded files
        knowledge_base = await self.get_knowledge_base()

        # Build the prompt with the knowledge base
        prompt = (
            "You are a helpful assistant. Use the following information as your knowledge base "
            "to answer the question. If the information below is insufficient, say so and do not "
            "rely on pretrained data.\n\n"
            "Human: Here is the knowledge base:\n"
            f"{knowledge_base}\n\n"
            f"Now, please answer this question: {question}\n\n"
            "Assistant:"
        )

        # Initialize the Bedrock Runtime client
        client = boto3.client("bedrock-runtime", region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))

        # Define the model ID
        model_id = "anthropic.claude-v2"  # Replace with your desired model ID

        # Prepare the request body
        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 2000,
            "temperature": 0.7,
        })

        try:
            # Invoke the Bedrock model
            response = client.invoke_model(
                modelId=model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            response_body = json.loads(response["body"].read())
            answer = response_body.get("completion", "").strip()
        except Exception as e:
            logger.error(f"Error calling AWS Bedrock: {e}")
            answer = "Sorry, I encountered an error while processing your request."

        self.chats[self.current_chat][-1].answer = answer
        self.chats = self.chats
        self.processing = False
        yield

    @rx.event
    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle file upload to S3."""
        logger.debug("handle_upload called with files: %s", files)
        if not files:
            logger.warning("No files selected for upload.")
            self.upload_error = "Please select a file before uploading."
            return
        bucket_name = os.getenv("S3_BUCKET_NAME")
        object_prefix = "nhqb-cloud-kinetics-bucket/"  # Hardcoded for now, or use os.getenv("S3_OBJECT_PREFIX", "nhqb-cloud-kinetics-bucket/")
        if not bucket_name:
            logger.error("S3_BUCKET_NAME not set in environment variables.")
            self.upload_error = "S3 configuration error. Contact support."
            return
        try:
            file = files[0]  # Only one file due to max_files=1
            clean_filename = file.filename.lstrip("./")  # Remove ./ from filename
            object_name = f"{object_prefix}{clean_filename}"  # Prepend desired directory
            logger.debug(f"Uploading to S3 with bucket: {bucket_name}, object_name: {object_name}")
            content = await file.read()
            self.total_bytes += len(content)
            await upload_to_s3(file, bucket_name, object_name)
            self.uploaded_files.append(object_name)
            self.uploaded_files = self.uploaded_files  # Trigger state update
            logger.info(f"Successfully uploaded {file.filename} to S3 at {object_name}")
            self.upload_error = ""
            self.uploading = False
            return rx.redirect("/")  # Redirect on success
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            self.upload_error = f"Upload failed: {str(e)}"
            self.uploading = False
            return

    def handle_upload_progress(self, progress: dict):
        """Update progress during upload."""
        logger.debug("Upload progress: %s", progress)
        self.uploading = True
        self.progress = round(progress["progress"] * 100)
        if self.progress >= 100:
            self.uploading = False
    
    @rx.event
    def cancel_upload(self):
        """Cancel the upload process."""
        logger.debug("Upload cancelled")
        self.uploading = False
        self.progress = 0
        self.upload_error = "Upload cancelled."
        return rx.cancel_upload("upload_s3")