from collections import defaultdict, deque
from time import monotonic


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit, self.window_seconds = limit, window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allowed(self, key: str) -> bool:
        now, window = monotonic(), self.hits[key]
        while window and window[0] <= now - self.window_seconds: window.popleft()
        if len(window) >= self.limit: return False
        window.append(now); return True
