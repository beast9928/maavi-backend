# itr_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db.database import get_db
from app.core.security import get_current_user
from app.services.ai.ai_service import ai_chat_response, _call_ai
import json

itr_router = APIRouter(prefix="/itr", tags=["ITR Filing"])

ITR_FORMS = {
    "ITR-1": "Sahaj — Salaried individuals, one house property, other sources. Income up to ₹50L.",
    "ITR-2": "Individuals/HUF with capital gains, foreign income, multiple properties.",
    "ITR-3": "Individuals/HUF with business or profession income (non-presumptive).",
    "ITR-4": "Sugam — Presumptive income under 44AD/44ADA/44AE. Income up to ₹50L.",
    "ITR-5": "Firms, LLPs, AOPs, BOIs — not companies.",
    "ITR-6": "Companies other than those claiming exemption u/s 11.",
    "ITR-7": "Trusts, political parties, research institutions.",
}

DEDUCTIONS = {
    "80C":   {"limit": 150000,  "desc": "PPF, ELSS, LIC, EPF, home loan principal, tuition fees"},
    "80CCD": {"limit": 50000,   "desc": "NPS additional contribution"},
    "80D":   {"limit": 25000,   "desc": "Medical insurance premium (₹50,000 for senior citizens)"},
    "80E":   {"limit": None,    "desc": "Education loan interest — no limit"},
    "80G":   {"limit": None,    "desc": "Donations — 50% or 100% depending on institution"},
    "80TTA": {"limit": 10000,   "desc": "Interest on savings account"},
    "80TTB": {"limit": 50000,   "desc": "Interest income for senior citizens"},
    "24B":   {"limit": 200000,  "desc": "Home loan interest on self-occupied property"},
    "87A":   {"limit": 12500,   "desc": "Tax rebate if income ≤ ₹5L (old regime)"},
    "10(14)": {"limit": None,   "desc": "HRA, LTA, uniform allowance exemptions"},
}

class ITRProfileRequest(BaseModel):
    client_name:    str
    pan:            Optional[str] = None
    ay:             str = "2024-25"
    employment:     str = "salaried"
    gross_salary:   Optional[float] = 0
    rental_income:  Optional[float] = 0
    business_income: Optional[float] = 0
    capital_gains:  Optional[float] = 0
    other_income:   Optional[float] = 0
    deduction_80c:  Optional[float] = 0
    deduction_80d:  Optional[float] = 0
    hra_exemption:  Optional[float] = 0
    home_loan_int:  Optional[float] = 0
    other_deductions: Optional[float] = 0
    regime:         str = "new"

@itr_router.get("/forms")
def get_forms(current_user=Depends(get_current_user)):
    return {"forms": ITR_FORMS}

@itr_router.get("/deductions")
def get_deductions(current_user=Depends(get_current_user)):
    return {"deductions": DEDUCTIONS}

@itr_router.post("/recommend-form")
def recommend_form(data: dict, current_user=Depends(get_current_user)):
    profile = data.get("profile", {})
    has_business   = float(profile.get("business_income", 0)) > 0
    has_cap_gains  = float(profile.get("capital_gains", 0)) > 0
    has_rental     = float(profile.get("rental_income", 0)) > 0
    is_company     = profile.get("entity_type", "individual") == "company"
    is_presumptive = profile.get("presumptive", False)
    total_income   = sum(float(profile.get(k, 0)) for k in [
        "gross_salary", "rental_income", "business_income", "capital_gains", "other_income"])

    if is_company:
        form, reason = "ITR-6", "Companies must file ITR-6"
    elif has_business and not is_presumptive:
        form, reason = "ITR-3", "Business/profession income requires ITR-3"
    elif has_business and is_presumptive:
        form, reason = "ITR-4", "Presumptive business income — use ITR-4 (Sugam)"
    elif has_cap_gains or (has_rental and total_income > 5000000):
        form, reason = "ITR-2", "Capital gains or high rental income requires ITR-2"
    elif total_income <= 5000000:
        form, reason = "ITR-1", "Salaried with simple income — ITR-1 (Sahaj)"
    else:
        form, reason = "ITR-2", "Income above ₹50L — ITR-2 recommended"

    return {"recommended_form": form, "reason": reason, "description": ITR_FORMS.get(form, "")}

