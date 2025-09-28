---
docsync: true
last_synced: 2025-09-28T21:59:22+09:00
source_sha: af745df9851adc5c9bb20a05c6f65b6905f0ed33
coverage: 1.0
---

# Sentiment Service Plan

## Objective
Provide low-latency sentiment classification for ingested text (document-level) with versioned models, monitoring, and gradual optimization.

## Architecture Snapshot
Components: Inference API (REST + batch), Model Loader (versioned), Preprocessor (lightweight adaptation), Confidence Calibrator, Metrics/Tracing, Drift Monitor.

Request Flow: Text -> Preprocess (tokenize, truncate) -> Model Inference -> Score Post-process (softmax, calibration) -> Response {sentiment_label, confidence, model_version}.

## Phases
### Phase 1 (Week 1-2): Baseline — Tasks S1, S3
- Select base model (DistilBERT or similar) (S1)
- Prepare evaluation dataset (subset of domain texts)
- Implement inference microservice (FastAPI/Go) (S3)
- Add health & readiness endpoints
- Add basic latency metrics & request counters
- Deploy baseline model v1.0 (container) to staging
- Create evaluation script: accuracy, macro F1, confusion matrix

### Phase 2 (Week 3-4): Quality & Calibration — Tasks S2, S4, S5
- Collect misclassifications sample for review
- Fine-tuning pipeline setup (S2) with reproducible config
- Add confidence scoring & Platt scaling or temperature scaling (S4)
- Introduce model registry metadata (version, date, dataset hash)
- Implement canary evaluation job (staging traffic shadow)
- Add p95 latency dashboard, model load time metric

### Phase 3 (Week 5-6): Monitoring & Resilience — Tasks S5, S6, S7
- Drift detection (S5): compare rolling window F1 vs baseline
- A/B model routing feature flag (S6 groundwork)
- Auto rollback on quality degradation threshold
- Batch inference endpoint (up to N texts) with rate limiting
- Caching layer (optional) for repeated short texts
- Structured error classes (validation vs system)

### Phase 4 (Week 7-8): Optimization & Governance — Tasks S8, S9, S10
- Quantization or ONNX export test (S8)
- Memory footprint and throughput benchmark under load
- Bias audit pass (S9) with demographic subset evaluation
- Explainability prototype (token saliency heatmap) (S10)
- Automatic reprocess pipeline hook (S7) for re-scoring historical records when promoting model

## Task Master Alignment
- **S1**: 모델 선정/데이터셋 준비 (`task-master` ID T-S1)
- **S2**: 파이프라인 파인튜닝 구성 (ID T-S2)
- **S3**: 추론 마이크로서비스 구현 (ID T-S3)
- **S4**: 신뢰도 보정(Platt/Temperature) (ID T-S4)
- **S5**: Drift 모니터링 및 메트릭 (ID T-S5)
- **S6**: A/B 모델 라우팅 준비 (ID T-S6)
- **S7**: 배치 재처리 파이프라인 (ID T-S7)
- **S8**: 최적화/양자화 실험 (ID T-S8)
- **S9**: 편향 감사 및 리포트 (ID T-S9)
- **S10**: 설명가능성 프로토타입 (ID T-S10)

## Definition of Done / Non-Functional Requirements
- p95 single inference latency ≤ 150ms (CPU baseline) target; stretch 80ms with optimization
- Availability ≥ 99% (excluding maintenance windows)
- Warm start time < 5s after deploy

## Testing Strategy
- Unit: preprocessing normalization, calibration math
- Integration: end-to-end inference, batch endpoint
- Performance: load test at expected QPS (determine during Phase2)
- Regression: model evaluation script gating promotion

## Metrics
- inference_requests_total (counter)
- inference_latency_ms (histogram)
- model_version_info (gauge with version labels)
- drift_score (gauge) & drift_alert (counter)
- error_rate (counter / total)

Alerts
- Latency p95 > objective for 10m
- Drift score exceeds threshold
- Error rate >2% (excluding client 4xx)
## Risks & Mitigations
- Model underperforms domain nuance: schedule early fine-tune (Phase2)
- Latency regression with larger model: quantization fallback
- Drift due to topic shifts: rolling evaluation (S5)
- Bias concerns: early audit (S9)