# ocr_routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.services.ai.ai_service import extract_invoice_data
import base64, os, tempfile

ocr_router = APIRouter(prefix="/ocr", tags=["OCR"])

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF or image using basic methods."""
    text = ""
    ext = filename.lower().split(".")[-1]
    try:
        if ext == "pdf":
            try:
                import pdfplumber
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        text += (page.extract_text() or "") + "\n"
                os.unlink(tmp_path)
            except ImportError:
                text = f"PDF file received ({len(file_bytes)} bytes). Please install pdfplumber."
        elif ext in ["jpg", "jpeg", "png", "webp", "bmp"]:
            # Send image to AI directly as base64
            text = f"[IMAGE:{base64.b64encode(file_bytes).decode()}]"
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        text = f"Error reading file: {str(e)}"
    return text

@ocr_router.post("/scan-invoice")
async def scan_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed = ["pdf", "jpg", "jpeg", "png", "webp", "bmp"]
    ext = file.filename.lower().split(".")[-1]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported. Use: {allowed}")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    text = extract_text_from_file(contents, file.filename)
    extracted = extract_invoice_data(text)

    return {
        "filename": file.filename,
        "extracted_data": extracted,
        "raw_text_preview": text[:500] if not text.startswith("[IMAGE:") else "[Image processed by AI]",
        "status": "success"
    }

@ocr_router.post("/scan-invoice-base64")
async def scan_invoice_base64(
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Accept base64 encoded file for frontend uploads."""
    b64 = data.get("file_base64", "")
    filename = data.get("filename", "invoice.pdf")
    if not b64:
        raise HTTPException(status_code=400, detail="No file data provided")
    file_bytes = base64.b64decode(b64)
    text = extract_text_from_file(file_bytes, filename)
    extracted = extract_invoice_data(text)
    return {"filename": filename, "extracted_data": extracted, "status": "success"}
