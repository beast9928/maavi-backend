from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class OrgRole(str, enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"

class Organisation(Base):
    __tablename__ = "organisations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    members = relationship("OrgMember", back_populates="organisation", cascade="all, delete-orphan")

class OrgMember(Base):
    __tablename__ = "org_members"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(OrgRole), default=OrgRole.STAFF)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    organisation = relationship("Organisation", back_populates="members")

class OrgInvite(Base):
    __tablename__ = "org_invites"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organisations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(Enum(OrgRole), default=OrgRole.STAFF)
    token = Column(String(100), unique=True, index=True)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
