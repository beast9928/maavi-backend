# legal_draft_routes.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.services.ai.ai_service import generate_legal_document, analyze_contract

draft_router = APIRouter(prefix="/legal/draft", tags=["Legal Drafting"])

class DraftRequest(BaseModel):
    doc_type: str
    client_name: str
    opposite_party: str = ""
    subject: str
    jurisdiction: str = "Delhi"
    relief: str = ""
    extra: str = ""

class ContractRequest(BaseModel):
    text: str

@draft_router.post("/generate")
def generate_doc(req: DraftRequest, current_user=Depends(get_current_user)):
    result = generate_legal_document(
        req.doc_type, req.client_name, req.opposite_party,
        req.subject, req.jurisdiction, req.relief, req.extra
    )
    return {"document": result, "doc_type": req.doc_type}

@draft_router.post("/analyze-contract")
def analyze(req: ContractRequest, current_user=Depends(get_current_user)):
    return analyze_contract(req.text)

@draft_router.get("/templates")
def get_templates(current_user=Depends(get_current_user)):
    return {"templates": [
        "Legal Notice", "NDA", "Service Agreement", "Demand Notice",
        "Affidavit", "Plaint", "Legal Opinion", "Rent Agreement",
        "Employment Contract", "Power of Attorney"
    ]}
