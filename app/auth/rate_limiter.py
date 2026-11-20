import time
from collections import defaultdict, deque
from fastapi import Depends, HTTPException, status
from app.auth.api_key_handler import verify_virtual_api_key
from app.repositories.models import ApiKey


class InMemoryRateLimiter:
    """ตัวจำกัดจำนวนครั้งการเรียกใช้งานต่อนาที (Sliding Window Rate Limiter)"""

    def __init__(self):
        # เก็บ Timestamp ของแต่ละ api_key_id: { key_id: deque([t1, t2, ...]) }
        self._requests: dict[int, deque[float]] = defaultdict(deque)

    def check_rate_limit(self, key_id: int, limit_per_minute: int) -> None:
        now = time.monotonic()
        window_start = now - 60.0
        timestamps = self._requests[key_id]

        # ลบประวัติการยิงที่เก่าเกิน 60 วินาทีออกจากคิว
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= limit_per_minute:
            retry_after = max(1, int(60 - (now - timestamps[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({limit_per_minute} requests/minute). Try again in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)


rate_limiter = InMemoryRateLimiter()


async def enforce_rate_limit(
    api_key: ApiKey = Depends(verify_virtual_api_key),
) -> ApiKey:
    """Dependency สำหรับตรวจสิทธิ์ API Key, ตรวจงบประมาณ (Budget) และเช็กโควต้า RPM"""
    # 1. ตรวจงบประมาณ (Budget Limit)
    if (
        api_key.max_budget_usd is not None
        and api_key.current_spend_usd >= api_key.max_budget_usd
    ):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Budget limit exceeded. "
                f"Current spend: ${api_key.current_spend_usd:.6f} / "
                f"Max budget: ${api_key.max_budget_usd:.6f}"
            ),
        )

    # 2. ตรวจความเร็วการยิง (Rate Limit RPM)
    limit = getattr(api_key, "rate_limit_per_minute", None)
    if limit and limit > 0:
        rate_limiter.check_rate_limit(key_id=api_key.id, limit_per_minute=limit)

    return api_key