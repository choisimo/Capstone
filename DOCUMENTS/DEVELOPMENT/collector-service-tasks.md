---
docsync: true
last_synced: 2025-09-28T21:58:30+09:00
source_sha: af745df9851adc5c9bb20a05c6f65b6905f0ed33
coverage: 1.0
---

# Collector Service Phased Plan

## Overview
Goal: Reliably ingest heterogeneous external content (feeds, APIs, webhooks) into standardized raw event format with resilience, observability, and backpressure safety.

## Architecture Summary
Components: Source Adapter Interface, Fetch Scheduler, RateLimiter, Fingerprint/Dedup Pre-step, Output Dispatcher (Pub/Sub or Kafka topic), Metrics & Health Probe.

Data Flow: Source -> Adapter (normalize) -> Validation -> Fingerprint (hash) -> Emit RawEvent -> Queue -> Downstream (Dedup/Preprocess).

## Week-by-Week Execution
### Week 1 (Tasks C1-C3)
- Spec ingestion schema (id, source_id, collected_at, payload, content_hash)
- Implement adapter interface contract (interface + registry)
- Build RSS adapter (baseline)
- Build REST polling adapter (configurable interval)
- Add basic validation (required fields, size limits)
- Implement content hash (SHA256 of normalized text)
- Emit to `raw_events` topic (placeholder stub if infra not ready)
- Metrics: ingest_count, ingest_errors labeled by source
- Health endpoint: /healthz (OK if adapter loop active)

### Week 2 (Tasks C4-C8)
- Add exponential backoff + jitter for transient failures
- Implement rate limiter per source (token bucket)
- Webhook adapter (HTTP endpoint) with signature verification placeholder
- Retry & poison queue (dead-letter topic) design & stub
- Structured logging (source, latency_ms, status)
- Secrets integration (API keys via env/secret manager abstraction)
- Source configuration loader (YAML or DB stub)
- Integration test: feed -> queue round trip

### Week 3 (Tasks C9-C10)
- Backfill job skeleton (historical ingestion) with time range parameters
- Adaptive scheduling (dynamic interval based on error/success ratio)
- Benchmark: sustained ingest at target eps
- Rate limit breach alert (metric threshold)
- Partial failure classification (network vs data)
- Config reload without restart

### Week 4 (Tasks C11-C12)
- Multi-tenant quotas (org-based rate allocation)
- Additional adapters (e.g., JSONLines bulk endpoint)
- Observability spans with trace IDs
- Performance tuning (goroutine / async batching)
- Stress test with 5x expected load

### Week 5+ (Task C13)
- Regional failover design & doc
- Source UI integration contract (API spec for CRUD)
- Automated schema drift detection (payload diffing)
- Cost optimization review

## Task Master Alignment
- **C1**: Ingestion schema 정의 (`task-master` ID T-C1)
- **C2**: Adapter 인터페이스 구현 (ID T-C2)
- **C3**: RSS 어댑터 구축 (ID T-C3)
- **C4**: 백오프/지터 로직 추가 (ID T-C4)
- **C5**: Rate Limiter 구현 (ID T-C5)
- **C6**: Webhook 어댑터 초안 (ID T-C6)
- **C7**: Secret 연동/설정 로더 (ID T-C7)
- **C8**: 통합 테스트 파이프라인 (ID T-C8)
- **C9**: 백필 잡 스켈레톤 (ID T-C9)
- **C10**: 어댑터 스케줄 자동화 (ID T-C10)
- **C11**: 다중 테넌트 쿼터 모델 (ID T-C11)
- **C12**: Observability/Trace 확장 (ID T-C12)
- **C13**: 지역 Failover 및 비용 리뷰 (ID T-C13)

## Definition of Done / Non-Functional Requirements
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