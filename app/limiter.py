"""Thread-Safe Sliding-Window Rate Limiter for Production API Endpoints.
"""
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple


class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = Lock()
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check rate limit eligibility.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._requests[client_key]
            # Retain only timestamps within the current sliding window
            valid_timestamps = [t for t in timestamps if t > cutoff]
            self._requests[client_key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                return False, retry_after

            valid_timestamps.append(now)
            return True, 0

    def reset(self):
        with self._lock:
            self._requests.clear()


rate_limiter = SlidingWindowRateLimiter()
