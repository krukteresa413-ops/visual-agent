import re

from pydantic import BaseModel, Field, field_validator, model_validator
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import User
from app.services.auth_service import ALLOWED_ROLES, create_access_token, create_tenant, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
CHINA_MOBILE_RE = re.compile(r"^1[3-9]\d{9}$")


class RegisterRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, min_length=11, max_length=11)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    tenant_name: str = Field(..., min_length=1, max_length=255)
    role: str = "member"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("invalid email")
        return email

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        phone = re.sub(r"[\s-]", "", value.strip())
        if phone.startswith("+86"):
            phone = phone[3:]
        if not CHINA_MOBILE_RE.fullmatch(phone):
            raise ValueError("invalid China mobile number")
        return phone

    @model_validator(mode="after")
    def require_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("email or phone is required")
        return self


class LoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    phone: str | None = Field(default=None, min_length=11, max_length=11)
    password: str = Field(..., min_length=1, max_length=128)

    @model_validator(mode="after")
    def normalize_identifier(self):
        raw = self.identifier or self.email or self.phone
        if not raw:
            raise ValueError("identifier is required")
        raw = raw.strip().lower()
        if raw.startswith("+86"):
            raw = raw[3:]
        self.identifier = re.sub(r"[\s-]", "", raw) if raw.startswith("1") else raw
        return self


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "phone": user.phone,
        "name": user.name,
        "role": user.role,
    }


@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="invalid role")
    duplicate_query = []
    if req.email:
        duplicate_query.append(User.email == req.email)
    if req.phone:
        duplicate_query.append(User.phone == req.phone)
    if duplicate_query and db.query(User).filter(or_(*duplicate_query)).first():
        raise HTTPException(status_code=409, detail="account already registered")

    tenant = create_tenant(db, req.tenant_name)
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        phone=req.phone,
        password_hash=hash_password(req.password),
        name=req.name.strip(),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_payload(user)


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    identifier = req.identifier or ""
    user = db.query(User).filter(or_(User.email == identifier, User.phone == identifier)).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="user disabled")
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": user_payload(user)}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return user_payload(current_user)
