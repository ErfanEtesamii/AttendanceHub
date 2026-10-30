from datetime import datetime, timedelta, timezone
from ipaddress import ip_network

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.deps import current_user, get_company_context
from app.database import get_session
from app.attendance import haversine_meters, ip_matches_cidr, location_is_allowed
from app.client_ip import resolve_client_ip
from app.bots import encrypt_bot_token, has_decryptable_token, validate_dedicated_token
from app.models import AttendancePolicy, AuditLog, BotConfiguration, Company, Invitation, Membership, PolicyGeofence, PolicyIpRange, User
from app.schemas import AttendancePolicyTestInput, AttendancePolicyUpdateInput, BotConfigurationInput, CompanyCreateInput, CompanyUpdateInput, InvitationAcceptInput, InvitationCreateInput, MembershipRoleUpdateInput
from app.security import new_refresh_token, token_digest

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])

def require_company_permission(slug: str, user: User, session: Session, permission: str) -> Company:
    return get_company_context(slug, user, session, permission).company

@router.get("")
def list_companies(user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    rows = session.execute(select(Company, Membership.role).join(Membership).where(Membership.user_id == user.id, Membership.status == "active", Company.status == "active")).all()
    return [{"name": company.name, "slug": company.slug, "role": role} for company, role in rows]


@router.get("/{slug}/overview")
def company_overview(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str | int | bool]:
    company = require_company_permission(slug, user, session, "company.read")
    policy = session.get(AttendancePolicy, company.id)
    bot = session.get(BotConfiguration, company.id)
    member_count = session.scalar(select(func.count()).select_from(Membership).where(Membership.company_id == company.id, Membership.status == "active"))
    return {"name": company.name, "status": company.status, "member_count": member_count or 0, "attendance_mode": policy.mode if policy else "not_configured", "bot_configured": bot is not None}

@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    if payload.slug in {"admin", "api", "auth", "dashboard", "login", "platform", "register", "www"}:
        raise HTTPException(status_code=422, detail="Reserved company slug")
    normalized_cidr = validate_attendance_policy(payload.mode, payload.allowed_cidr, payload.latitude, payload.longitude, payload.radius_meters, payload.confirm_wide_range)
    count = session.scalar(
        select(func.count()).select_from(Membership).where(
            Membership.user_id == user.id,
            Membership.role == "owner",
            Membership.status == "active",
        )
    )
    if count is not None and count >= 3:
        raise HTTPException(status_code=403, detail="Company limit reached")
    company = Company(name=payload.name.strip(), slug=payload.slug)
    try:
        session.add(company)
        session.flush()
        session.add(Membership(company_id=company.id, user_id=user.id, role="owner"))
        session.add(
            AttendancePolicy(
                company_id=company.id,
                mode=payload.mode,
                allowed_cidr=normalized_cidr,
                latitude=str(payload.latitude) if payload.latitude is not None else None,
                longitude=str(payload.longitude) if payload.longitude is not None else None,
                radius_meters=payload.radius_meters,
                updated_by=user.id,
            )
        )
        if payload.mode == "ip" and normalized_cidr:
            session.add(PolicyIpRange(company_id=company.id, policy_id=company.id, cidr=normalized_cidr, label="Primary network"))
        if payload.mode == "location" and payload.latitude is not None and payload.longitude is not None and payload.radius_meters is not None:
            session.add(PolicyGeofence(company_id=company.id, policy_id=company.id, name="Primary location", latitude=payload.latitude, longitude=payload.longitude, radius_meters=payload.radius_meters))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Unable to create company")
    return {"name": company.name, "slug": company.slug, "role": "owner"}


@router.get("/{slug}")
def get_company(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str | None]:
    company = require_company_permission(slug, user, session, "company.read")
    return {"name": company.name, "name_en": company.name_en, "industry": company.industry, "city": company.city, "phone": company.phone, "timezone": company.timezone}


@router.patch("/{slug}")
def update_company(slug: str, payload: CompanyUpdateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str | None]:
    company = require_company_permission(slug, user, session, "company.edit")
    company.name = payload.name.strip()
    company.name_en = payload.name_en
    company.industry = payload.industry
    company.city = payload.city
    company.phone = payload.phone
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="company.updated"))
    session.commit()
    return {"name": company.name, "name_en": company.name_en}


def validate_attendance_policy(mode: str, allowed_cidr: str | None, latitude: float | str | None, longitude: float | str | None, radius_meters: int | None, confirm_wide_range: bool = False) -> str | None:
    if mode == "ip":
        try:
            network = ip_network(allowed_cidr or "", strict=True)
        except ValueError:
            raise HTTPException(status_code=422, detail="A valid CIDR is required for IP mode")
        if network.prefixlen == 0:
            raise HTTPException(status_code=422, detail="Unrestricted network is not allowed")
        if not confirm_wide_range and network.prefixlen < (16 if network.version == 4 else 48):
            raise HTTPException(status_code=422, detail="Wide network requires confirmation")
        return str(network)
    if latitude is None or longitude is None or radius_meters is None:
        raise HTTPException(status_code=422, detail="Location coordinates and radius are required")
    return None


