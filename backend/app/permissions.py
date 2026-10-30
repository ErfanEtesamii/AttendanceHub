ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {"company.read", "company.edit", "policy.read", "policy.edit", "bot.read", "bot.manage", "members.read", "members.invite", "members.manage", "audit.read", "settings.edit", "company.danger"},
    "admin": {"company.read", "company.edit", "policy.read", "policy.edit", "bot.read", "bot.manage", "members.read", "members.invite", "members.manage", "audit.read", "settings.edit"},
    "manager": {"company.read", "members.read", "policy.read"},
    "hr": {"company.read", "members.read", "members.invite", "policy.read"},
    "employee": set(),
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
