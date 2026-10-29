from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.deps import current_user, get_company_context
from app.database import get_session
from app.attendance import ip_matches_cidr, location_is_allowed
from app.bots import encrypt_bot_token, has_decryptable_token, validate_dedicated_token
from app.models import AttendancePolicy, AuditLog, BotConfiguration, Company, Invitation, Membership, PolicyGeofence, PolicyIpRange, User
from app.schemas import AttendancePolicyTestInput, AttendancePolicyUpdateInput, BotConfigurationInput, CompanyCreateInput, InvitationCreateInput, MembershipRoleUpdateInput
from app.security import new_refresh_token, token_digest

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

def require_company_permission(slug: str, user: User, session: Session, permission: str) -> Company:
    return get_company_context(slug, user, session, permission).company

@router.get("")
def list_companies(user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    rows = session.execute(select(Company, Membership.role).join(Membership).where(Membership.user_id == user.id)).all()
    return [{"name": company.name, "slug": company.slug, "role": role} for company, role in rows]

@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    if payload.mode == "ip" and not payload.allowed_cidr: raise HTTPException(status_code=422, detail="CIDR is required for IP mode")
    if payload.mode == "location" and (not payload.latitude or not payload.longitude or not payload.radius_meters): raise HTTPException(status_code=422, detail="Location is required for location mode")
    if session.scalar(select(func.count()).select_from(Membership).where(Membership.user_id == user.id)) >= 3: raise HTTPException(status_code=403, detail="Company limit reached")
    company = Company(name=payload.name.strip(), slug=payload.slug)
    session.add(company); session.flush()
    session.add(Membership(company_id=company.id, user_id=user.id, role="owner"))
    session.add(AttendancePolicy(company_id=company.id, mode=payload.mode, allowed_cidr=payload.allowed_cidr, latitude=payload.latitude, longitude=payload.longitude, radius_meters=payload.radius_meters))
    if payload.mode == "ip" and payload.allowed_cidr:
        session.add(PolicyIpRange(company_id=company.id, policy_id=company.id, cidr=payload.allowed_cidr, label="Primary network"))
    if payload.mode == "location" and payload.latitude is not None and payload.longitude is not None and payload.radius_meters:
        session.add(PolicyGeofence(company_id=company.id, policy_id=company.id, name="Primary location", latitude=float(payload.latitude), longitude=float(payload.longitude), radius_meters=payload.radius_meters))
    try: session.commit()
    except IntegrityError: session.rollback(); raise HTTPException(status_code=400, detail="Unable to create company")
    return {"name": company.name, "slug": company.slug, "role": "owner"}


def validate_attendance_policy(mode: str, allowed_cidr: str | None, latitude: float | str | None, longitude: float | str | None, radius_meters: int | None) -> None:
    if mode == "ip":
        if not allowed_cidr or not ip_matches_cidr("127.0.0.1", allowed_cidr) and not ip_matches_cidr("::1", allowed_cidr):
            # `ip_network` validation without trusting a client IP.
            from ipaddress import ip_network
            try: ip_network(allowed_cidr or "", strict=False)
            except ValueError: raise HTTPException(status_code=422, detail="A valid CIDR is required for IP mode")
        return
    if latitude is None or longitude is None or radius_meters is None:
        raise HTTPException(status_code=422, detail="Location coordinates and radius are required")


@router.get("/{slug}/attendance-policy")
def get_attendance_policy(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str | int | None]:
    company = require_company_permission(slug, user, session, "company.read")
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    return {"mode": policy.mode, "allowed_cidr": policy.allowed_cidr, "latitude": policy.latitude, "longitude": policy.longitude, "radius_meters": policy.radius_meters}


@router.put("/{slug}/attendance-policy")
def update_attendance_policy(slug: str, payload: AttendancePolicyUpdateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "policy.manage")
    validate_attendance_policy(payload.mode, payload.allowed_cidr, payload.latitude, payload.longitude, payload.radius_meters)
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    policy.mode = payload.mode
    policy.allowed_cidr = payload.allowed_cidr if payload.mode == "ip" else None
    policy.latitude = str(payload.latitude) if payload.mode == "location" else None
    policy.longitude = str(payload.longitude) if payload.mode == "location" else None
    policy.radius_meters = payload.radius_meters if payload.mode == "location" else None
    session.query(PolicyIpRange).filter(PolicyIpRange.company_id == company.id).delete()
    session.query(PolicyGeofence).filter(PolicyGeofence.company_id == company.id).delete()
    if payload.mode == "ip" and payload.allowed_cidr:
        session.add(PolicyIpRange(company_id=company.id, policy_id=company.id, cidr=payload.allowed_cidr, label="Primary network"))
    if payload.mode == "location" and payload.latitude is not None and payload.longitude is not None and payload.radius_meters:
        session.add(PolicyGeofence(company_id=company.id, policy_id=company.id, name="Primary location", latitude=payload.latitude, longitude=payload.longitude, radius_meters=payload.radius_meters))
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="attendance_policy.updated")); session.commit()
    return {"status": "saved", "mode": policy.mode}


@router.post("/{slug}/attendance-policy/test")
def test_attendance_policy(slug: str, payload: AttendancePolicyTestInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, bool | str]:
    company = require_company_permission(slug, user, session, "policy.manage")
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    if policy.mode == "ip":
        allowed = bool(payload.ip and policy.allowed_cidr and ip_matches_cidr(payload.ip, policy.allowed_cidr))
    else:
        allowed = bool(payload.latitude is not None and payload.longitude is not None and payload.accuracy_meters is not None and policy.latitude and policy.longitude and policy.radius_meters and location_is_allowed(payload.latitude, payload.longitude, payload.accuracy_meters, float(policy.latitude), float(policy.longitude), policy.radius_meters))
    return {"mode": policy.mode, "allowed": allowed}


@router.get("/{slug}/audit")
def list_audit(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    company = require_company_permission(slug, user, session, "audit.read")
    entries = session.scalars(select(AuditLog).where(AuditLog.company_id == company.id).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [{"action": entry.action, "created_at": entry.created_at.isoformat()} for entry in entries]


@router.get("/{slug}/members")
def list_members(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    company = require_company_permission(slug, user, session, "company.read")
    rows = session.execute(select(User, Membership.role).join(Membership).where(Membership.company_id == company.id)).all()
    return [{"email": member.email, "name": member.name, "role": role} for member, role in rows]


@router.post("/{slug}/invitations", status_code=status.HTTP_201_CREATED)
def create_invitation(slug: str, payload: InvitationCreateInput, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "members.manage")
    token = new_refresh_token()
    invitation = Invitation(company_id=company.id, email=str(payload.email).lower(), role=payload.role, token_hash=token_digest(token), expires_at=datetime.now(timezone.utc) + timedelta(days=7))
    session.add(invitation)
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="invitation.created")); session.commit()
    # Delivery is intentionally isolated from the API response; do not expose tokens to callers.
    if settings.environment == "development": print(f"Invitation URL: {settings.app_public_url}/dashboard/invitations?token={token}")
    return {"status": "created"}


@router.post("/invitations/accept")
def accept_invitation(token: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    invitation = session.scalar(select(Invitation).where(Invitation.token_hash == token_digest(token), Invitation.accepted_at.is_(None)))
    now = datetime.now(timezone.utc)
    if invitation is None or invitation.expires_at < now or invitation.email != user.email:
        raise HTTPException(status_code=404, detail="Invitation not found")
    existing = session.scalar(select(Membership).where(Membership.company_id == invitation.company_id, Membership.user_id == user.id))
    if existing is None: session.add(Membership(company_id=invitation.company_id, user_id=user.id, role=invitation.role))
    invitation.accepted_at = now; session.add(AuditLog(company_id=invitation.company_id, actor_id=user.id, action="invitation.accepted")); session.commit()
    company = session.get(Company, invitation.company_id)
    return {"status": "accepted", "slug": company.slug}


@router.patch("/{slug}/members/{member_email}")
def update_member_role(slug: str, member_email: str, payload: MembershipRoleUpdateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "members.manage")
    member = session.scalar(select(User).where(User.email == member_email.lower()))
    membership = session.scalar(select(Membership).where(Membership.company_id == company.id, Membership.user_id == member.id)) if member else None
    if membership is None or membership.role == "owner":
        raise HTTPException(status_code=404, detail="Member not found")
    membership.role = payload.role
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="member.role_updated")); session.commit()
    return {"email": member.email, "role": membership.role}


@router.get("/{slug}/bot")
def get_bot_configuration(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str | bool | None]:
    company = require_company_permission(slug, user, session, "company.read")
    configuration = session.get(BotConfiguration, company.id)
    if configuration is None:
        return {"mode": "shared", "username": settings.shared_bot_username, "dedicated_configured": False}
    return {"mode": configuration.mode, "username": configuration.username, "dedicated_configured": has_decryptable_token(configuration.token_ciphertext, settings)}


@router.get("/{slug}/bot/health")
def bot_health(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "company.read")
    configuration = session.get(BotConfiguration, company.id)
    if configuration is None or configuration.mode == "shared":
        return {"status": "ready" if settings.shared_bot_username else "not_configured", "mode": "shared"}
    return {"status": "ready" if has_decryptable_token(configuration.token_ciphertext, settings) else "not_configured", "mode": "dedicated"}


@router.put("/{slug}/bot")
def configure_bot(slug: str, payload: BotConfigurationInput, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "company.manage")
    if payload.mode == "dedicated" and (not payload.dedicated_token or not validate_dedicated_token(payload.dedicated_token)):
        raise HTTPException(status_code=422, detail="A valid dedicated bot token is required")
    configuration = session.get(BotConfiguration, company.id) or BotConfiguration(company_id=company.id)
    configuration.mode, configuration.username = payload.mode, payload.username
    if payload.mode == "dedicated" and payload.dedicated_token:
        configuration.token_ciphertext = encrypt_bot_token(payload.dedicated_token, settings)
    elif payload.mode == "shared":
        configuration.token_ciphertext = None
    session.add(configuration); session.add(AuditLog(company_id=company.id, actor_id=user.id, action="bot.configured")); session.commit()
    return {"mode": configuration.mode, "status": "saved"}