@router.get("/{slug}/attendance-policy")
def get_attendance_policy(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str | int | None]:
    company = require_company_permission(slug, user, session, "policy.read")
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    return {"mode": policy.mode, "allowed_cidr": policy.allowed_cidr, "latitude": policy.latitude, "longitude": policy.longitude, "radius_meters": policy.radius_meters}


@router.put("/{slug}/attendance-policy")
def update_attendance_policy(slug: str, payload: AttendancePolicyUpdateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "policy.edit")
    normalized_cidr = validate_attendance_policy(payload.mode, payload.allowed_cidr, payload.latitude, payload.longitude, payload.radius_meters, payload.confirm_wide_range)
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    policy.mode = payload.mode
    policy.allowed_cidr = normalized_cidr
    policy.latitude = str(payload.latitude) if payload.mode == "location" else None
    policy.longitude = str(payload.longitude) if payload.mode == "location" else None
    policy.radius_meters = payload.radius_meters if payload.mode == "location" else None
    session.query(PolicyIpRange).filter(PolicyIpRange.company_id == company.id).delete()
    session.query(PolicyGeofence).filter(PolicyGeofence.company_id == company.id).delete()
    if payload.mode == "ip" and normalized_cidr:
        session.add(PolicyIpRange(company_id=company.id, policy_id=company.id, cidr=normalized_cidr, label="Primary network"))
    if payload.mode == "location" and payload.latitude is not None and payload.longitude is not None and payload.radius_meters:
        session.add(PolicyGeofence(company_id=company.id, policy_id=company.id, name="Primary location", latitude=payload.latitude, longitude=payload.longitude, radius_meters=payload.radius_meters))
    policy.updated_by = user.id
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="attendance_policy.updated")); session.commit()
    return {"status": "saved", "mode": policy.mode}


@router.post("/{slug}/attendance-policy/test")
def test_attendance_policy(slug: str, payload: AttendancePolicyTestInput, request: Request, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, bool | str | float | None]:
    company = require_company_permission(slug, user, session, "policy.edit")
    policy = session.get(AttendancePolicy, company.id)
    if policy is None: raise HTTPException(status_code=404, detail="Policy not found")
    if policy.mode == "ip":
        client_ip = resolve_client_ip(request.client.host if request.client else None, request.headers.get("x-forwarded-for"), settings.trusted_proxy_networks)
        ranges = session.scalars(select(PolicyIpRange).where(PolicyIpRange.company_id == company.id)).all()
        allowed = bool(client_ip and any(ip_matches_cidr(client_ip, item.cidr) for item in ranges))
        return {"mode": policy.mode, "allowed": allowed, "reason": "within_allowed_network" if allowed else "outside_allowed_network"}
    else:
        if payload.latitude is None or payload.longitude is None or payload.accuracy_meters is None or payload.timestamp is None:
            return {"mode": policy.mode, "allowed": False, "reason": "missing_location_fix", "distance_meters": None}
        geofences = session.scalars(select(PolicyGeofence).where(PolicyGeofence.company_id == company.id)).all()
        distances = [haversine_meters(payload.latitude, payload.longitude, fence.latitude, fence.longitude) for fence in geofences]
        allowed = any(location_is_allowed(payload.latitude, payload.longitude, payload.accuracy_meters, fence.latitude, fence.longitude, fence.radius_meters, policy.max_accuracy_meters, payload.timestamp, policy.max_fix_age_seconds) for fence in geofences)
        return {"mode": policy.mode, "allowed": allowed, "reason": "within_geofence" if allowed else "location_rejected", "distance_meters": min(distances) if distances else None}


@router.get("/{slug}/audit")
def list_audit(slug: str, action: str | None = None, limit: int = 100, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    company = require_company_permission(slug, user, session, "audit.read")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="Invalid limit")
    statement = select(AuditLog).where(AuditLog.company_id == company.id)
    if action:
        statement = statement.where(AuditLog.action == action)
    entries = session.scalars(statement.order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [{"action": entry.action, "created_at": entry.created_at.isoformat()} for entry in entries]


@router.get("/{slug}/members")
def list_members(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str]]:
    context = get_company_context(slug, user, session, "members.read")
    company = context.company
    rows = session.execute(select(User, Membership).join(Membership).where(Membership.company_id == company.id)).all()
    return [
        {
            "id": str(membership.id),
            "name": member.name,
            "role": membership.role,
            "status": membership.status,
            **({"email": member.email} if context.membership.role in {"owner", "admin", "hr"} else {}),
        }
        for member, membership in rows
    ]


