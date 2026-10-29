from ipaddress import ip_address, ip_network


def resolve_client_ip(peer_ip: str | None, forwarded_for: str | None, trusted_proxies: list[str]) -> str | None:
    try:
        peer = ip_address(peer_ip or "")
        trusted = [ip_network(value, strict=False) for value in trusted_proxies]
    except ValueError:
        return None
    if not any(peer in network for network in trusted):
        return str(peer)
    if not forwarded_for:
        return None
    try:
        chain = [ip_address(value.strip()) for value in forwarded_for.split(",")]
    except ValueError:
        return None
    for address in reversed(chain):
        if not any(address in network for network in trusted):
            return str(address)
    return None
