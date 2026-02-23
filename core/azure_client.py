import logging
import os
import asyncio
from typing import Optional
from uuid import uuid4
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from fastapi import HTTPException, UploadFile, status
from datetime import datetime, timedelta
from core.config import settings

logger = logging.getLogger(__name__)

# Set logging level for Azure to avoid too much noise
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)

# Initialize clients globally as per reference
blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_BLOB_CONNECTION_STRING)
image_container_client = blob_service_client.get_container_client(settings.AZURE_BLOB_CONTAINER)

async def upload_file_to_blob(user_id: str, upload_file: UploadFile, image_type: Optional[str] = None) -> str:
    """
    Uploads a file to Azure Blob Storage asynchronously.
    """
    try:
        # Read file content from memory
        file_content = await upload_file.read()

        file_extension = os.path.splitext(upload_file.filename)[1]
        file_path = f"{user_id}/{image_type}/{uuid4()}{file_extension}"

        # Upload the file content to blob storage
        await image_container_client.upload_blob(
            file_path, file_content, metadata={"user_id": str(user_id)}, overwrite=True
        )

        return file_path
    except Exception as e:
        logger.error(f"Failed to upload {upload_file.filename} due to: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload {upload_file.filename} due to: {e}")

async def delete_file_from_blob(file_name: str) -> None:
    """
    Deletes a file from Azure Blob Storage asynchronously.
    """
    try:
        # Attempt to delete the blob
        await image_container_client.delete_blob(file_name, delete_snapshots='include')
    except ResourceNotFoundError:
        logger.error(f'Failed to delete "{file_name}" as it does not exist')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Failed to delete "{file_name}" as it does not exist')
    except Exception as e:
        logger.error(f'Failed to delete "{file_name}" due to: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete {file_name} due to: {e}")

def generate_blob_sas_url(blob_path: str, expiry_hours: int = 24) -> str:
    """
    Generate a signed URL for a blob.
    """
    try:
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=settings.AZURE_BLOB_CONTAINER,
            blob_name=blob_path,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        return f"{blob_service_client.primary_endpoint}{settings.AZURE_BLOB_CONTAINER}/{blob_path}?{sas_token}"
    except Exception as e:
        logger.error(f"Failed to generate signed URL for {blob_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating download URL: {str(e)}")

async def download_file_from_blob(file_name: str) -> bytes:
    """
    Downloads a file from Azure Blob Storage asynchronously.
    """
    try:
        # Download the file content from blob storage
        download_stream = await image_container_client.download_blob(file_name, max_concurrency=5)
        return await download_stream.readall()
    except ResourceNotFoundError:
        logger.error(f'Failed to download "{file_name}" as it does not exist')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Failed to download "{file_name}" as it does not exist')
    except Exception as e:
        logger.error(f'Failed to download "{file_name}" due to: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download {file_name} due to: {e}")