@itr_router.post("/calculate-tax")
def calculate_tax(req: ITRProfileRequest, current_user=Depends(get_current_user)):
    gross = (req.gross_salary or 0) + (req.rental_income or 0) + \
            (req.business_income or 0) + (req.capital_gains or 0) + (req.other_income or 0)

    if req.regime == "old":
        std_deduction = min(50000, req.gross_salary or 0)
        deduction_80c = min(req.deduction_80c or 0, 150000)
        deduction_80d = min(req.deduction_80d or 0, 25000)
        hra            = req.hra_exemption or 0
        home_loan      = min(req.home_loan_int or 0, 200000)
        other_ded      = req.other_deductions or 0
        total_deductions = std_deduction + deduction_80c + deduction_80d + hra + home_loan + other_ded
        taxable = max(0, gross - total_deductions)

        # Old regime slabs FY 2023-24
        if taxable <= 250000:    tax = 0
        elif taxable <= 500000:  tax = (taxable - 250000) * 0.05
        elif taxable <= 1000000: tax = 12500 + (taxable - 500000) * 0.20
        else:                    tax = 112500 + (taxable - 1000000) * 0.30

        if taxable <= 500000:
            tax = max(0, tax - 12500)  # 87A rebate
    else:
        # New regime slabs FY 2024-25
        std_deduction    = min(75000, req.gross_salary or 0)
        total_deductions = std_deduction
        taxable = max(0, gross - std_deduction)

        if taxable <= 300000:    tax = 0
        elif taxable <= 600000:  tax = (taxable - 300000) * 0.05
        elif taxable <= 900000:  tax = 15000 + (taxable - 600000) * 0.10
        elif taxable <= 1200000: tax = 45000 + (taxable - 900000) * 0.15
        elif taxable <= 1500000: tax = 90000 + (taxable - 1200000) * 0.20
        else:                    tax = 150000 + (taxable - 1500000) * 0.30

        if taxable <= 700000:
            tax = 0  # Section 87A rebate new regime

    surcharge = 0
    if gross > 5000000:
        surcharge = tax * 0.10
    elif gross > 10000000:
        surcharge = tax * 0.15

    cess = (tax + surcharge) * 0.04
    total_tax = round(tax + surcharge + cess, 2)

    return {
        "assessment_year":   req.ay,
        "regime":            req.regime,
        "gross_income":      round(gross, 2),
        "total_deductions":  round(total_deductions, 2),
        "taxable_income":    round(taxable, 2),
        "income_tax":        round(tax, 2),
        "surcharge":         round(surcharge, 2),
        "health_ed_cess":    round(cess, 2),
        "total_tax":         total_tax,
        "effective_rate":    round((total_tax / gross * 100) if gross > 0 else 0, 2),
        "monthly_tds":       round(total_tax / 12, 2),
    }

@itr_router.post("/ai-advice")
def itr_ai_advice(data: dict, current_user=Depends(get_current_user)):
    query   = data.get("query", "")
    profile = data.get("profile", {})
    context = f"Client profile: {json.dumps(profile)}" if profile else ""
    system  = "You are a senior CA specialising in Indian Income Tax. Give specific advice on ITR filing, tax saving, regime selection, and deductions. Use INR. Be concise."
    response = _call_ai(system, f"{query}\n{context}")
    return {"advice": response}

@itr_router.post("/checklist")
def get_checklist(data: dict, current_user=Depends(get_current_user)):
    employment = data.get("employment", "salaried")
    form       = data.get("itr_form", "ITR-1")
    system     = "You are a CA. Return ONLY valid JSON: {\"documents\": [\"...\"], \"deadlines\": {\"filing\": \"...\", \"audit\": \"...\"}, \"tips\": [\"...\"]}"
    user_msg   = f"ITR filing checklist for {employment} taxpayer filing {form} for AY 2024-25. Include documents needed, key deadlines, and tax saving tips."
    result     = _call_ai(system, user_msg, json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {"documents": ["Form 16", "AIS/TIS", "Bank statements", "Investment proofs"], "deadlines": {"filing": "31 July 2024", "audit": "30 September 2024"}, "tips": ["Choose regime wisely", "Don't miss 80C investments"]}
