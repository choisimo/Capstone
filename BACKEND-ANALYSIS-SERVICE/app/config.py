from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    mongo_uri: str = Field(default="mongodb://localhost:27017", alias="MONGO_URI")
    mongo_db: str = Field(default="analysis", alias="MONGO_DB")

    vector_db_url: str | None = Field(default=None, alias="VECTOR_DB_URL")
    # Optional granular settings to build VECTOR_DB_URL when not provided
    vector_db_host: str = Field(default="localhost", alias="VECTOR_DB_HOST")
    vector_db_port: int = Field(default=5432, alias="VECTOR_DB_PORT")
    vector_db_user: str = Field(default="postgres", alias="VECTOR_DB_USER")
    vector_db_password: str = Field(default="postgres", alias="VECTOR_DB_PASSWORD")
    vector_db_database: str = Field(default="vectors", alias="VECTOR_DB_DATABASE")

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
    s = Settings()
    # Build vector DB URL if not explicitly set
    if not s.vector_db_url:
        s.vector_db_url = f"postgresql://{s.vector_db_user}:{s.vector_db_password}@{s.vector_db_host}:{s.vector_db_port}/{s.vector_db_database}"
    return s