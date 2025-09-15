# BACKEND-ANALYSIS-SERVICE

Analysis microservice for Pension Sentiment ("연금 나침반").

Provides:
- FastAPI endpoint stubs: /api/v1/mesh-data, /api/v1/articles, /api/v1/articles/{id}/mesh-data, /api/v1/documents, /api/v1/generate-report, /api/v1/chat (compat: /api/* deprecated)
- Pydantic schemas: articles, documents, mesh, report
- DB connectors (stubs): MongoDB, VectorDB
- Ingest worker: consumes raw.posts.v1 and writes to Mongo/Vector (stub)

Environment variables:
- MONGO_URI, MONGO_DB
- VECTOR_DB_URL
- GEMINI_API_KEY

Run dev:
- uvicorn app.main:app --reload --port 8010
- python workers/ingest_worker.py
