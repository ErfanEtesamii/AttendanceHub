from app.permissions import has_permission


def test_permissions_are_default_deny() -> None:
    assert has_permission("owner", "members.manage")
    assert has_permission("admin", "policy.edit")
    assert not has_permission("employee", "company.edit")
    assert not has_permission("unknown", "company.read")
