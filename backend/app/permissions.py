ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {"company.read", "company.manage", "members.manage", "policy.manage", "audit.read"},
    "admin": {"company.read", "members.manage", "policy.manage", "audit.read"},
    "manager": {"company.read"},
    "hr": {"company.read"},
    "employee": set(),
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
