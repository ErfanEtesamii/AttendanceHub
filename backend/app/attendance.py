from ipaddress import ip_address, ip_network
from math import asin, cos, radians, sin, sqrt
from datetime import datetime, timezone
from math import isfinite


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


def location_is_allowed(lat: float, lon: float, accuracy_meters: float, policy_lat: float, policy_lon: float, radius_meters: float, max_accuracy_meters: float = 50, timestamp: datetime | None = None, max_fix_age_seconds: int = 60) -> bool:
    values = (lat, lon, accuracy_meters, policy_lat, policy_lon, radius_meters, max_accuracy_meters)
    if not all(isfinite(value) for value in values) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return False
    if timestamp is not None:
        timestamp = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
        if age_seconds < 0 or age_seconds > max_fix_age_seconds:
            return False
    return accuracy_meters <= max_accuracy_meters and haversine_meters(lat, lon, policy_lat, policy_lon) <= radius_meters
