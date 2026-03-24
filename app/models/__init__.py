"""
Complete database models for AI CA Copilot
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    Enum, JSON, Date, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    CA_ADMIN = "ca_admin"
    CA_STAFF = "ca_staff"
    CLIENT_USER = "client_user"


class DocumentType(str, enum.Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    GST_REPORT = "gst_report"
    FINANCIAL_STATEMENT = "financial_statement"
    OTHER = "other"


class InvoiceType(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"


class TransactionType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class ComplianceType(str, enum.Enum):
    GST_FILING = "gst_filing"
    TDS_RETURN = "tds_return"
    INCOME_TAX = "income_tax"
    ROC_FILING = "roc_filing"
    ADVANCE_TAX = "advance_tax"
    PT_FILING = "pt_filing"


class ComplianceStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FILED = "filed"
    OVERDUE = "overdue"


class GSTRate(str, enum.Enum):
    ZERO = "0"
    FIVE = "5"
    TWELVE = "12"
    EIGHTEEN = "18"
    TWENTY_EIGHT = "28"
    EXEMPT = "exempt"


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CA_STAFF)
    is_active = Column(Boolean, default=True)
    firm_name = Column(String(255))
    phone = Column(String(20))
    gstin = Column(String(15))
    avatar_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    clients = relationship("Client", back_populates="assigned_ca")
    documents = relationship("Document", back_populates="uploaded_by")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    pan = Column(String(10))
    gstin = Column(String(15), index=True)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    state = Column(String(50))
    state_code = Column(String(5))
    business_type = Column(String(100))  # Proprietorship, Partnership, Pvt Ltd, etc.
    industry = Column(String(100))
    financial_year_start = Column(String(5), default="04-01")  # MM-DD
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    assigned_ca = relationship("User", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client")
    documents = relationship("Document", back_populates="client")
    transactions = relationship("Transaction", back_populates="client")
    compliance_items = relationship("ComplianceItem", back_populates="client")
    ledger_entries = relationship("LedgerEntry", back_populates="client")
    gst_mismatches = relationship("GSTMismatch", back_populates="client")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    doc_type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    ocr_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    ocr_text = Column(Text)
    extracted_data = Column(JSON)
    ai_summary = Column(Text)
    processing_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="documents")
    uploaded_by = relationship("User", back_populates="documents")
    invoices = relationship("Invoice", back_populates="document")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    invoice_type = Column(Enum(InvoiceType), nullable=False)
    invoice_number = Column(String(100), index=True)
    invoice_date = Column(Date)
    due_date = Column(Date)
    vendor_name = Column(String(255))
    vendor_gstin = Column(String(15))
    vendor_pan = Column(String(10))
    vendor_address = Column(Text)
    buyer_name = Column(String(255))
    buyer_gstin = Column(String(15))
    place_of_supply = Column(String(50))
    # Amounts
    taxable_amount = Column(Float, default=0)
    cgst_rate = Column(Float, default=0)
    cgst_amount = Column(Float, default=0)
    sgst_rate = Column(Float, default=0)
    sgst_amount = Column(Float, default=0)
    igst_rate = Column(Float, default=0)
    igst_amount = Column(Float, default=0)
    cess_amount = Column(Float, default=0)
    total_tax = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    tds_amount = Column(Float, default=0)
    # Categorization
    expense_category = Column(String(100))
    hsn_sac_code = Column(String(20))
    description = Column(Text)
    # Status
    payment_status = Column(String(50), default="unpaid")
    is_reconciled = Column(Boolean, default=False)
    gst_verified = Column(Boolean, default=False)
    notes = Column(Text)
    raw_extracted_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="invoices")
    document = relationship("Document", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(Text)
    hsn_sac = Column(String(20))
    quantity = Column(Float, default=1)
    unit = Column(String(20))
    unit_price = Column(Float, default=0)
    discount = Column(Float, default=0)
    taxable_amount = Column(Float, default=0)
    gst_rate = Column(Float, default=0)
    gst_amount = Column(Float, default=0)
    total = Column(Float, default=0)

    invoice = relationship("Invoice", back_populates="line_items")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    transaction_date = Column(Date, nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(String(100))
    sub_category = Column(String(100))
    account_head = Column(String(100))
    reference_number = Column(String(100))
    bank_name = Column(String(100))
    is_reconciled = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="transactions")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    entry_date = Column(Date, nullable=False)
    account_name = Column(String(200), nullable=False)
    account_type = Column(String(50))  # Asset, Liability, Income, Expense, Equity
    debit_amount = Column(Float, default=0)
    credit_amount = Column(Float, default=0)
    balance = Column(Float, default=0)
    narration = Column(Text)
    voucher_number = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="ledger_entries")


class ComplianceItem(Base):
    __tablename__ = "compliance_items"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    compliance_type = Column(Enum(ComplianceType), nullable=False)
    period = Column(String(20))  # e.g., "2024-03", "Q1-2024", "FY2024"
    due_date = Column(Date, nullable=False)
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING)
    filed_date = Column(Date)
    acknowledgment_number = Column(String(100))
    amount_payable = Column(Float, default=0)
    amount_paid = Column(Float, default=0)
    penalty_amount = Column(Float, default=0)
    notes = Column(Text)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="compliance_items")


class GSTMismatch(Base):
    __tablename__ = "gst_mismatches"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    mismatch_type = Column(String(100))  # amount_mismatch, missing_invoice, gstin_invalid, etc.
    period = Column(String(20))
    our_amount = Column(Float)
    portal_amount = Column(Float)
    difference = Column(Float)
    vendor_gstin = Column(String(15))
    invoice_number = Column(String(100))
    description = Column(Text)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="gst_mismatches")


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    session_id = Column(String(100), index=True)
    role = Column(String(20))  # user, assistant
    message = Column(Text, nullable=False)
    context_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
