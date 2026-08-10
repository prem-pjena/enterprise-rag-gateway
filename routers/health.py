import asyncpg
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException

from core.config import settings
from providers.db import get_db_pool


router = APIRouter()


@router.get("/health")
async def health(
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, str]:
    try:
        async with pool.acquire() as connection:
            result = await connection.fetchval("SELECT 1")

        if result != 1:
            raise RuntimeError("Database health check failed")

        redis_client = redis.from_url(settings.REDIS_URL)

        try:
            redis_ok = await redis_client.ping()
        finally:
            await redis_client.aclose()

        if not redis_ok:
            raise RuntimeError("Redis health check failed")

        return {
            "status": "ok",
            "database": "ok",
            "redis": "ok",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Dependency health check failed",
        ) from exc