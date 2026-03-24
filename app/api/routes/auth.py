from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.schemas import UserCreate, TokenResponse, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from pydantic import BaseModel

router = APIRouter(prefix='/auth', tags=['Authentication'])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post('/signup', response_model=TokenResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        firm_name=user_data.firm_name,
        phone=user_data.phone,
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({'sub': str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@router.post('/login', response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    if not user.is_active:
        raise HTTPException(status_code=403, detail='Account is inactive')
    token = create_access_token({'sub': str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@router.get('/me', response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
