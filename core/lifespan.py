from contextlib import asynccontextmanager

import asyncpg

from core.config import settings


@asynccontextmanager
async def lifespan(app):
    pool = await asyncpg.create_pool(settings.DATABASE_URL)

    app.state.db_pool = pool

    try:
        yield
    finally:
        await pool.close()