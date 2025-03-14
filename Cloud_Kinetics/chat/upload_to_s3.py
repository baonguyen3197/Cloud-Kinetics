# Cloud_Kinetics/chat/upload_to_s3.py
import boto3
import logging
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def upload_to_s3(file: UploadFile, bucket_name: str, object_name: str):
    s3_client = boto3.client('s3')
    try:
        content = await file.read()
        s3_client.put_object(Body=content, Bucket=bucket_name, Key=object_name)
        logger.info(f"Uploaded {file.filename} to s3://{bucket_name}/{object_name}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise