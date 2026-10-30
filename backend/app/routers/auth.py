from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.client_ip import resolve_client_ip
from app.database import get_session
from app.deps import current_user
from app.models import OtpChallenge, RefreshToken, User
from app.schemas import ChangePasswordInput, LoginInput, OtpRequestInput, OtpVerifyInput, PreferencesInput, ProfileUpdateInput, RegisterInput, TwoFactorInput
from app.security import decode_access_token, decode_login_challenge, hash_password, is_strong_password, issue_access_token, issue_login_challenge, new_otp, new_refresh_token, token_digest, verify_password
from app.rate_limit import allow_request
from app.otp import get_otp_sender

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
_dummy_password_hash = hash_password("DummyPassword1!")


def check_auth_rate_limit(request: Request, session: Session, identifier: str | None = None) -> None:
    settings = get_settings()
    client_ip = resolve_client_ip(request.client.host if request.client else None, request.headers.get("x-forwarded-for"), settings.trusted_proxy_networks)
    if client_ip is None or not allow_request(session, f"auth:ip:{client_ip}", 10, 60):
        raise HTTPException(status_code=429, detail="Too many requests")
    if identifier is not None and not allow_request(session, f"auth:identifier:{identifier.casefold()}", 5, 900):
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
    lock_key = int.from_bytes(sha256(f"otp:{email}:{purpose}".encode()).digest()[:8], "big", signed=True)
    session.execute(select(func.pg_advisory_xact_lock(lock_key)))
    recent = session.scalars(
        select(OtpChallenge).where(
            OtpChallenge.email == email,
            OtpChallenge.purpose == purpose,
            OtpChallenge.created_at >= now - timedelta(hours=1),
        ).order_by(OtpChallenge.created_at.desc())
    ).all()
    if len(recent) >= 5:
        session.commit()
        return
    if recent and recent[0].created_at >= now - timedelta(seconds=60):
        session.commit()
        return
    session.execute(
        update(OtpChallenge).where(
            OtpChallenge.email == email,
            OtpChallenge.purpose == purpose,
            OtpChallenge.consumed_at.is_(None),
            OtpChallenge.invalidated_at.is_(None),
        ).values(invalidated_at=now)
    )
    code = new_otp()
    session.add(OtpChallenge(email=email, purpose=purpose, code_hash=token_digest(code), expires_at=now + timedelta(minutes=5)))
    session.commit()
    get_otp_sender(settings).send(email, code, purpose)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, response: Response, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request, session)
    if payload.username in {"admin", "api", "platform", "login", "register", "dashboard", "www"} or not is_strong_password(payload.password):
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
    check_auth_rate_limit(request, session, payload.identifier)
    user = session.scalar(select(User).where(or_(User.email == payload.identifier.lower(), User.username == payload.identifier.lower())))
    password_matches = verify_password(payload.password, user.password_hash if user else _dummy_password_hash)
    if user is None or not password_matches or not user.email_verified:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.two_factor_enabled:
        issue_otp(user.email, "login_2fa", session, settings)
        response.set_cookie("ah_login_challenge", issue_login_challenge(str(user.id), user.token_version, settings), httponly=True, secure=settings.environment == "production", samesite="lax", max_age=300, path="/api/v1/auth/otp")
        return {"status": "two_factor_required", "email": user.email}
    set_session(response, user, session, settings)
    return {"id": str(user.id), "email": user.email, "name": user.name}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, ah_refresh: str | None = Cookie(default=None), session: Session = Depends(get_session)) -> Response:
    if ah_refresh:
        stored = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_digest(ah_refresh), RefreshToken.revoked_at.is_(None)))
        if stored is not None: stored.revoked_at = datetime.now(timezone.utc); session.commit()
    response.delete_cookie("ah_access", path="/")
    response.delete_cookie("ah_refresh", path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
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
    stored = session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_digest(ah_refresh)).with_for_update())
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
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.patch("/me")
def update_profile(payload: ProfileUpdateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    user.name = payload.name.strip()
    session.commit()
    return {"name": user.name}


@router.get("/preferences")
def preferences(user: User = Depends(current_user)) -> dict[str, str]:
    return {"locale": user.locale, "theme": user.theme}


@router.patch("/preferences")
def update_preferences(payload: PreferencesInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    user.locale, user.theme = payload.locale, payload.theme
    session.commit()
    return {"locale": user.locale, "theme": user.theme}


@router.patch("/two-factor")
def update_two_factor(payload: TwoFactorInput, response: Response, user: User = Depends(current_user), session: Session = Depends(get_session)) -> Response:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    user.two_factor_enabled = payload.enabled
    user.token_version += 1
    session.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({RefreshToken.revoked_at: datetime.now(timezone.utc)})
    session.commit()
    response.delete_cookie("ah_access", path="/")
    response.delete_cookie("ah_refresh", path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/two-factor")
def get_two_factor(user: User = Depends(current_user)) -> dict[str, bool]:
    return {"enabled": user.two_factor_enabled}


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ChangePasswordInput, response: Response, user: User = Depends(current_user), session: Session = Depends(get_session)) -> Response:
    if not verify_password(payload.current_password, user.password_hash) or not is_strong_password(payload.new_password):
        raise HTTPException(status_code=400, detail="Invalid password")
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    session.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({RefreshToken.revoked_at: datetime.now(timezone.utc)})
    session.commit()
    response.delete_cookie("ah_access", path="/")
    response.delete_cookie("ah_refresh", path="/api/v1/auth")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/otp/request", status_code=status.HTTP_202_ACCEPTED)
def request_otp(payload: OtpRequestInput, request: Request, session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    check_auth_rate_limit(request, session)
    email = str(payload.email).lower()
    user = session.scalar(select(User).where(User.email == email))
    eligible = user is not None and ((payload.purpose == "verify_email" and not user.email_verified) or payload.purpose == "reset_password")
    if eligible:
        issue_otp(email, payload.purpose, session, settings)
    else:
        hmac.compare_digest(token_digest("000000"), token_digest("000000"))
    return {"status": "accepted"}


@router.post("/otp/verify")
def verify_otp(payload: OtpVerifyInput, response: Response, ah_login_challenge: str | None = Cookie(default=None), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    login_user = None
    if payload.purpose == "login_2fa":
        claims = decode_login_challenge(ah_login_challenge or "", settings)
        login_user = session.get(User, claims["sub"]) if claims and isinstance(claims.get("sub"), str) else None
        if login_user is None or login_user.email != str(payload.email).lower() or not login_user.two_factor_enabled or claims.get("ver") != login_user.token_version:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    challenge = session.scalar(select(OtpChallenge).where(OtpChallenge.email == str(payload.email).lower(), OtpChallenge.purpose == payload.purpose, OtpChallenge.consumed_at.is_(None), OtpChallenge.invalidated_at.is_(None)).order_by(OtpChallenge.expires_at.desc()).with_for_update())
    now = datetime.now(timezone.utc)
    code_matches = hmac.compare_digest(challenge.code_hash if challenge else "0" * 64, token_digest(payload.code))
    if challenge is None or challenge.expires_at < now or challenge.attempts >= 5 or not code_matches:
        if challenge is not None:
            challenge.attempts += 1
            if challenge.attempts >= 5:
                challenge.invalidated_at = now
            session.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    challenge.consumed_at = now
    if payload.purpose == "login_2fa" and login_user is not None:
        session.commit()
        response.delete_cookie("ah_login_challenge", path="/api/v1/auth/otp")
        set_session(response, login_user, session, settings)
        return {"status": "verified"}
    if payload.purpose == "verify_email":
        user = session.scalar(select(User).where(User.email == challenge.email))
        if user is None: raise HTTPException(status_code=400, detail="Invalid verification request")
        user.email_verified = True
        session.commit()
        set_session(response, user, session, settings)
        return {"status": "verified"}
    if payload.purpose == "reset_password":
        if not payload.new_password or not is_strong_password(payload.new_password):
            raise HTTPException(status_code=422, detail="A strong new password is required")
        user = session.scalar(select(User).where(User.email == challenge.email))
        if user is not None:
            user.password_hash = hash_password(payload.new_password)
            user.token_version += 1
            session.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({RefreshToken.revoked_at: now})
    session.commit()
    return {"status": "verified"}
