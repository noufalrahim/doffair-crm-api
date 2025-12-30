from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions,
)

from azure.storage.blob import BlobServiceClient
from core.config import settings

blob_service_client = BlobServiceClient.from_connection_string(
    settings.AZURE_BLOB_CONNECTION_STRING
)

CONTAINER_NAME = settings.AZURE_BLOB_CONTAINER

from azure.storage.blob import ContentSettings


def upload_blob(
    blob_path: str,
    content: bytes,
):
    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=blob_path,
    )

    blob_client.upload_blob(
        content,
        overwrite=True,
        content_settings=ContentSettings(
            content_type="image/jpeg",
            cache_control="public, max-age=31536000, immutable"
        ),
    )

    return blob_path



def generate_signed_url(blob_path: str, expiry_minutes: int = 60) -> str:
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=CONTAINER_NAME,
        blob_name=blob_path,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )

    return (
        f"{blob_service_client.primary_endpoint}/"
        f"{CONTAINER_NAME}/{blob_path}?{sas_token}"
    )
