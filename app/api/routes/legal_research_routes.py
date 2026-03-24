# legal_research_routes.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.services.ai.ai_service import do_legal_research, find_precedents

research_router = APIRouter(prefix="/legal/research", tags=["Legal Research"])

class ResearchRequest(BaseModel):
    query: str
    court_filter: Optional[str] = ""

class PrecedentRequest(BaseModel):
    matter_type: str
    facts: str
    court: Optional[str] = ""

@research_router.post("/search")
def search(req: ResearchRequest, current_user=Depends(get_current_user)):
    result = do_legal_research(req.query, req.court_filter)
    return {"result": result, "query": req.query}

@research_router.post("/precedents")
def precedents(req: PrecedentRequest, current_user=Depends(get_current_user)):
    result = find_precedents(req.matter_type, req.facts, req.court)
    return {"result": result}
