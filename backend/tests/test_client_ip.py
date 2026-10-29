from app.client_ip import resolve_client_ip


def test_only_trusted_peers_can_supply_forwarded_ip() -> None:
    assert resolve_client_ip("10.0.0.2", "198.51.100.8, 10.0.0.3", ["10.0.0.0/8"]) == "198.51.100.8"
    assert resolve_client_ip("198.51.100.9", "203.0.113.1", ["10.0.0.0/8"]) == "198.51.100.9"
    assert resolve_client_ip("10.0.0.2", "broken", ["10.0.0.0/8"]) is None
