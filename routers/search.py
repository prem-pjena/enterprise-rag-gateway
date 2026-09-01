from typing import Any
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from redis.asyncio import Redis

from core.config import settings
from providers.db import get_db_pool, hybrid_search
from services.embeddings import embed_query
from services.llm import stream_answer
from services.reranker import rerank_documents
from services.rate_limiter import rate_limit
from services.semantic_cache import SemanticCache


router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


def serialize_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    serialized = []

    for result in results:
        serialized.append(
            {
                key: value.item()
                if hasattr(value, "item")
                else value
                for key, value in result.items()
            }
        )

    return serialized


@router.post("/search")
async def search(
    request: Request,
    search_request: SearchRequest,
    tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> StreamingResponse:
    await rate_limit(
        request=request,
        tenant_id=str(tenant_id),
    )

    redis: Redis = request.app.state.redis

    cache = SemanticCache(
        redis=redis,
        ttl=settings.SEMANTIC_CACHE_TTL,
    )

    tenant = str(tenant_id)

    cached_answer = await cache.get(
        tenant_id=tenant,
        query=search_request.query,
    )

    if cached_answer is not None:

        async def cached_event_stream():
            yield f"data: {cached_answer}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            cached_event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Cache": "HIT",
            },
        )

    try:
        query_vector = await embed_query(
            search_request.query
        )

        results = await hybrid_search(
            pool=pool,
            query=search_request.query,
            tenant_id=tenant_id,
            query_vector=query_vector,
            limit=max(search_request.limit * 10, 50),
        )

        results = rerank_documents(
            query=search_request.query,
            documents=results,
            limit=search_request.limit,
        )

        context = "\n\n".join(
            result["content"]
            for result in results
        )

        answer_chunks: list[str] = []

        async def event_stream():
            try:
                async for answer in stream_answer(
                    context=context,
                    question=search_request.query,
                ):
                    answer_chunks.append(answer)
                    yield f"data: {answer}\n\n"

                final_answer = "".join(answer_chunks)

                await cache.set(
                    tenant_id=tenant,
                    query=search_request.query,
                    answer=final_answer,
                )

                yield "data: [DONE]\n\n"

            except Exception as exc:
                yield (
                    f"event: error\n"
                    f"data: {str(exc)}\n\n"
                )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Cache": "MISS",
            },
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Search failed",
        ) from exc