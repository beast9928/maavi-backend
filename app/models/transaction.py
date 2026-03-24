# Re-export models from the unified __init__ for backwards compatibility
from app.models import (
    User, Client, Document, Invoice, InvoiceLineItem,
    Transaction, LedgerEntry, ComplianceItem, GSTMismatch, AIConversation,
    UserRole, DocumentType, InvoiceType, TransactionType,
    ComplianceType, ComplianceStatus, GSTRate
)

__all__ = [
    "User", "Client", "Document", "Invoice", "InvoiceLineItem",
    "Transaction", "LedgerEntry", "ComplianceItem", "GSTMismatch", "AIConversation",
    "UserRole", "DocumentType", "InvoiceType", "TransactionType",
    "ComplianceType", "ComplianceStatus", "GSTRate",
]
