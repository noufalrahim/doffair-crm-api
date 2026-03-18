from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from odmantic import AIOEngine
from typing import Optional

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response
from vendor.services.document_service import (
    upload_document,
    get_document_by_id,
    list_documents,
    update_document,
    delete_document
)
from schemas.common import APIResponse
from vendor.schemas.document import (
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse
)

router = APIRouter(
    prefix="/vendor/documents",
    tags=["Vendor - Documents"]
)

@router.post("/upload", response_model=APIResponse)
async def upload_document_endpoint(
    name: str = Form(..., description="Name of the document"),
    doc_type: str = Form(..., description="Type of document (e.g., kyc, invoice)"),
    description: Optional[str] = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="File to upload"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Upload a new document and save metadata.
    """
    vendor_id = current_vendor["vendor_id"]
    document = await upload_document(engine, vendor_id, file, name, doc_type, description)
    
    response_data = DocumentResponse(
        id=str(document.id),
        vendor_id=document.vendor_id,
        name=document.name,
        link=document.link,
        type=document.type,
        description=document.description,
        is_verified=document.is_verified,
        message=document.message,
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at
    )
    
    return success_response(
        message="Document uploaded successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("", response_model=APIResponse)
async def list_documents_endpoint(
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List all documents for the vendor.
    """
    vendor_id = current_vendor["vendor_id"]
    documents = await list_documents(engine, vendor_id, doc_type, is_active, search)
    
    doc_responses = [
        DocumentResponse(
            id=str(d.id),
            vendor_id=d.vendor_id,
            name=d.name,
            link=d.link,
            type=d.type,
            description=d.description,
            is_verified=d.is_verified,
            message=d.message,
            is_active=d.is_active,
            created_at=d.created_at,
            updated_at=d.updated_at
        ).model_dump()
        for d in documents
    ]
    
    response_data = DocumentListResponse(
        total=len(doc_responses),
        items=doc_responses
    )
    
    return success_response(
        message="Documents retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("/{doc_id}", response_model=APIResponse)
async def get_document_endpoint(
    doc_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get detailed information about a specific document.
    """
    vendor_id = current_vendor["vendor_id"]
    document = await get_document_by_id(engine, vendor_id, doc_id)
    
    response_data = DocumentResponse(
        id=str(document.id),
        vendor_id=document.vendor_id,
        name=document.name,
        link=document.link,
        type=document.type,
        description=document.description,
        is_verified=document.is_verified,
        message=document.message,
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at
    )
    
    return success_response(
        message="Document retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.patch("/{doc_id}", response_model=APIResponse)
async def update_document_endpoint(
    doc_id: str,
    data: DocumentUpdate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Update an existing document metadata.
    """
    vendor_id = current_vendor["vendor_id"]
    document = await update_document(engine, vendor_id, doc_id, data)
    
    response_data = DocumentResponse(
        id=str(document.id),
        vendor_id=document.vendor_id,
        name=document.name,
        link=document.link,
        type=document.type,
        description=document.description,
        is_verified=document.is_verified,
        message=document.message,
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at
    )
    
    return success_response(
        message="Document updated successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.delete("/{doc_id}", response_model=APIResponse)
async def delete_document_endpoint(
    doc_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Delete a document and its file.
    """
    vendor_id = current_vendor["vendor_id"]
    await delete_document(engine, vendor_id, doc_id)
    
    return success_response(
        message="Document deleted successfully",
        data={"document_id": doc_id, "deleted": True}
    ).model_dump()
