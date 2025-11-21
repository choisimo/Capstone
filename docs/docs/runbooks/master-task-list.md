# Master Task List (Draft in SERVICES)

Intended final location: `DOCUMENTS/DEVELOPMENT/master-task-list.md`
Move after review.

## Phase Overview
- Phase 0 (Weeks 1-2): Foundations (Collector, Dedup, NLP core, Gateway basics, Observability & CI)
- Phase 1 (Weeks 3-5): Core ML Services (Sentiment, Tagging baseline), Dashboard skeleton, Summarizer retrieval baseline
- Phase 2 (Weeks 6-9): Advanced ML (ABSA, Topic modeling, RAG improvements), Alerting, Mesh Aggregator
- Phase 3 (Weeks 10-12): Optimization, Governance, Scaling, UX polish

## Milestones
- M1: First end-to-end raw -> sentiment score in API (Week 2 end)
- M2: Dashboard displays real-time processed feed (Week 5)
- M3: ABSA + Topic insights available (Week 8)
- M4: Summaries + Alerts integrated (Week 10)
- M5: Hardening & Launch Readiness (Week 12)

## Priority Buckets
P0 = Must for initial launch, P1 = Strongly desired pre-launch, P2 = Post-launch improvement, P3 = Stretch

### P0 Tasks
Collector: C1–C7
Dedup: D1–D3,D7
NLP: N1–N7,N11
Sentiment: S1,S3
API Gateway: G1–G5,G7
Dashboard: W1,W2,W9
Ingest Worker: IW1–IW6
Observability/Security: X1–X8
Summarizer: R1–R4,R5
Event Analysis: EA1,EA6
Alert: AL1–AL5
Cross infra: X5 (CI), X7 (IaC)

### P1 Tasks
Sentiment: S2,S4,S5
ABSA: A1,A2,A7
Tagging: T1–T3
Topic: TM2,TM3,TM4
Summarizer: R6,R7,R8
Dashboard: W3–W6,W8,W10
API Gateway: G6
Event Analysis: EA2–EA5
Mesh: M1–M3
Security/ops: X9,X10

### P2 Tasks
Sentiment: S6–S8
ABSA: A3–A6,A8–A9,A10
Tagging: T4–T6
Topic: TM5–TM8
Summarizer: R9,R10
Alert: AL6–AL9
Mesh: M4–M8
Analysis Service: AN1–AN5
API: G8,G9
Dashboard: W7,W11
Ingest: IW7–IW9
Governance: D10, X6 (post adjustments) Cost: X10

### P3 Tasks
Sentiment: S9,S10
Tagging: T7
Mesh: M9
API: G10
Event Analysis: EA7–EA9
Exploration: R&D spikes beyond baseline

## Critical Path Detailing (Weeks 1-5)
Week 1: C1-C5, D1-D2, N1-N3, G1-G2, X1-X3, X5 scaffold
Week 2: C6-C7, D3,D7, N4,N6,N7,N11, S1,S3, G3-G5, W1 (skeleton), IW1-IW3
Week 3: W2,W9, IW4-IW6, R1-R3, S2,S4, Tagging T1-T2, TM2, A1,A2
Week 4: R4,R5, S5, Tagging T3, TM3-TM4, W3,W4 initial, G7, X7 infra refine
Week 5: Dashboard W5,W6,W8,W10, ABSA prototype A3, Topic TM5, Summarizer R6-R7, Mesh M1-M3

## KPI Definitions
- Data Throughput: events/sec ingest (target ≥ 200 eps initial)
- Processing Latency: raw -> sentiment score ≤ 5s p95
- Sentiment Model F1: ≥ 0.80 domain baseline
- Uptime (core pipeline): ≥ 99.0% pre-launch
- Duplicate Rate After Dedup: ≤ 2% residual duplicates sample
- Dashboard LCP: ≤ 2.5s
- Cost per 1k events: tracked weekly baseline

## Governance & Quality Gates
- Definition of Done includes: unit tests, metrics, tracing spans, config docs
- Security review before enabling external endpoints (G2/G3)
- Model version tag required (N10) before production use
- Performance regression threshold: >10% latency increase blocks merge

## Risk Register (Top 5)
1. Model performance insufficient (Mitigation: early labeling & baseline S1, fallback rules)
2. Vector store scaling risk (Mitigation: start with manageable PGVector; plan FAISS)
3. Cost overrun via large model inference (Mitigation: quantization & monitoring R8)
4. Ingestion instability from external sources (Mitigation: C2 modular adapters + circuit breakers)
5. Data privacy concerns (Mitigation: D4,D5 + audit logging X8)

## Staffing Assumptions (Illustrative)
- Platform Eng: Collector/Ingest/Gateway/Infra (2 FTE)
- ML Eng: Sentiment/ABSA/Topic/Summarizer (2 FTE)
- Fullstack: Dashboard + API integration (1-2 FTE)
- Data Analyst: Labeling, evaluation (0.5 FTE)

## Dependency Mapping Highlights
- Embeddings (N6) gate RAG retrieval (R3) and some topic tasks (TM6 if embedding-based)
- API Gateway stable auth/routing before Dashboard real-time (W3)
- Observability (X1-X3) must exist before scaling concurrency (IW1, M2)

## Post-Launch Focus (Phase 3)
- Advanced optimization (S8 latency, R9 long context)
- Governance & Explainability (S10, R6, R7)
- Scaling: Mesh adaptive load (M8), Multi-region (M9)
- User Experience polish (W7 offline, W11 SSO)

(END OF DRAFT)