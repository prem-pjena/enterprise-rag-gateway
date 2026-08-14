from typing import Any

import asyncpg
from fastapi import Request


async def get_db_pool(request: Request) -> asyncpg.Pool:
    if not hasattr(request.app.state, "db_pool"):
        raise RuntimeError("Database pool is not initialized")

    return request.app.state.db_pool


async def dense_search(
    pool: asyncpg.Pool,
    query_vector: list[float],
    limit: int = 5,
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                e.document_id,
                d.content,
                e.embedding <=> $1 AS distance
            FROM embeddings AS e
            JOIN documents AS d
                ON e.document_id = d.id
            ORDER BY e.embedding <=> $1
            LIMIT $2
            """,
            query_vector,
            limit,
        )

    return [dict(row) for row in rows]

async def insert_embedding(
    pool: asyncpg.Pool,
    document_id: int,
    embedding: list[float],
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO embeddings (document_id, embedding)
            VALUES ($1, $2)
            """,
            document_id,
            embedding,
        )


async def sparse_search(
    pool: asyncpg.Pool,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id AS document_id,
                content,
                ts_rank(
                    search_vector,
                    plainto_tsquery('english', $1)
                ) AS score
            FROM documents
            WHERE search_vector @@ plainto_tsquery('english', $1)
            ORDER BY score DESC
            LIMIT $2
            """,
            query,
            limit,
        )

    return [dict(row) for row in rows]


async def hybrid_search(
    pool: asyncpg.Pool,
    query: str,
    query_vector: list[float],
    limit: int = 5,
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            WITH dense_results AS (
                SELECT
                    e.document_id,
                    ROW_NUMBER() OVER (
                        ORDER BY e.embedding <=> $1
                    ) AS rank_dense
                FROM embeddings AS e
                LIMIT $3
            ),
            sparse_results AS (
                SELECT
                    d.id AS document_id,
                    ROW_NUMBER() OVER (
                        ORDER BY ts_rank(
                            d.search_vector,
                            plainto_tsquery('english', $2)
                        ) DESC
                    ) AS rank_sparse
                FROM documents AS d
                WHERE d.search_vector @@ plainto_tsquery('english', $2)
                LIMIT $3
            ),
            combined AS (
                SELECT
                    COALESCE(dense_results.document_id, sparse_results.document_id)
                        AS document_id,
                    dense_results.rank_dense,
                    sparse_results.rank_sparse
                FROM dense_results
                FULL OUTER JOIN sparse_results
                    ON dense_results.document_id = sparse_results.document_id
            )
            SELECT
                c.document_id,
                d.content,
                (
                    CASE
                        WHEN c.rank_dense IS NOT NULL
                        THEN 1.0 / (60 + c.rank_dense)
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN c.rank_sparse IS NOT NULL
                        THEN 1.0 / (60 + c.rank_sparse)
                        ELSE 0
                    END
                ) AS rrf_score
            FROM combined AS c
            JOIN documents AS d
                ON d.id = c.document_id
            ORDER BY rrf_score DESC
            LIMIT $3
            """,
            query_vector,
            query,
            limit,
        )

    return [dict(row) for row in rows]