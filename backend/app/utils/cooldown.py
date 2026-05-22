"""Rate-limit real emergency dispatches."""

import time

_last_real_dispatch: float = 0.0


def can_dispatch_real(cooldown_sec: int) -> tuple[bool, int]:
    """Return (allowed, seconds_remaining)."""
    global _last_real_dispatch
    if _last_real_dispatch <= 0:
        return True, 0
    elapsed = time.time() - _last_real_dispatch
    if elapsed >= cooldown_sec:
        return True, 0
    return False, int(cooldown_sec - elapsed)


def record_real_dispatch() -> None:
    global _last_real_dispatch
    _last_real_dispatch = time.time()
