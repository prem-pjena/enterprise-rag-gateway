import asyncio

import asyncpg

from core.config import settings
from core.lifespan import init


async def test_vector():
    pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        init=init,
    )

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():

                # Create controlled 768-dimensional test vectors
                vector_a = [0.0] * 768
                vector_a[0] = 1.0

                vector_b = [0.0] * 768
                vector_b[1] = 1.0

                vector_c = [0.0] * 768
                vector_c[2] = 1.0

                # 1. Insert source
                source_id = await conn.fetchval(
                    """
                    INSERT INTO sources (file)
                    VALUES ($1)
                    RETURNING id
                    """,
                    "refund_policy.pdf",
                )

                # 2. Insert chunks and embeddings
                chunks = [
                    (
                        "Refunds are available within 30 days.",
                        vector_a,
                    ),
                    (
                        "Orders can be cancelled before shipment.",
                        vector_b,
                    ),
                    (
                        "Delivery addresses can be changed before dispatch.",
                        vector_c,
                    ),
                ]

                for content, embedding in chunks:
                    document_id = await conn.fetchval(
                        """
                        INSERT INTO documents (source_id, content)
                        VALUES ($1, $2)
                        RETURNING id
                        """,
                        source_id,
                        content,
                    )

                    await conn.execute(
                        """
                        INSERT INTO embeddings (document_id, embedding)
                        VALUES ($1, $2)
                        """,
                        document_id,
                        embedding,
                    )

                    print(
                        f"Inserted document_id={document_id}: {content}"
                    )

                print(f"source_id={source_id}")

                # 3. Dense retrieval
                query_vector = vector_a

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
                    LIMIT 5
                    """,
                    query_vector,
                )

                print("\nDense retrieval results:")

                for row in rows:
                    print(
                        f"document_id={row['document_id']}, "
                        f"distance={row['distance']:.4f}, "
                        f"content={row['content']}"
                    )

                # 4. Verify query execution plan
                plan = await conn.fetch(
                    """
                    EXPLAIN (ANALYZE, BUFFERS)
                    SELECT
                        e.document_id,
                        d.content,
                        e.embedding <=> $1 AS distance
                    FROM embeddings AS e
                    JOIN documents AS d
                        ON e.document_id = d.id
                    ORDER BY e.embedding <=> $1
                    LIMIT 5
                    """,
                    query_vector,
                )

                print("\nQuery plan:")

                for row in plan:
                    print(row[0])

    finally:
        await pool.close()


asyncio.run(test_vector())