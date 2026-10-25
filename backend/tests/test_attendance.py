from app.attendance import haversine_meters, ip_matches_cidr, location_is_allowed


def test_cidr_checks_ipv4_ipv6_and_invalid_values() -> None:
    assert ip_matches_cidr("192.168.10.7", "192.168.10.0/24")
    assert not ip_matches_cidr("192.168.11.7", "192.168.10.0/24")
    assert ip_matches_cidr("2001:db8::1", "2001:db8::/64")
    assert not ip_matches_cidr("not-an-ip", "192.168.10.0/24")


def test_haversine_and_accuracy_threshold() -> None:
    assert haversine_meters(35.6892, 51.3890, 35.6892, 51.3890) == 0
    assert location_is_allowed(35.6892, 51.3890, 10, 35.6892, 51.3890, 50)
    assert not location_is_allowed(35.6892, 51.3890, 150, 35.6892, 51.3890, 50)
