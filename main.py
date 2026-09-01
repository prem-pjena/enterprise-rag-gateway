from fastapi import FastAPI, Request

from langfuse import get_client
from pydantic_ai import Agent

from core.lifespan import lifespan

from routers.health import router as health_router
from routers.search import router as search_router
from routers.ingest import router as ingest_router


langfuse = get_client()

if not langfuse.auth_check():
    raise RuntimeError("Langfuse authentication failed")

Agent.instrument_all()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def langfuse_middleware(
    request: Request,
    call_next,
):
    with langfuse.start_as_current_observation(
        name=f"{request.method} {request.url.path}",
        as_type="span",
    ):
        response = await call_next(request)

    langfuse.flush()

    return response


app.include_router(health_router)

app.include_router(search_router)

app.include_router(ingest_router)