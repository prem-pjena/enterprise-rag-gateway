from contextlib import asynccontextmanager

import asyncpg
from pgvector.asyncpg import register_vector

from core.config import settings


async def init(conn):
    await register_vector(conn)


@asynccontextmanager
async def lifespan(app):
    pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        init=init,
    )

    app.state.db_pool = pool

    try:
        yield
    finally:
        await pool.close()