# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class MatterStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    URGENT = "urgent"
    CLOSED = "closed"
    DISCOVERY = "discovery"

class Matter(Base):
    __tablename__ = "matters"
    id = Column(Integer, primary_key=True, index=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    matter_number = Column(String(50), unique=True, index=True)
    title = Column(String(500), nullable=False)
    practice_area = Column(String(100))
    court = Column(String(200))
    judge = Column(String(200))
    status = Column(Enum(MatterStatus), default=MatterStatus.PENDING)
    filed_date = Column(Date)
    next_hearing = Column(Date)
    client_name = Column(String(255))
    opposite_party = Column(String(255))
    brief = Column(Text)
    assigned_to = Column(String(255))
    relief_sought = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    hearings = relationship("CourtHearing", back_populates="matter", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="matter", cascade="all, delete-orphan")

class CourtHearing(Base):
    __tablename__ = "court_hearings"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    hearing_date = Column(Date, nullable=False)
    hearing_time = Column(String(20))
    court = Column(String(200))
    purpose = Column(String(200))
    notes = Column(Text)
    is_attended = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    outcome = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    matter = relationship("Matter", back_populates="hearings")

class TimeEntry(Base):
    __tablename__ = "time_entries"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    rate_per_hour = Column(Float, nullable=False)
    amount = Column(Float)
    description = Column(Text)
    is_billed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    matter = relationship("Matter", back_populates="time_entries")

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doc_type = Column(String(100))
    title = Column(String(500))
    content = Column(Text)
    client_name = Column(String(255))
    opposite_party = Column(String(255))
    jurisdiction = Column(String(200))
    ai_generated = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ContractAnalysis(Base):
    __tablename__ = "contract_analyses"
    id = Column(Integer, primary_key=True, index=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=True)
    filename = Column(String(500))
    risk_score = Column(Float)
    risk_level = Column(String(20))
    summary = Column(Text)
    red_flags = Column(Text)
    clause_analysis = Column(Text)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
