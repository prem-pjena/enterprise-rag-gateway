from typing import Any

from flashrank import Ranker, RerankRequest


ranker = Ranker(
    model_name="ms-marco-MiniLM-L-12-v2",
    cache_dir="/tmp",
)


def rerank_documents(
    query: str,
    documents: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    passages = [
        {
            "id": str(document["document_id"]),
            "text": document["content"],
        }
        for document in documents
    ]

    request = RerankRequest(
        query=query,
        passages=passages,
    )

    reranked = ranker.rerank(request)

    document_by_id = {
        str(document["document_id"]): document
        for document in documents
    }

    results = []

    for result in reranked[:limit]:
        document = document_by_id[str(result["id"])]

        results.append(
            {
                **document,
                "rerank_score": result["score"],
            }
        )

    return results