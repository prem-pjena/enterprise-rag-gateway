from uuid import UUID

import asyncpg

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request
from pydantic import BaseModel
from redis.asyncio import Redis

from core.config import settings
from providers.db import (
    create_child_with_embedding,
    create_parent,
    get_db_pool,
)
from services.chunker import (
    create_children,
    create_parents,
)
from services.embeddings import embed_text
from services.semantic_cache import SemanticCache


router = APIRouter()


class IngestRequest(BaseModel):
    source_id: int
    content: str


async def process_ingest(
    source_id: int,
    content: str,
    tenant_id: UUID,
    pool: asyncpg.Pool,
    redis: Redis,
) -> None:
    cache = SemanticCache(
        redis=redis,
        ttl=settings.SEMANTIC_CACHE_TTL,
    )

    await cache.invalidate_tenant(
        tenant_id=str(tenant_id),
    )

    parents = create_parents(
        content,
        parent_size=3000,
        parent_overlap=200,
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                SELECT set_config(
                    'app.current_tenant',
                    $1,
                    true
                )
                """,
                str(tenant_id),
            )

            for parent_content in parents:
                parent_id = await create_parent(
                    conn=conn,
                    tenant_id=tenant_id,
                    source_id=source_id,
                    content=parent_content,
                )

                children = create_children(
                    parent_content,
                    child_size=800,
                    child_overlap=100,
                )

                for child_content in children:
                    embedding = await embed_text(
                        child_content
                    )

                    await create_child_with_embedding(
                        conn=conn,
                        tenant_id=tenant_id,
                        source_id=source_id,
                        parent_id=parent_id,
                        content=child_content,
                        embedding=embedding,
                    )


@router.post("/ingest")
async def ingest(
    request: Request,
    ingest_request: IngestRequest,
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, str]:
    redis: Redis = request.app.state.redis

    background_tasks.add_task(
        process_ingest,
        ingest_request.source_id,
        ingest_request.content,
        tenant_id,
        pool,
        redis,
    )

    return {
        "status": "accepted",
        "tenant_id": str(tenant_id),
    }