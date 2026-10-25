from ipaddress import ip_address, ip_network
from math import asin, cos, radians, sin, sqrt


def ip_matches_cidr(client_ip: str, allowed_cidr: str) -> bool:
    """Fail closed for invalid or mismatched IP versions."""
    try:
        return ip_address(client_ip) in ip_network(allowed_cidr, strict=False)
    except ValueError:
        return False


def haversine_meters(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius = 6_371_000
    d_lat, d_lon = radians(lat_b - lat_a), radians(lon_b - lon_a)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(d_lon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def location_is_allowed(lat: float, lon: float, accuracy_meters: float, policy_lat: float, policy_lon: float, radius_meters: float, max_accuracy_meters: float = 100) -> bool:
    return accuracy_meters <= max_accuracy_meters and haversine_meters(lat, lon, policy_lat, policy_lon) <= radius_meters
