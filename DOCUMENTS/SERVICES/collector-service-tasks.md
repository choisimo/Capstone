# Collector Service Phased Plan (Draft)

Intended final location: `DOCUMENTS/DEVELOPMENT/collector-service-tasks.md`

## Overview
Goal: Reliably ingest heterogeneous external content (feeds, APIs, webhooks) into standardized raw event format with resilience, observability, and backpressure safety.

## Architecture Summary
Components: Source Adapter Interface, Fetch Scheduler, RateLimiter, Fingerprint/Dedup Pre-step, Output Dispatcher (Pub/Sub or Kafka topic), Metrics & Health Probe.

Data Flow: Source -> Adapter (normalize) -> Validation -> Fingerprint (hash) -> Emit RawEvent -> Queue -> Downstream (Dedup/Preprocess).

## Week-by-Week
### Week 1
- Spec ingestion schema (id, source_id, collected_at, payload, content_hash)
- Implement adapter interface contract (interface + registry)
- Build RSS adapter (baseline)
- Build REST polling adapter (configurable interval)
- Add basic validation (required fields, size limits)
- Implement content hash (SHA256 of normalized text)
- Emit to `raw_events` topic (placeholder stub if infra not ready)
- Metrics: ingest_count, ingest_errors labeled by source
- Health endpoint: /healthz (OK if adapter loop active)

### Week 2
- Add exponential backoff + jitter for transient failures
- Implement rate limiter per source (token bucket)
- Webhook adapter (HTTP endpoint) with signature verification placeholder
- Retry & poison queue (dead-letter topic) design & stub
- Structured logging (source, latency_ms, status)
- Secrets integration (API keys via env/secret manager abstraction)
- Source configuration loader (YAML or DB stub)
- Integration test: feed -> queue round trip

### Week 3
- Backfill job skeleton (historical ingestion) with time range parameters
- Adaptive scheduling (dynamic interval based on error/success ratio)
- Benchmark: sustained ingest at target eps
- Rate limit breach alert (metric threshold)
- Partial failure classification (network vs data)
- Config reload without restart

### Week 4
- Multi-tenant quotas (org-based rate allocation)
- Additional adapters (e.g., JSONLines bulk endpoint)
- Observability spans with trace IDs
- Performance tuning (goroutine / async batching)
- Stress test with 5x expected load

### Week 5+
- Regional failover design & doc
- Source UI integration contract (API spec for CRUD)
- Automated schema drift detection (payload diffing)
- Cost optimization review

## Task Inventory (Mapped to Detailed List)
C1-C13 represented; Weeks 1-2 cover C1-C8; Weeks 3-4 cover C9-C12; Week5+ covers C13.

## Non-Functional Requirements
- p95 ingestion latency < 2s (adapter fetch to enqueue)
- Error budget: <1% failed attempts per 24h (excluding remote 5xx)
- Zero data loss on single node failure (at-least-once semantics)

## Testing Strategy
- Unit: adapter normalization, hash function, rate limiter logic
- Integration: end-to-end ingest -> queue
- Load: soak test 1 hour at target eps
- Chaos: kill process mid-fetch, verify restart resilience

## Metrics & Alerts
- ingest_count (counter)
- ingest_errors (counter with reason label)
- ingest_latency_ms (histogram)
- rate_limited_events (counter)
- dlt_messages (counter)

Alerts:
- Error rate >2% (5m window)
- DLT messages > 10 in 10m
- Latency p95 > 2s sustained 15m

## Risks
- External API instability (mitigate retries + circuit logic)
- Payload schema drift (add logging + sample retention)
- Over-ingestion cost (quotas + adaptive intervals)

(END OF DRAFT)