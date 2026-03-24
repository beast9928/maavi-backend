"""
Document Routes - Upload, OCR processing, retrieval
"""
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models import Document, DocumentType, Client, User
from app.schemas import DocumentResponse
from app.core.security import get_current_user
from app.core.config import settings
from app.services.document_service import save_uploaded_file, process_document

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/tiff",
    "image/bmp", "image/webp"
}


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    client_id: int = Form(...),
    doc_type: DocumentType = Form(DocumentType.INVOICE),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate client ownership
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.ca_user_id == current_user.id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not allowed. Use PDF or image files."
        )

    # Validate file size
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save file
    file_path, unique_name = save_uploaded_file(
        content, file.filename, doc_type.value, settings.UPLOAD_DIR
    )

    # Create DB record
    document = Document(
        client_id=client_id,
        uploaded_by_id=current_user.id,
        filename=unique_name,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        doc_type=doc_type,
        ocr_status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Process in background
    background_tasks.add_task(process_document, document.id, db)

    return document


@router.get("/client/{client_id}", response_model=List[DocumentResponse])
def list_documents(
    client_id: int,
    doc_type: Optional[DocumentType] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)

    query = db.query(Document).filter(Document.client_id == client_id)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)

    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _verify_client_access(doc.client_id, current_user.id, db)
    return doc


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _verify_client_access(doc.client_id, current_user.id, db)

    doc.ocr_status = "pending"
    doc.processing_error = None
    db.commit()

    background_tasks.add_task(process_document, document_id, db)
    return {"message": "Document queued for reprocessing"}


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _verify_client_access(doc.client_id, current_user.id, db)

    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}


def _verify_client_access(client_id: int, user_id: int, db: Session):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.ca_user_id == user_id
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Access denied")
