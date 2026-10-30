from app.attendance import haversine_meters, ip_matches_cidr, location_is_allowed
from datetime import datetime, timedelta, timezone


def test_cidr_checks_ipv4_ipv6_and_invalid_values() -> None:
    assert ip_matches_cidr("192.168.10.7", "192.168.10.0/24")
    assert not ip_matches_cidr("192.168.11.7", "192.168.10.0/24")
    assert ip_matches_cidr("2001:db8::1", "2001:db8::/64")
    assert not ip_matches_cidr("not-an-ip", "192.168.10.0/24")


def test_haversine_and_accuracy_threshold() -> None:
    assert haversine_meters(35.6892, 51.3890, 35.6892, 51.3890) == 0
    assert location_is_allowed(35.6892, 51.3890, 10, 35.6892, 51.3890, 50)
    assert not location_is_allowed(35.6892, 51.3890, 150, 35.6892, 51.3890, 50)


def test_location_rejects_stale_future_and_invalid_fixes() -> None:
    now = datetime.now(timezone.utc)
    assert not location_is_allowed(35.6892, 51.3890, 10, 35.6892, 51.3890, 50, timestamp=now - timedelta(seconds=61))
    assert not location_is_allowed(35.6892, 51.3890, 10, 35.6892, 51.3890, 50, timestamp=now + timedelta(seconds=61))
    assert not location_is_allowed(float("nan"), 51.3890, 10, 35.6892, 51.3890, 50)
    assert not location_is_allowed(0, 0, 10, 0, 0, 20, timestamp=now + timedelta(seconds=1))
    assert location_is_allowed(0, 0, 10, 0, 0, 20, timestamp=now)
