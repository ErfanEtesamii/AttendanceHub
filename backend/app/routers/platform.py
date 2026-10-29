from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import AuditLog, Company, User
from app.deps import current_user
from app.schemas import CompanyStatusInput

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def platform_admin(user: User = Depends(current_user)) -> User:
    if user.platform_role != "platform_admin":
        raise HTTPException(status_code=404, detail="Platform not found")
    return user


@router.get("/companies")
def list_platform_companies(_: User = Depends(platform_admin), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    companies = session.scalars(select(Company).order_by(Company.created_at.desc())).all()
    return [{"name": company.name, "slug": company.slug, "timezone": company.timezone, "status": company.status} for company in companies]


@router.patch("/companies/{slug}/status")
def update_company_status(slug: str, payload: CompanyStatusInput, user: User = Depends(platform_admin), session: Session = Depends(get_session)) -> dict[str, str]:
    company = session.scalar(select(Company).where(Company.slug == slug))
    if company is None: raise HTTPException(status_code=404, detail="Company not found")
    company.status = payload.status
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="company.status_updated"))
    session.commit()
    return {"slug": company.slug, "status": company.status}
