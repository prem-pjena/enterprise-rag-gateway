from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    GOOGLE_API_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    RATE_LIMIT_CAPACITY: int = 10
    RATE_LIMIT_REFILL_RATE: float = 2.0

    SEMANTIC_CACHE_TTL: int = 3600


settings = Settings()