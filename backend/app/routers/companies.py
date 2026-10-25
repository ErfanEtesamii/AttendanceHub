from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_session
from app.models import AttendancePolicy, Company, Membership, User
from app.schemas import CompanyCreateInput
from app.security import decode_access_token

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

def current_user(ah_access: str | None = Cookie(default=None), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> User:
    claims = decode_access_token(ah_access, settings) if ah_access else None
    user = session.get(User, claims.get("sub")) if claims else None
    if user is None or claims.get("ver") != user.token_version: raise HTTPException(status_code=401, detail="Invalid session")
    return user

@router.get("")
def list_companies(user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    rows = session.execute(select(Company, Membership.role).join(Membership).where(Membership.user_id == user.id)).all()
    return [{"name": company.name, "slug": company.slug, "role": role} for company, role in rows]

@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    if payload.mode == "ip" and not payload.allowed_cidr: raise HTTPException(status_code=422, detail="CIDR is required for IP mode")
    if payload.mode == "location" and (not payload.latitude or not payload.longitude or not payload.radius_meters): raise HTTPException(status_code=422, detail="Location is required for location mode")
    if session.scalar(select(func.count()).select_from(Membership).where(Membership.user_id == user.id)) >= 3: raise HTTPException(status_code=403, detail="Company limit reached")
    company = Company(name=payload.name.strip(), slug=payload.slug)
    session.add(company); session.flush()
    session.add(Membership(company_id=company.id, user_id=user.id, role="owner"))
    session.add(AttendancePolicy(company_id=company.id, mode=payload.mode, allowed_cidr=payload.allowed_cidr, latitude=payload.latitude, longitude=payload.longitude, radius_meters=payload.radius_meters))
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(status_code=400, detail="Unable to create company")
    return {"name": company.name, "slug": company.slug, "role": "owner"}
