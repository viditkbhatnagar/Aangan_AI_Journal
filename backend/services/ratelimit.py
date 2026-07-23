"""Tiny in-memory sliding-window rate limiter (per-IP, per-scope). Enough for
a single-node pilot; swap for a shared store when horizontally scaled."""
import time
from collections import defaultdict, deque

_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def allow(ip: str, scope: str, max_hits: int, window_sec: int) -> bool:
    now = time.monotonic()
    bucket = _hits[(ip, scope)]
    while bucket and now - bucket[0] > window_sec:
        bucket.popleft()
    if len(bucket) >= max_hits:
        return False
    bucket.append(now)
    return True


def reset() -> None:
    _hits.clear()
