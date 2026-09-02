Enterprise RAG Gateway

A production-oriented multi-tenant Retrieval-Augmented Generation (RAG) gateway built with FastAPI.

Architecture

Client
  |
  v
FastAPI
  |
  +--> Redis token-bucket rate limiter
  +--> NeMo Guardrails
  +--> Redis semantic cache
  +--> Gemini embeddings
  +--> PostgreSQL + pgvector HNSW
  |      +--> dense retrieval
  |      +--> PostgreSQL full-text search
  |      +--> RRF fusion
  |      +--> Row-Level Security
  +--> FlashRank reranking
  +--> pydantic-ai
  +--> LiteLLM primary/fallback routing
  +--> Langfuse observability
  |
  v
SSE response

Stack

FastAPI, asyncpg, PostgreSQL 16, pgvector, HNSW, PostgreSQL full-text search, RRF, Redis, LangChain, FlashRank, pydantic-ai, LiteLLM, NeMo Guardrails, Langfuse, Docker.

Security

Tenant isolation

Requests provide tenant identity through X-Tenant-ID. PostgreSQL Row-Level Security is enforced at the database layer using the app.current_tenant context.

A real API test confirmed that content ingested for tenant 00000000-0000-0000-0000-000000000001 was not retrievable by tenant 11111111-1111-1111-1111-111111111111.

NeMo Guardrails

The /search path checks prohibited cross-tenant data requests before normal retrieval/generation.

Blocked responses return:

X-Guardrail: BLOCKED
X-Cache: BYPASS

and a refusal message.

Rate limiting

Redis-backed Lua token bucket:

Capacity: 10
Refill rate: 2 tokens/second

A concurrent burst test produced both 200 and 429 responses, confirming enforcement.

API

Health

GET /health

curl -i http://localhost:8000/health

Example:

{"status":"ok","database":"ok","redis":"ok"}

Ingest

POST /ingest
X-Tenant-ID: <tenant UUID>

Body:

{
  "source_id": 1,
  "content": "Document content"
}

Ingestion is processed as a FastAPI background task and returns an accepted response.

Search

POST /search
X-Tenant-ID: <tenant UUID>

Body:

{
  "query": "What is the refund policy?",
  "limit": 5
}

The response is streamed using Server-Sent Events.

Local Development

Create .env from the example and populate the required credentials:

cp .env.example .env

Start the stack:

docker compose up -d --build

Check services:

docker compose ps

Check health:

curl -i http://localhost:8000/health

Stop:

docker compose down

Retrieval Pipeline

Query
  |
  v
Semantic cache
  |
  v
Gemini embedding
  |
  +----------------------+
  |                      |
  v                      v
Dense retrieval      Sparse retrieval
pgvector             PostgreSQL FTS
  |                      |
  +----------+-----------+
             |
             v
          RRF fusion
             |
             v
        FlashRank
             |
             v
       RAG generation
             |
             v
        SSE response

Model Routing

LiteLLM provides the model gateway with a configured Gemini primary and fallback route.

If the primary model fails, LiteLLM can route the request to the configured fallback model.

Caching

Redis provides:

semantic response caching

rate limiting

The semantic cache is tenant-aware and is invalidated during ingestion.

Performance Evidence

Measurements were taken against the running Dockerized implementation.

Hybrid / RRF retrieval

10 runs:

Minimum: 0.91 ms
Maximum: 1.84 ms
Average: 1.24 ms
Target: <200 ms
Result: PASS

FlashRank reranking

10 runs:

Minimum: 10.01 ms
Maximum: 25.61 ms
Average: 16.92 ms
Target: <50 ms
Result: PASS

These are component-level measurements, not end-to-end /search latency measurements.

Observability

Langfuse is integrated into the application request path.

A real /search request produced a Langfuse observation:

Name: POST /search
Trace ID: ec3d8db94077b5050454c90e7bf79d1a

The observation was successfully retrieved from the Langfuse API.

Verified Deployment-Gate Checks

/health with database and Redis health

/ingest

/search normal RAG flow

PostgreSQL tenant isolation

NeMo Guardrails refusal

Redis token-bucket rate limiting

LiteLLM primary/fallback routing

Semantic cache behavior

RRF performance

FlashRank performance

Langfuse request observation

Known Limitation

The current SSE implementation can emit the generated answer more than once before:

data: [DONE]

This has not been changed during the deployment-gate work.

Project Status

P1 — Enterprise RAG Gateway
Deployment Gate

Local functional, performance, and observability checks have passed.

Live deployment URL and Loom demonstration will be added after deployment.