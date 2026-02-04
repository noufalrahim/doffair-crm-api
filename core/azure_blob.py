"""
Azure Blob Storage utility for file uploads
Handles prescription and other document uploads to Azure Blob Storage
"""
import os
import uuid
from typing import Optional, BinaryIO
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class AzureBlobService:
    """
    Service for uploading files to Azure Blob Storage
    Thread-safe singleton pattern
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureBlobService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_BLOB_CONNECTION_STRING
            )
            self.container_name = settings.AZURE_BLOB_CONTAINER
            self._initialized = True
            logger.info(f"✅ Azure Blob Service initialized - Container: {self.container_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure Blob Service: {str(e)}")
            raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        folder_path: str,
        content_type: str = "application/octet-stream"
    ) -> dict:
        """
        Upload file to Azure Blob Storage
        
        Args:
            file_data: File binary data
            file_name: Original filename
            folder_path: Folder structure (e.g., "prescriptions/vendor_id/customer_id")
            content_type: MIME type
        
        Returns:
            dict with blob_url, blob_path, file_name, file_size
        """
        try:
            # Generate unique filename to avoid conflicts
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Construct blob path
            blob_path = f"{folder_path}/{unique_filename}"
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Set content settings for proper MIME type
            content_settings = ContentSettings(content_type=content_type)
            
            # Upload file
            file_data.seek(0)  # Reset file pointer to beginning
            blob_client.upload_blob(
                file_data,
                content_settings=content_settings,
                overwrite=True
            )
            
            # Get blob properties for file size
            blob_properties = blob_client.get_blob_properties()
            file_size = blob_properties.size
            
            # Construct URLs
            blob_url = blob_client.url
            cdn_url = None
            
            # If CDN is configured, use CDN URL
            if hasattr(settings, 'AZURE_CDN_BASE_URL') and settings.AZURE_CDN_BASE_URL:
                cdn_url = f"{settings.AZURE_CDN_BASE_URL}/{blob_path}"
            
            logger.info(f"✅ File uploaded: {blob_path} ({file_size} bytes)")
            
            return {
                "blob_url": blob_url,
                "blob_path": blob_path,
                "file_name": file_name,
                "file_size": file_size,
                "cdn_url": cdn_url
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload file {file_name}: {str(e)}")
            raise
    
    def delete_file(self, blob_path: str) -> bool:
        """
        Delete file from Azure Blob Storage
        
        Args:
            blob_path: Full path to blob
        
        Returns:
            True if successful, False otherwise
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            blob_client.delete_blob()
            logger.info(f"✅ File deleted: {blob_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete file {blob_path}: {str(e)}")
            return False
    
    def get_file_url(self, blob_path: str, expiry_hours: int = 24) -> str:
        """
        Get temporary signed URL for file access
        
        Args:
            blob_path: Path to blob
            expiry_hours: Hours until URL expires
        
        Returns:
            Signed URL with SAS token
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=blob_path,
                account_key=self.blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            return f"{blob_client.url}?{sas_token}"
            
        except Exception as e:
            logger.error(f"❌ Failed to generate signed URL for {blob_path}: {str(e)}")
            raise
    
    def file_exists(self, blob_path: str) -> bool:
        """
        Check if file exists in blob storage
        
        Args:
            blob_path: Path to blob
        
        Returns:
            True if exists, False otherwise
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            return blob_client.exists()
        except Exception as e:
            logger.error(f"❌ Error checking file existence {blob_path}: {str(e)}")
            return False


# Singleton instance
azure_blob_service = AzureBlobService()
