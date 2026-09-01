from contextlib import asynccontextmanager

import asyncpg
from langfuse import get_client
from pgvector.asyncpg import register_vector
from redis.asyncio import Redis

from core.config import settings


async def init(conn):
    await register_vector(conn)


@asynccontextmanager
async def lifespan(app):
    pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        init=init,
    )

    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    await redis.ping()

    app.state.db_pool = pool
    app.state.redis = redis

    try:
        yield
    finally:
        await pool.close()
        await redis.aclose()

        langfuse = get_client()
        langfuse.flush()