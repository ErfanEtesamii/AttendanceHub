"""Create or promote a user to platform administrator.

Usage: python scripts/create_platform_admin.py owner@example.com
The account must already exist; public registration can never assign this role.
"""
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User


def main(email: str) -> None:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            raise SystemExit("No user exists with that email")
        user.platform_role = "platform_admin"
        session.commit()
    print("Platform administrator configured")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/create_platform_admin.py owner@example.com")
    main(sys.argv[1])
