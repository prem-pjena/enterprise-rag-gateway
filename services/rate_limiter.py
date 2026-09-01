from fastapi import HTTPException, Request
from redis.asyncio import Redis

from core.config import settings


TOKEN_BUCKET_SCRIPT = """
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])

local tokens = tonumber(redis.call("GET", KEYS[1]))
local last_refill = tonumber(redis.call("GET", KEYS[2]))

local time = redis.call("TIME")
local current_time = tonumber(time[1]) * 1000
    + tonumber(time[2]) / 1000

if tokens == nil then
    tokens = capacity
    last_refill = current_time
end

local elapsed = (current_time - last_refill) / 1000
local refill = elapsed * refill_rate

tokens = math.min(
    capacity,
    tokens + refill
)

last_refill = current_time

if tokens >= 1 then
    tokens = tokens - 1

    redis.call("SET", KEYS[1], tokens)
    redis.call("SET", KEYS[2], last_refill)

    return {1, 0}
end

redis.call("SET", KEYS[1], tokens)
redis.call("SET", KEYS[2], last_refill)

local retry_after = math.ceil((1 - tokens) / refill_rate)

return {0, retry_after}
"""


class TokenBucketRateLimiter:
    def __init__(
        self,
        redis: Redis,
        capacity: int,
        refill_rate: float,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        if refill_rate <= 0:
            raise ValueError("refill_rate must be greater than zero")

        self.redis = redis
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.script = redis.register_script(TOKEN_BUCKET_SCRIPT)

    async def allow(self, tenant_id: str) -> tuple[bool, int]:
        bucket_key = f"rate_limit:{tenant_id}:bucket"
        refill_key = f"rate_limit:{tenant_id}:last_refill"

        result = await self.script(
            keys=[bucket_key, refill_key],
            args=[
                self.capacity,
                self.refill_rate,
            ],
        )

        allowed = int(result[0]) == 1
        retry_after = int(result[1])

        return allowed, retry_after


async def rate_limit(request: Request, tenant_id: str) -> None:
    redis: Redis = request.app.state.redis

    limiter = TokenBucketRateLimiter(
        redis=redis,
        capacity=settings.RATE_LIMIT_CAPACITY,
        refill_rate=settings.RATE_LIMIT_REFILL_RATE,
    )

    allowed, retry_after = await limiter.allow(
        tenant_id=str(tenant_id),
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(max(retry_after, 1)),
            },
        )