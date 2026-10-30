import os
from uuid import uuid4
from hashlib import sha256

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app.rate_limit import allow_request


def test_limiter_rejects_over_limit() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL must point to PostgreSQL")

    from app.models import RateLimitHit

    engine = create_engine(database_url)
    key = f"test:rate-limit:{uuid4()}"
    try:
        with Session(engine) as session:
            assert allow_request(session, key, 2, 60)
            assert allow_request(session, key, 2, 60)
            assert not allow_request(session, key, 2, 60)
            digest = sha256(key.encode()).hexdigest()
            assert session.scalar(select(func.count()).select_from(RateLimitHit).where(RateLimitHit.key == digest)) == 2
    finally:
        engine.dispose()
