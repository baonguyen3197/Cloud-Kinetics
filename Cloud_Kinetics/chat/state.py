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
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat."""
        self.current_chat = chat_name

    def reset_session(self):
        """Reset the session."""
        self.chats = DEFAULT_CHATS
        self.current_chat = "Intros"
        self.processing = False

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

    @rx.event
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