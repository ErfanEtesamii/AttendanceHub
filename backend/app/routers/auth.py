from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_session
from app.models import OtpChallenge, RefreshToken, User
from app.schemas import LoginInput, OtpRequestInput, OtpVerifyInput, RegisterInput
from app.security import decode_access_token, hash_password, issue_access_token, new_otp, new_refresh_token, token_digest, verify_password
from app.rate_limit import SlidingWindowLimiter
from app.otp import get_otp_sender

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
auth_limiter = SlidingWindowLimiter(limit=10, window_seconds=60)


def check_auth_rate_limit(request: Request) -> None:
    if not auth_limiter.allowed(request.client.host if request.client else "unknown"):
        raise HTTPException(status_code=429, detail="Too many requests")


def set_access_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie("ah_access", token, httponly=True, secure=settings.environment == "production", samesite="lax", max_age=900, path="/")


def set_session(response: Response, user: User, session: Session, settings: Settings) -> None:
    refresh = new_refresh_token()
    session.add(RefreshToken(user_id=user.id, token_hash=token_digest(refresh), expires_at=datetime.now(timezone.utc) + timedelta(days=14)))
    session.commit()
    set_access_cookie(response, issue_access_token(str(user.id), user.token_version, settings), settings)
    response.set_cookie("ah_refresh", refresh, httponly=True, secure=settings.environment == "production", samesite="lax", max_age=1_209_600, path="/api/v1/auth")


def issue_otp(email: str, purpose: str, session: Session, settings: Settings) -> None:
    code = new_otp()
    session.add(OtpChallenge(email=email, purpose=purpose, code_hash=token_digest(code), expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
    session.commit()
    get_otp_sender(settings).send(email, code, purpose)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, response: Response, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request)
    user = User(email=str(payload.email).lower(), name=payload.name.strip(), password_hash=hash_password(payload.password), email_verified=False)
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
    user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
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
    stored = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_digest(ah_refresh), RefreshToken.revoked_at.is_(None)))
    if stored is None or stored.expires_at < datetime.now(timezone.utc): raise HTTPException(status_code=401, detail="Invalid session")
    user = session.get(User, stored.user_id)
    if user is None: raise HTTPException(status_code=401, detail="Invalid session")
    stored.revoked_at = datetime.now(timezone.utc); session.commit()
    set_session(response, user, session, settings)
    return {"status": "refreshed"}


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
def request_otp(payload: OtpRequestInput, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request)
    issue_otp(str(payload.email).lower(), payload.purpose, session, settings)
    return {"status": "accepted"}


@router.post("/otp/verify")
def verify_otp(payload: OtpVerifyInput, response: Response, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    challenge = session.scalar(select(OtpChallenge).where(OtpChallenge.email == str(payload.email).lower(), OtpChallenge.purpose == payload.purpose, OtpChallenge.consumed_at.is_(None)).order_by(OtpChallenge.expires_at.desc()))
    now = datetime.now(timezone.utc)
    if challenge is None or challenge.expires_at < now or challenge.attempts >= 5 or challenge.code_hash != token_digest(payload.code):
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
