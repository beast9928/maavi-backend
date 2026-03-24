from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import secrets, re
from app.db.database import get_db
from app.models.organisation import Organisation, OrgMember, OrgInvite, OrgRole
from app.models import User
from app.core.security import get_current_user, get_password_hash

org_router = APIRouter(prefix="/org", tags=["Organisation"])

class OrgCreate(BaseModel):
    name: str

class InviteCreate(BaseModel):
    email: str
    role: str = "staff"

class AcceptInvite(BaseModel):
    token: str
    full_name: str
    password: str

def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

@org_router.post("/create")
def create_org(data: OrgCreate, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    slug = slugify(data.name)
    if db.query(Organisation).filter(Organisation.slug==slug).first():
        slug = slug + "-" + secrets.token_hex(3)
    org = Organisation(name=data.name, slug=slug)
    db.add(org); db.flush()
    db.add(OrgMember(org_id=org.id, user_id=current_user.id, role=OrgRole.OWNER))
    db.commit(); db.refresh(org)
    return {"id": org.id, "name": org.name, "slug": org.slug, "role": "owner"}

@org_router.get("/my")
def my_orgs(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    memberships = db.query(OrgMember).filter(OrgMember.user_id==current_user.id, OrgMember.is_active==True).all()
    result = []
    for m in memberships:
        org = db.query(Organisation).filter(Organisation.id==m.org_id).first()
        if org:
            count = db.query(OrgMember).filter(OrgMember.org_id==org.id, OrgMember.is_active==True).count()
            result.append({"id":org.id,"name":org.name,"slug":org.slug,"role":m.role.value,"members":count})
    return result

@org_router.get("/{org_id}/members")
def list_members(org_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    members = db.query(OrgMember).filter(OrgMember.org_id==org_id, OrgMember.is_active==True).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id==m.user_id).first()
        if u: result.append({"user_id":u.id,"email":u.email,"full_name":u.full_name,"role":m.role.value})
    return result

@org_router.post("/{org_id}/invite")
def invite_member(org_id: int, data: InviteCreate, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    from datetime import datetime, timedelta
    token = secrets.token_urlsafe(32)
    invite = OrgInvite(org_id=org_id, email=data.email, role=OrgRole(data.role), token=token, expires_at=datetime.utcnow()+timedelta(days=7))
    db.add(invite); db.commit()
    return {"invite_token": token, "email": data.email, "role": data.role}

@org_router.post("/accept-invite")
def accept_invite(data: AcceptInvite, db: Session=Depends(get_db)):
    from datetime import datetime
    invite = db.query(OrgInvite).filter(OrgInvite.token==data.token, OrgInvite.is_used==False).first()
    if not invite: raise HTTPException(status_code=400, detail="Invalid invite token")
    user = db.query(User).filter(User.email==invite.email).first()
    if not user:
        user = User(email=invite.email, full_name=data.full_name, hashed_password=get_password_hash(data.password), role="ca_staff")
        db.add(user); db.flush()
    db.add(OrgMember(org_id=invite.org_id, user_id=user.id, role=invite.role))
    invite.is_used = True; db.commit()
    return {"message": "Joined successfully", "email": user.email}

@org_router.delete("/{org_id}/members/{user_id}")
def remove_member(org_id: int, user_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    m = db.query(OrgMember).filter(OrgMember.org_id==org_id, OrgMember.user_id==user_id).first()
    if m: m.is_active = False; db.commit()
    return {"removed": True}
