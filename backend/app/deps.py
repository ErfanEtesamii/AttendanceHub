"""Central authentication and tenant-context dependencies."""
from dataclasses import dataclass

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_session
from app.models import Company, Membership, User
from app.permissions import has_permission
from app.security import decode_access_token


def current_user(ah_access: str | None = Cookie(default=None), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> User:
    claims = decode_access_token(ah_access, settings) if ah_access else None
    user = session.get(User, claims.get("sub")) if claims else None
    if user is None or claims.get("ver") != user.token_version:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user


@dataclass(frozen=True)
class CompanyContext:
    company: Company
    membership: Membership
    user: User


def get_company_context(slug: str, user: User, session: Session, required_permission: str) -> CompanyContext:
    company = session.scalar(select(Company).where(Company.slug == slug))
    membership = session.scalar(select(Membership).where(Membership.company_id == company.id, Membership.user_id == user.id)) if company else None
    if company is None or company.status != "active" or membership is None or membership.status != "active" or not has_permission(membership.role, required_permission):
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyContext(company=company, membership=membership, user=user)
