import time


class RateLimiter:
    def __init__(self, cooldown: float = 1.0):
        self._cooldown = cooldown
        self._last: dict[int, float] = {}

    def check(self, user_id: int) -> bool:
        now = time.monotonic()
        last = self._last.get(user_id, 0.0)
        if now - last < self._cooldown:
            return False
        self._last[user_id] = now
        return True