@router.patch("/{slug}/members/{member_id}/status")
def update_member_status(slug: str, member_id: str, member_status: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "members.manage")
    if member_status not in {"active", "suspended"}:
        raise HTTPException(status_code=422, detail="Invalid member status")
    membership = session.scalar(select(Membership).where(Membership.id == member_id, Membership.company_id == company.id))
    if membership is None or membership.role == "owner" or membership.user_id == user.id:
        raise HTTPException(status_code=404, detail="Member not found")
    membership.status = member_status
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="member.status_updated"))
    session.commit()
    return {"id": str(membership.id), "status": membership.status}


@router.post("/{slug}/invitations", status_code=status.HTTP_201_CREATED)
def create_invitation(slug: str, payload: InvitationCreateInput, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "members.invite")
    token = new_refresh_token()
    invitation = Invitation(company_id=company.id, email=str(payload.email).lower(), role=payload.role, token_hash=token_digest(token), expires_at=datetime.now(timezone.utc) + timedelta(days=7))
    session.add(invitation)
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="invitation.created")); session.commit()
    # Delivery is intentionally isolated from the API response; do not expose tokens to callers.
    if settings.environment == "development": print(f"Invitation URL: {settings.app_public_url}/dashboard/invitations?token={token}")
    return {"status": "created"}


@router.get("/{slug}/invitations")
def list_invitations(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> list[dict[str, str | None]]:
    company = require_company_permission(slug, user, session, "members.invite")
    invitations = session.scalars(select(Invitation).where(Invitation.company_id == company.id).order_by(Invitation.expires_at.desc())).all()
    return [{"id": str(item.id), "email": item.email, "role": item.role, "expires_at": item.expires_at.isoformat(), "accepted_at": item.accepted_at.isoformat() if item.accepted_at else None} for item in invitations]


@router.delete("/{slug}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(slug: str, invitation_id: str, user: User = Depends(current_user), session: Session = Depends(get_session)) -> None:
    company = require_company_permission(slug, user, session, "members.invite")
    invitation = session.scalar(select(Invitation).where(Invitation.id == invitation_id, Invitation.company_id == company.id, Invitation.accepted_at.is_(None)))
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    session.delete(invitation)
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="invitation.revoked"))
    session.commit()


@router.post("/invitations/accept")
def accept_invitation(payload: InvitationAcceptInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    invitation = session.scalar(select(Invitation).where(Invitation.token_hash == token_digest(payload.token), Invitation.accepted_at.is_(None)).with_for_update())
    now = datetime.now(timezone.utc)
    if invitation is None or invitation.expires_at < now or invitation.email != user.email:
        raise HTTPException(status_code=404, detail="Invitation not found")
    existing = session.scalar(select(Membership).where(Membership.company_id == invitation.company_id, Membership.user_id == user.id))
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Verified email required")
    if existing is None:
        session.add(Membership(company_id=invitation.company_id, user_id=user.id, role=invitation.role))
    elif existing.status != "active":
        existing.status = "active"
    invitation.accepted_at = now; session.add(AuditLog(company_id=invitation.company_id, actor_id=user.id, action="invitation.accepted")); session.commit()
    company = session.get(Company, invitation.company_id)
    return {"status": "accepted", "slug": company.slug}


@router.patch("/{slug}/members/id/{member_id}/role")
def update_member_role_by_id(slug: str, member_id: str, payload: MembershipRoleUpdateInput, user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "members.manage")
    membership = session.scalar(select(Membership).where(Membership.id == member_id, Membership.company_id == company.id))
    if membership is None or membership.role == "owner" or membership.user_id == user.id:
        raise HTTPException(status_code=404, detail="Member not found")
    membership.role = payload.role
    session.add(AuditLog(company_id=company.id, actor_id=user.id, action="member.role_updated"))
    session.commit()
    return {"id": str(membership.id), "role": membership.role}


@router.get("/{slug}/bot")
def get_bot_configuration(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str | bool | None]:
    company = require_company_permission(slug, user, session, "bot.read")
    configuration = session.get(BotConfiguration, company.id)
    if configuration is None:
        return {"mode": "shared", "username": settings.shared_bot_username, "dedicated_configured": False}
    return {"mode": configuration.mode, "username": configuration.username, "dedicated_configured": has_decryptable_token(configuration.token_ciphertext, settings)}


@router.get("/{slug}/bot/health")
def bot_health(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "bot.read")
    configuration = session.get(BotConfiguration, company.id)
    if configuration is None or configuration.mode == "shared":
        return {"status": "ready" if settings.shared_bot_username else "not_configured", "mode": "shared"}
    return {"status": "ready" if has_decryptable_token(configuration.token_ciphertext, settings) else "not_configured", "mode": "dedicated"}


@router.put("/{slug}/bot")
def configure_bot(slug: str, payload: BotConfigurationInput, user: User = Depends(current_user), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    company = require_company_permission(slug, user, session, "bot.manage")
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
