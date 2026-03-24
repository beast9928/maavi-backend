"""
OCR Service - Document text extraction using multiple methods
Falls back gracefully if PaddleOCR is not available
"""
import os
import re
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import OCR libraries - graceful fallback
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
    _paddle_instance = None

    def get_paddle():
        global _paddle_instance
        if _paddle_instance is None:
            _paddle_instance = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        return _paddle_instance
except ImportError:
    PADDLE_AVAILABLE = False
    logger.warning("PaddleOCR not available, using fallback OCR")

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF or image file."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == '.pdf':
        return extract_from_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        return extract_from_image(file_path)
    else:
        return ""


def extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF - tries direct text extraction first, then OCR."""
    text = ""

    # Try PyMuPDF direct text extraction
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            if len(text.strip()) > 50:
                return text
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")

    # Fall back to OCR on PDF images
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(file_path)
            full_text = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img_path = f"/tmp/page_{page.number}.png"
                pix.save(img_path)
                page_text = extract_from_image(img_path)
                full_text.append(page_text)
                os.remove(img_path)
            doc.close()
            return "\n".join(full_text)
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")

    return text


def extract_from_image(file_path: str) -> str:
    """Extract text from image using PaddleOCR or Tesseract."""
    # Try PaddleOCR first
    if PADDLE_AVAILABLE:
        try:
            ocr = get_paddle()
            result = ocr.ocr(file_path, cls=True)
            if result and result[0]:
                lines = [line[1][0] for line in result[0] if line and len(line) > 1]
                return "\n".join(lines)
        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")

    # Fall back to Tesseract
    if TESSERACT_AVAILABLE:
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='eng')
            return text
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")

    return ""


def parse_invoice_from_text(ocr_text: str) -> Dict[str, Any]:
    """
    Parse structured invoice data from OCR text using regex patterns.
    This is a rule-based fallback; the AI service provides better extraction.
    """
    data = {
        "invoice_number": None,
        "invoice_date": None,
        "vendor_name": None,
        "vendor_gstin": None,
        "buyer_name": None,
        "buyer_gstin": None,
        "taxable_amount": None,
        "cgst_amount": None,
        "sgst_amount": None,
        "igst_amount": None,
        "total_amount": None,
        "hsn_sac_code": None,
        "place_of_supply": None,
    }

    text = ocr_text

    # GSTIN pattern: 15 characters alphanumeric
    gstin_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b'
    gstins = re.findall(gstin_pattern, text, re.IGNORECASE)
    if gstins:
        data["vendor_gstin"] = gstins[0]
        if len(gstins) > 1:
            data["buyer_gstin"] = gstins[1]

    # Invoice number
    inv_patterns = [
        r'invoice\s*(?:no|number|#)[:\s]*([A-Z0-9\-/]+)',
        r'bill\s*(?:no|number|#)[:\s]*([A-Z0-9\-/]+)',
        r'inv[:\s#]*([A-Z0-9\-/]+)',
    ]
    for pattern in inv_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(1).strip()
            break

    # Date patterns
    date_patterns = [
        r'(?:invoice\s*date|date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_date"] = match.group(1).strip()
            break

    # Amount patterns
    amount_patterns = {
        "total_amount": [
            r'total\s*(?:amount|value)?[:\s]*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)',
            r'grand\s*total[:\s]*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)',
        ],
        "taxable_amount": [
            r'taxable\s*(?:value|amount)[:\s]*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)',
        ],
        "cgst_amount": [
            r'cgst[:\s@\d%]*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)',
        ],
        "sgst_amount": [
            r'sgst[:\s@\d%]*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)',
        ],
        "igst_amount": [
            r'igst[:\s@\d%]*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d{2})?)',
        ],
    }

    for field, patterns in amount_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    data[field] = float(amount_str)
                    break
                except ValueError:
                    pass

    # HSN/SAC code
    hsn_match = re.search(r'hsn[/\s]?sac[:\s]*([A-Z0-9]+)', text, re.IGNORECASE)
    if hsn_match:
        data["hsn_sac_code"] = hsn_match.group(1)

    # Place of supply - Indian state patterns
    pos_match = re.search(r'place\s+of\s+supply[:\s]*([A-Za-z\s]+?)(?:\n|,|\d)', text, re.IGNORECASE)
    if pos_match:
        data["place_of_supply"] = pos_match.group(1).strip()

    return data
