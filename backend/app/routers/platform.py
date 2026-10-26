from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import Company, User
from app.routers.companies import current_user

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def platform_admin(user: User = Depends(current_user)) -> User:
    if user.platform_role != "platform_admin":
        raise HTTPException(status_code=404, detail="Platform not found")
    return user


@router.get("/companies")
def list_platform_companies(_: User = Depends(platform_admin), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    companies = session.scalars(select(Company).order_by(Company.created_at.desc())).all()
    return [{"name": company.name, "slug": company.slug, "timezone": company.timezone} for company in companies]
