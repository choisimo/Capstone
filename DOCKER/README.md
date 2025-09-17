# Capstone Local Infra Stack (Docker Compose)

This brings up essential infra services for the MSA in containers:

- MongoDB (no auth, dev-only)
- Postgres with pgvector extension (vector DB)
- Redpanda (Kafka API compatible) + Console UI

## Quick start

1) Copy env example and (optionally) adjust Postgres credentials

```bash
cp DOCKER/.env.example DOCKER/.env
```

2) Start services

```bash
docker compose -f DOCKER/docker-compose.yml --env-file DOCKER/.env up -d
```

3) Configure your microservices to use these endpoints (host → containers):

- `MONGO_URI=mongodb://localhost:27017`
- `MONGO_DB=analysis`
- `VECTOR_DB_URL=postgresql://postgres:postgres@localhost:5432/vectors`
- `KAFKA_BROKERS=localhost:9092`
- `MESSAGE_BUS=kafka`

If you run services inside Docker on the same compose network, use:

- `MONGO_URI=mongodb://mongodb:27017`
- `VECTOR_DB_URL=postgresql://postgres:postgres@pgvector:5432/vectors`
- `KAFKA_BROKERS=redpanda:9092`

## Ports

- MongoDB: `localhost:27017`
- Postgres/pgvector: `localhost:5432`
- Redpanda (Kafka): `localhost:9092` (inside cluster), `localhost:19092` (host advertised)
- Redpanda Console: `http://localhost:8080`

## Integration notes

- `BACKEND-ANALYSIS-SERVICE` reads `.env` in its working directory via Pydantic. Create `BACKEND-ANALYSIS-SERVICE/.env` and copy values from above, or export them in your shell.
- `BACKEND-WEB-COLLECTOR` reads environment variables at runtime. Export `MESSAGE_BUS=kafka` and `KAFKA_BROKERS=localhost:9092` to publish events to Kafka.
- The `workers/ingest_worker.py` uses `MONGO_URI`, `MONGO_DB`, and Kafka envs; it will connect automatically when those are set.

## Postgres pgvector init

We mount `DOCKER/pgvector/init.sql` to enable the pgvector extension on first boot. Your application can now create tables with `vector` columns, e.g.

```sql
CREATE TABLE posts_embeddings (
  id TEXT PRIMARY KEY,
  embedding VECTOR(1536),
  meta JSONB
);
```

## Tear down

```bash
docker compose -f DOCKER/docker-compose.yml down
```

To also remove volumes/data:

```bash
docker compose -f DOCKER/docker-compose.yml down -v
```
