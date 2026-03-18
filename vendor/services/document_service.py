from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException, UploadFile
from typing import List, Optional

from vendor.models.document import Document
from vendor.schemas.document import DocumentUpdate
from core.azure_client import upload_file_to_blob, delete_file_from_blob

async def upload_document(
    engine: AIOEngine, 
    vendor_id: str, 
    file: UploadFile, 
    name: str, 
    doc_type: str, 
    description: Optional[str] = None
) -> Document:
    # Upload to Azure Blob Storage
    # The current template from vendor/routers/media.py uses image_type as a folder
    blob_path = await upload_file_to_blob(vendor_id, file, f"documents/{doc_type}")
    
    document = Document(
        vendor_id=vendor_id,
        name=name,
        link=blob_path,
        type=doc_type,
        description=description
    )
    await engine.save(document)
    return document

async def get_document_by_id(engine: AIOEngine, vendor_id: str, doc_id: str) -> Document:
    document = await engine.find_one(Document, Document.id == ObjectId(doc_id), Document.vendor_id == vendor_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

async def list_documents(
    engine: AIOEngine, 
    vendor_id: str, 
    doc_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Document]:
    query = [Document.vendor_id == vendor_id]
    if doc_type:
        query.append(Document.type == doc_type)
    if is_active is not None:
        query.append(Document.is_active == is_active)
    if search:
        query.append(Document.name.match(f"(?i).*{search}.*"))
    
    documents = await engine.find(Document, *query)
    return documents

async def update_document(engine: AIOEngine, vendor_id: str, doc_id: str, data: DocumentUpdate) -> Document:
    document = await get_document_by_id(engine, vendor_id, doc_id)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(document, key, value)
    
    document.updated_at = datetime.utcnow()
    await engine.save(document)
    return document

async def delete_document(engine: AIOEngine, vendor_id: str, doc_id: str) -> bool:
    document = await get_document_by_id(engine, vendor_id, doc_id)
    
    # Delete from Azure Blob Storage
    try:
        await delete_file_from_blob(document.link)
    except Exception:
        # Log error but continue with DB deletion
        pass
        
    await engine.delete(document)
    return True
