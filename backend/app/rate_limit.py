"""Database backed limits shared by every API worker."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

def allow_request(session: Session, key: str, limit: int, window_seconds: int) -> bool:
    """Serialize checks per key and persist a sliding window hit."""
    from app.models import RateLimitHit

    digest = sha256(key.encode()).digest()
    safe_key = digest.hex()
    lock_id = int.from_bytes(digest[:8], "big", signed=True)
    now = datetime.now(timezone.utc)
    session.execute(select(func.pg_advisory_xact_lock(lock_id)))
    session.execute(delete(RateLimitHit).where(RateLimitHit.created_at < now - timedelta(days=1)))
    session.execute(
        delete(RateLimitHit).where(
            RateLimitHit.key == safe_key,
            RateLimitHit.created_at < now - timedelta(seconds=window_seconds),
        )
    )
    count = session.scalar(
        select(func.count()).select_from(RateLimitHit).where(RateLimitHit.key == safe_key)
    )
    if count is not None and count >= limit:
        session.commit()
        return False
    session.add(RateLimitHit(key=safe_key, created_at=now))
    session.commit()
    return True
