"""Idempotently create the default Faraz Honar company and IP policy."""
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import AttendancePolicy, BotConfiguration, Company, Membership, User


def main() -> None:
    settings = get_settings()
    with SessionLocal() as session:
        company = session.scalar(select(Company).where(Company.slug == "faraz-honar"))
        if company is None:
            company = Company(name="فراز هنر", slug="faraz-honar", timezone="Asia/Tehran")
            session.add(company); session.flush()
            session.add(AttendancePolicy(company_id=company.id, mode="ip", allowed_cidr="192.168.10.0/24"))
            session.add(BotConfiguration(company_id=company.id, mode="shared", username=settings.shared_bot_username))
        if settings.farazhonar_owner_email:
            owner = session.scalar(select(User).where(User.email == settings.farazhonar_owner_email.lower()))
            if owner and not session.scalar(select(Membership).where(Membership.company_id == company.id, Membership.user_id == owner.id)):
                session.add(Membership(company_id=company.id, user_id=owner.id, role="owner"))
        session.commit()
    print("Faraz Honar seed completed")


if __name__ == "__main__":
    main()
