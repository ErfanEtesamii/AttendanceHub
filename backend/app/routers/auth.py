from datetime import datetime, timedelta, timezone
import hmac
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.client_ip import resolve_client_ip
from app.database import get_session
from app.models import OtpChallenge, RefreshToken, User
from app.schemas import LoginInput, OtpRequestInput, OtpVerifyInput, RegisterInput
from app.security import decode_access_token, hash_password, issue_access_token, new_otp, new_refresh_token, token_digest, verify_password
from app.rate_limit import SlidingWindowLimiter
from app.otp import get_otp_sender

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
auth_limiter = SlidingWindowLimiter(limit=10, window_seconds=60)


def check_auth_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_ip = resolve_client_ip(request.client.host if request.client else None, request.headers.get("x-forwarded-for"), settings.trusted_proxy_networks)
    if client_ip is None or not auth_limiter.allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests")


def set_access_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie("ah_access", token, httponly=True, secure=settings.environment == "production", samesite="lax", max_age=900, path="/")


def set_session(response: Response, user: User, session: Session, settings: Settings) -> None:
    refresh = new_refresh_token()
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email verification required")
    session.add(RefreshToken(user_id=user.id, token_hash=token_digest(refresh), token_version=user.token_version, expires_at=datetime.now(timezone.utc) + timedelta(days=14)))
    session.commit()
    set_access_cookie(response, issue_access_token(str(user.id), user.token_version, settings), settings)
    response.set_cookie("ah_refresh", refresh, httponly=True, secure=settings.environment == "production", samesite="lax", max_age=1_209_600, path="/api/v1/auth")


def issue_otp(email: str, purpose: str, session: Session, settings: Settings) -> None:
    now = datetime.now(timezone.utc)
    recent = session.scalars(select(OtpChallenge).where(OtpChallenge.email == email, OtpChallenge.purpose == purpose, OtpChallenge.created_at >= now - timedelta(hours=1))).all()
    if len(recent) >= 5:
        return
    last = session.scalar(select(OtpChallenge).where(OtpChallenge.email == email, OtpChallenge.purpose == purpose, OtpChallenge.consumed_at.is_(None), OtpChallenge.invalidated_at.is_(None)).order_by(OtpChallenge.created_at.desc()))
    if last is not None and last.created_at >= now - timedelta(seconds=60):
        return
    if last is not None:
        last.invalidated_at = now
    code = new_otp()
    session.add(OtpChallenge(email=email, purpose=purpose, code_hash=token_digest(code), expires_at=now + timedelta(minutes=5)))
    session.commit()
    get_otp_sender(settings).send(email, code, purpose)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, response: Response, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request)
    if payload.username in {"admin", "api", "platform", "login", "register", "dashboard", "www"} or not any(c.islower() for c in payload.password) or not any(c.isupper() for c in payload.password) or not any(c.isdigit() for c in payload.password) or not any(not c.isalnum() for c in payload.password):
        raise HTTPException(status_code=422, detail="Invalid registration details")
    user = User(email=str(payload.email).lower(), username=payload.username, phone=payload.phone, name=payload.name.strip(), password_hash=hash_password(payload.password), email_verified=False)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Unable to create account")
    issue_otp(user.email, "verify_email", session, settings)
    return {"status": "verification_required"}


@router.post("/login")
def login(payload: LoginInput, response: Response, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request)
    user = session.scalar(select(User).where(or_(User.email == payload.identifier.lower(), User.username == payload.identifier.lower())))
    if user is None or not verify_password(payload.password, user.password_hash) or not user.email_verified:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_session(response, user, session, settings)
    return {"id": str(user.id), "email": user.email, "name": user.name}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, ah_refresh: str | None = Cookie(default=None), session: Session = Depends(get_session)) -> Response:
    if ah_refresh:
        stored = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_digest(ah_refresh), RefreshToken.revoked_at.is_(None)))
        if stored is not None: stored.revoked_at = datetime.now(timezone.utc); session.commit()
    response.delete_cookie("ah_access", path="/")
    response.delete_cookie("ah_refresh", path="/api/v1/auth")
    return response


@router.get("/me")
def me(ah_access: str | None = Cookie(default=None), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    claims = decode_access_token(ah_access, settings) if ah_access else None
    if not claims or not isinstance(claims.get("sub"), str): raise HTTPException(status_code=401, detail="Invalid session")
    user = session.get(User, claims["sub"])
    if user is None or claims.get("ver") != user.token_version: raise HTTPException(status_code=401, detail="Invalid session")
    return {"id": str(user.id), "email": user.email, "name": user.name}


@router.post("/refresh")
def refresh(response: Response, ah_refresh: str | None = Cookie(default=None), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    if not ah_refresh: raise HTTPException(status_code=401, detail="Invalid session")
    stored = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_digest(ah_refresh)))
    if stored is None: raise HTTPException(status_code=401, detail="Invalid session")
    user = session.get(User, stored.user_id)
    if user is None or stored.revoked_at is not None or stored.expires_at < datetime.now(timezone.utc) or stored.token_version != user.token_version:
        if user is not None and stored.revoked_at is not None:
            user.token_version += 1
            session.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({RefreshToken.revoked_at: datetime.now(timezone.utc)})
            session.commit()
        raise HTTPException(status_code=401, detail="Invalid session")
    stored.revoked_at = datetime.now(timezone.utc); session.commit()
    set_session(response, user, session, settings)
    return {"status": "refreshed"}


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(response: Response, user: User = Depends(current_user), session: Session = Depends(get_session)) -> Response:
    user.token_version += 1
    session.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({RefreshToken.revoked_at: datetime.now(timezone.utc)})
    session.commit()
    response.delete_cookie("ah_access", path="/")
    response.delete_cookie("ah_refresh", path="/api/v1/auth")
    return response


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
def request_otp(payload: OtpRequestInput, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request)
    email = str(payload.email).lower()
    user = session.scalar(select(User).where(User.email == email))
    eligible = user is not None and ((payload.purpose == "verify_email" and not user.email_verified) or payload.purpose == "reset_password")
    if eligible:
        issue_otp(email, payload.purpose, session, settings)
    else:
        hmac.compare_digest(token_digest("000000"), token_digest("000000"))
    return {"status": "accepted"}


@router.post("/otp/verify")
def verify_otp(payload: OtpVerifyInput, response: Response, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    challenge = session.scalar(select(OtpChallenge).where(OtpChallenge.email == str(payload.email).lower(), OtpChallenge.purpose == payload.purpose, OtpChallenge.consumed_at.is_(None), OtpChallenge.invalidated_at.is_(None)).order_by(OtpChallenge.expires_at.desc()))
    now = datetime.now(timezone.utc)
    if challenge is None or challenge.expires_at < now or challenge.attempts >= 5 or not hmac.compare_digest(challenge.code_hash if challenge else "0" * 64, token_digest(payload.code)):
        if challenge is not None:
            challenge.attempts += 1; session.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    challenge.consumed_at = now
    if payload.purpose == "verify_email":
        user = session.scalar(select(User).where(User.email == challenge.email))
        if user is None: raise HTTPException(status_code=400, detail="Invalid verification request")
        user.email_verified = True
        session.commit()
        set_session(response, user, session, settings)
        return {"status": "verified"}
    if payload.purpose == "reset_password":
        if not payload.new_password: raise HTTPException(status_code=422, detail="A new password is required")
        user = session.scalar(select(User).where(User.email == challenge.email))
        if user is not None: user.password_hash = hash_password(payload.new_password); user.token_version += 1
    session.commit()
    return {"status": "verified"}
