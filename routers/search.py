from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from providers.db import get_db_pool, hybrid_search
from services.embeddings import embed_query
from services.llm import generate_answer


router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("/search")
async def search(
    request: SearchRequest,
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, Any]:
    try:
        query_vector = await embed_query(request.query)

        results = await hybrid_search(
            pool=pool,
            query=request.query,
            query_vector=query_vector,
            limit=request.limit,
        )

        context = "\n\n".join(
            result["content"]
            for result in results
        )

        answer = await generate_answer(
            context=context,
            question=request.query,
        )

        return {
            "query": request.query,
            "answer": answer,
            "results": results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Search failed",
        ) from exc