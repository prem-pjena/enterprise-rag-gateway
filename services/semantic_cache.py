import hashlib

from redis.asyncio import Redis


class SemanticCache:
    def __init__(
        self,
        redis: Redis,
        ttl: int,
    ) -> None:
        self.redis = redis
        self.ttl = ttl

    def _make_key(
        self,
        tenant_id: str,
        query: str,
    ) -> str:
        raw_key = f"{tenant_id}:{query}"

        query_hash = hashlib.sha256(
            raw_key.encode("utf-8")
        ).hexdigest()

        return f"semantic_cache:{tenant_id}:{query_hash}"

    async def get(
        self,
        tenant_id: str,
        query: str,
    ) -> str | None:
        key = self._make_key(
            tenant_id=tenant_id,
            query=query,
        )

        return await self.redis.get(key)

    async def set(
        self,
        tenant_id: str,
        query: str,
        answer: str,
    ) -> None:
        key = self._make_key(
            tenant_id=tenant_id,
            query=query,
        )

        await self.redis.set(
            key,
            answer,
            ex=self.ttl,
        )

    async def invalidate_tenant(
        self,
        tenant_id: str,
    ) -> None:
        pattern = f"semantic_cache:{tenant_id}:*"

        keys: list[str] = []

        async for key in self.redis.scan_iter(
            match=pattern,
        ):
            keys.append(key)

        if keys:
            await self.redis.delete(*keys)