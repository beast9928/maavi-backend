from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum


class UserRole(str, Enum):
    CA_ADMIN = "ca_admin"
    CA_STAFF = "ca_staff"


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    firm_name: Optional[str] = None
    phone: Optional[str] = None
    role: str = "ca_admin"


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    firm_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ClientCreate(BaseModel):
    company_name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ClientResponse(BaseModel):
    id: int
    company_name: str
    pan: Optional[str] = None
    gstin: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClientSummary(ClientResponse):
    total_invoices: int = 0
    total_revenue: float = 0
    pending_compliance: int = 0
    gst_mismatches: int = 0


class InvoiceCreate(BaseModel):
    client_id: int
    invoice_type: str
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    vendor_address: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    taxable_amount: float = 0
    cgst_rate: float = 0
    cgst_amount: float = 0
    sgst_rate: float = 0
    sgst_amount: float = 0
    igst_rate: float = 0
    igst_amount: float = 0
    total_tax: float = 0
    total_amount: float = 0
    tds_amount: float = 0
    expense_category: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    line_items: List[Dict] = []


class InvoiceResponse(BaseModel):
    id: int
    client_id: int
    invoice_type: str
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    buyer_name: Optional[str] = None
    taxable_amount: float
    total_tax: float
    total_amount: float
    expense_category: Optional[str] = None
    payment_status: str
    is_reconciled: bool
    gst_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    client_id: int
    filename: str
    original_filename: str
    doc_type: str
    ocr_status: str
    ai_summary: Optional[str] = None
    extracted_data: Optional[Dict] = None
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceCreate(BaseModel):
    client_id: int
    compliance_type: str
    period: str
    due_date: date
    amount_payable: float = 0
    notes: Optional[str] = None


class ComplianceUpdate(BaseModel):
    status: Optional[str] = None
    filed_date: Optional[date] = None
    acknowledgment_number: Optional[str] = None
    amount_paid: Optional[float] = None
    penalty_amount: Optional[float] = None
    notes: Optional[str] = None


class ComplianceResponse(BaseModel):
    id: int
    client_id: int
    compliance_type: str
    period: str
    due_date: date
    status: str
    filed_date: Optional[date] = None
    acknowledgment_number: Optional[str] = None
    amount_payable: float
    amount_paid: float
    penalty_amount: float
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    client_id: int
    transaction_date: date
    description: str
    amount: float
    transaction_type: str
    category: Optional[str] = None
    account_head: Optional[str] = None
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    client_id: int
    transaction_date: date
    description: str
    amount: float
    transaction_type: str
    category: Optional[str] = None
    account_head: Optional[str] = None
    is_reconciled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    message: str
    client_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    data: Optional[Dict] = None


class DashboardStats(BaseModel):
    total_clients: int
    active_clients: int
    total_invoices: int
    total_revenue: float
    pending_compliance: int
    overdue_compliance: int
    gst_mismatches: int
    documents_processed: int


class FinancialInsight(BaseModel):
    client_id: int = 0
    period: str = ""
    total_income: float = 0
    total_expenses: float = 0
    net_profit: float = 0
    profit_margin: float = 0
    top_expense_categories: List[Dict] = []
    gst_liability: float = 0
    tds_liability: float = 0
    health_score: float = 0
    health_indicators: List[str] = []


class GSTSummary(BaseModel):
    period: str = ""
    total_sales: float = 0
    total_purchases: float = 0
    output_gst: float = 0
    input_gst: float = 0
    net_gst_payable: float = 0
    mismatches_count: int = 0
