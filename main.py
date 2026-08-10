from fastapi import FastAPI
from core.lifespan import lifespan
from routers.health import router


app = FastAPI(lifespan=lifespan)

app.include_router(router)
