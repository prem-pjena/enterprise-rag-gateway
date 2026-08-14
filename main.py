from fastapi import FastAPI

from core.lifespan import lifespan
from routers.health import router as health_router
from routers.search import router as search_router


app = FastAPI(lifespan=lifespan)


app.include_router(health_router)
app.include_router(search_router)