"""
Document Processing Service - Orchestrates OCR + AI extraction pipeline
"""
import os
import uuid
import shutil
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Document, DocumentType, Invoice, InvoiceType
from app.services.ocr.ocr_service import extract_text_from_file, parse_invoice_from_text
from app.services.ai.ai_service import extract_invoice_data, ai_chat_response

logger = logging.getLogger(__name__)


def save_uploaded_file(file_content: bytes, original_filename: str, doc_type: str, upload_dir: str) -> tuple:
    """Save uploaded file and return (saved_path, unique_filename)."""
    ext = os.path.splitext(original_filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    type_dir = os.path.join(upload_dir, doc_type.lower())
    os.makedirs(type_dir, exist_ok=True)
    file_path = os.path.join(type_dir, unique_name)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    return file_path, unique_name


async def process_document(document_id: int, db: Session) -> None:
    """
    Full document processing pipeline:
    1. Extract text via OCR
    2. Parse with regex
    3. Enhance with AI
    4. Store structured data
    5. Auto-create invoice if applicable
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.error(f"Document {document_id} not found")
        return

    try:
        # Update status to processing
        document.ocr_status = "processing"
        db.commit()

        # Step 1: Extract text
        logger.info(f"Extracting text from {document.file_path}")
        ocr_text = extract_text_from_file(document.file_path)
        document.ocr_text = ocr_text

        if not ocr_text.strip():
            document.ocr_status = "failed"
            document.processing_error = "No text could be extracted from document"
            db.commit()
            return

        # Step 2: Parse with regex (fast, no AI cost)
        regex_data = {}
        if document.doc_type in [DocumentType.INVOICE, DocumentType.RECEIPT]:
            regex_data = parse_invoice_from_text(ocr_text)

        # Step 3: AI-enhanced extraction
        extracted_data = {}
        if document.doc_type in [DocumentType.INVOICE, DocumentType.RECEIPT]:
            extracted_data = extract_invoice_data(ocr_text, regex_data)
        
        document.extracted_data = extracted_data

        # Step 4: Generate AI summary
        document.ai_summary = ai_chat_response(ocr_text, document.doc_type.value)

        # Step 5: Auto-create invoice record if this is an invoice
        if document.doc_type == DocumentType.INVOICE and extracted_data:
            _auto_create_invoice(document, extracted_data, db)

        document.ocr_status = "completed"
        db.commit()
        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")
        document.ocr_status = "failed"
        document.processing_error = str(e)
        db.commit()


def _auto_create_invoice(document: Document, data: dict, db: Session) -> None:
    """Auto-create an Invoice record from extracted document data."""
    try:
        from datetime import date as date_type
        from dateutil import parser as dateutil_parser

        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return dateutil_parser.parse(str(date_str)).date()
            except Exception:
                return None

        # Determine invoice type from hints
        invoice_type = InvoiceType.PURCHASE
        hint = data.get("invoice_type_hint", "").lower()
        if "sale" in hint:
            invoice_type = InvoiceType.SALE

        invoice = Invoice(
            client_id=document.client_id,
            document_id=document.id,
            invoice_type=invoice_type,
            invoice_number=data.get("invoice_number"),
            invoice_date=parse_date(data.get("invoice_date")),
            due_date=parse_date(data.get("due_date")),
            vendor_name=data.get("vendor_name"),
            vendor_gstin=data.get("vendor_gstin"),
            vendor_address=data.get("vendor_address"),
            buyer_name=data.get("buyer_name"),
            buyer_gstin=data.get("buyer_gstin"),
            place_of_supply=data.get("place_of_supply"),
            taxable_amount=float(data.get("taxable_amount") or 0),
            cgst_rate=float(data.get("cgst_rate") or 0),
            cgst_amount=float(data.get("cgst_amount") or 0),
            sgst_rate=float(data.get("sgst_rate") or 0),
            sgst_amount=float(data.get("sgst_amount") or 0),
            igst_rate=float(data.get("igst_rate") or 0),
            igst_amount=float(data.get("igst_amount") or 0),
            total_tax=float(data.get("total_tax") or 0),
            total_amount=float(data.get("total_amount") or 0),
            tds_amount=float(data.get("tds_amount") or 0),
            hsn_sac_code=data.get("hsn_sac_code"),
            description=data.get("description"),
            expense_category=data.get("expense_category"),
            raw_extracted_data=data,
        )
        db.add(invoice)
        db.flush()

        # Add line items
        for item in data.get("line_items", []):
            from app.models import InvoiceLineItem
            li = InvoiceLineItem(
                invoice_id=invoice.id,
                description=item.get("description"),
                hsn_sac=item.get("hsn_sac"),
                quantity=float(item.get("quantity") or 1),
                unit=item.get("unit"),
                unit_price=float(item.get("unit_price") or 0),
                taxable_amount=float(item.get("taxable_amount") or 0),
                gst_rate=float(item.get("gst_rate") or 0),
                total=float(item.get("total") or 0),
            )
            db.add(li)

        # Auto-create transaction entry
        if invoice.total_amount > 0:
            from app.models import Transaction, TransactionType
            txn = Transaction(
                client_id=document.client_id,
                invoice_id=invoice.id,
                transaction_date=invoice.invoice_date or date_type.today(),
                description=f"{'Purchase' if invoice_type == InvoiceType.PURCHASE else 'Sale'} - {invoice.vendor_name or 'Unknown'}",
                amount=invoice.total_amount,
                transaction_type=TransactionType.DEBIT if invoice_type == InvoiceType.PURCHASE else TransactionType.CREDIT,
                category=invoice.expense_category or "Other",
                account_head="Accounts Payable" if invoice_type == InvoiceType.PURCHASE else "Accounts Receivable",
            )
            db.add(txn)

        logger.info(f"Auto-created invoice from document {document.id}")
    except Exception as e:
        logger.error(f"Failed to auto-create invoice: {e}")
