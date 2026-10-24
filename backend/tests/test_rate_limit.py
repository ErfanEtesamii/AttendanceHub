from app.rate_limit import SlidingWindowLimiter


def test_limiter_rejects_over_limit() -> None:
    limiter = SlidingWindowLimiter(2, 60)
    assert limiter.allowed("ip") and limiter.allowed("ip") and not limiter.allowed("ip")
