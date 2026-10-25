from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_session
from app.attendance import ip_matches_cidr, location_is_allowed
from app.models import AttendancePolicy, AuditLog, Company, Invitation, Membership, User
from app.permissions import has_permission
from app.schemas import AttendancePolicyTestInput, CompanyCreateInput, InvitationCreateInput
from app.security import decode_access_token, new_refresh_token, token_digest

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

def current_user(ah_access: str | None = Cookie(default=None), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> User:
    claims = decode_access_token(ah_access, settings) if ah_access else None
    user = session.get(User, claims.get("sub")) if claims else None
    if user is None or claims.get("ver") != user.token_version: raise HTTPException(status_code=401, detail="Invalid session")
    return user


def require_company_permission(slug: str, user: User, session: Session, permission: str) -> Company:
    company = session.scalar(select(Company).where(Company.slug == slug))
    membership = session.scalar(select(Membership).where(Membership.company_id == company.id, Membership.user_id == user.id)) if company else None
    if company is None or membership is None or not has_permission(membership.role, permission): raise HTTPException(status_code=404, detail="Company not found")
    return company

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


@router.post("/{slug}/attendance-policy/test")
def test_attendance_policy(slug: str, payload: AttendancePolicyTestInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, bool | str]:
    company = require_company_permission(slug, user, session, "policy.manage")
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    if policy.mode == "ip":
        allowed = bool(payload.ip and policy.allowed_cidr and ip_matches_cidr(payload.ip, policy.allowed_cidr))
    else:
        allowed = bool(payload.latitude is not None and payload.longitude is not None and payload.accuracy_meters is not None and policy.latitude and policy.longitude and policy.radius_meters and location_is_allowed(payload.latitude, payload.longitude, payload.accuracy_meters, float(policy.latitude), float(policy.longitude), policy.radius_meters))
    return {"mode": policy.mode, "allowed": allowed}


@router.get("/{slug}/audit")
def list_audit(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    company = require_company_permission(slug, user, session, "audit.read")
    entries = session.scalars(select(AuditLog).where(AuditLog.company_id == company.id).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [{"action": entry.action, "created_at": entry.created_at.isoformat()} for entry in entries]


@router.get("/{slug}/members")
def list_members(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    company = require_company_permission(slug, user, session, "company.read")
    rows = session.execute(select(User, Membership.role).join(Membership).where(Membership.company_id == company.id)).all()
    return [{"email": member.email, "name": member.name, "role": role} for member, role in rows]


@router.post("/{slug}/invitations", status_code=status.HTTP_201_CREATED)
def create_invitation(slug: str, payload: InvitationCreateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "members.manage")
    token = new_refresh_token()
    session.add(Invitation(company_id=company.id, email=str(payload.email).lower(), role=payload.role, token_hash=token_digest(token), expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="invitation.created")); session.commit()
    return {"status": "created"}
