import asyncpg
from fastapi import Request


async def get_db_pool(request: Request) -> asyncpg.Pool:
    if not hasattr(request.app.state, "db_pool"):
        raise RuntimeError("Database pool is not initialized")

    return request.app.state.db_pool