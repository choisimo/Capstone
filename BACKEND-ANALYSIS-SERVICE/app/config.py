from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_db: str = Field(default="analysis", alias="MONGO_DB")

    vector_db_url: str | None = Field(default=None, alias="VECTOR_DB_URL")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    mesh_cache_ttl_sec: int = Field(default=21600, alias="MESH_CACHE_TTL_SEC")
    max_mesh_nodes: int = Field(default=500, alias="MAX_MESH_NODES")
    max_mesh_links: int = Field(default=5000, alias="MAX_MESH_LINKS")
    agg_min_support: int = Field(default=3, alias="AGG_MIN_SUPPORT")
    rag_max_tokens: int = Field(default=2048, alias="RAG_MAX_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()