import os
import reflex as rx
import boto3
import logging
import json
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
from typing import List, Dict, Any
from Cloud_Kinetics.chat.upload_to_s3 import upload_to_s3
from fastapi import UploadFile

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Checking if the AWS credentials are set properly
try:
    boto3.client('sts').get_caller_identity()
except (NoCredentialsError, PartialCredentialsError):
    raise Exception("Please set AWS credentials properly.")

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
    uploaded_files: List[str] = []  # Track S3 object keys of uploaded files
    upload_error: str = ""
    uploading: bool = False
    progress: int = 0
    total_bytes: int = 0

    def create_chat(self):
        """Create a new chat."""
        if not self.new_chat_name.strip():
            logger.warning("New chat name is empty.")
            return
        chat_name = self.new_chat_name.strip()
        if chat_name in self.chats:
            logger.warning(f"Chat '{chat_name}' already exists.")
            return
        self.chats[chat_name] = []
        self.current_chat = chat_name
        self.new_chat_name = ""  # Reset input field
        logger.info(f"Created new chat: {chat_name}")

    def delete_chat(self):
        """Delete the current chat and set the next logical chat as default."""
        if self.current_chat not in self.chats:
            logger.warning(f"Attempted to delete non-existent chat: {self.current_chat}")
            return

        # Get the list of chat titles before deletion
        chat_titles = list(self.chats.keys())
        current_index = chat_titles.index(self.current_chat)

        # Delete the current chat
        del self.chats[self.current_chat]
        logger.info(f"Deleted chat: {self.current_chat}")

        # If no chats remain, create a new 'Intros'
        if not self.chats:
            self.chats = DEFAULT_CHATS.copy()  # Use copy to avoid mutating DEFAULT_CHATS
            self.current_chat = "Intros"
            logger.info("No chats remain, created new default 'Intros'")
        else:
            # Use the updated chat list after deletion
            remaining_chats = list(self.chats.keys())
            # If it was the last chat, go to the previous one; otherwise, go to the next or first
            new_index = min(current_index, len(remaining_chats) - 1) if current_index < len(remaining_chats) else 0
            self.current_chat = remaining_chats[new_index]
            logger.info(f"Switched to chat: {self.current_chat}")

        # Force state update to trigger UI re-render
        self.chats = self.chats

    def set_chat(self, chat_name: str):
        """Set the name of the current chat, fallback to a valid chat or create new if needed."""
        if chat_name not in self.chats:
            logger.warning(f"Chat '{chat_name}' does not exist.")
            if not self.chats:  # If chat history is empty, create a new 'Intros'
                self.chats = DEFAULT_CHATS.copy()
                self.current_chat = "Intros"
                logger.info("Chat history empty, created new default 'Intros'")
            else:  # Set to the first available chat
                self.current_chat = list(self.chats.keys())[0]
                logger.info(f"Chat '{chat_name}' deleted or invalid, switched to: {self.current_chat}")
            # Force state update
            self.chats = self.chats
            return
        self.current_chat = chat_name
        logger.debug(f"Switched to chat: {chat_name}")
        # Optional: self.chats = self.chats here if needed, but not necessary for valid chat switch

    def reset_session(self):
        """Reset the session."""
        self.chats = DEFAULT_CHATS.copy()
        self.current_chat = "Intros"
        self.processing = False
        logger.info("Session reset to default state.")
        self.chats = self.chats  # Ensure UI updates

    @rx.var(cache=True)
    def chat_titles(self) -> List[str]:
        """Get the list of chat titles."""
        return list(self.chats.keys())

    async def process_question(self, form_data: Dict[str, Any]):
        """Process the user's question."""
        question = form_data.get("question", "")
        if not question:
            return
        model = self.bedrock_process_question
        async for value in model(question):
            yield value

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