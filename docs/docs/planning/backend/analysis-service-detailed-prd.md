---
docsync: true
last_synced: 2025-09-30T09:16:00+0900
source_sha: e8f4c21a9b45f88e9d3056c8a7e9f1a2b8c4d5e6
coverage: 1.0
title: Analysis Service Detailed PRD
version: 2.0
status: approved
---
# Analysis Service 상세 PRD

## 문서 정보
- **서비스명**: Analysis Service
- **버전**: 2.0
- **포트**: 8001
- **저장소**: `/BACKEND-ANALYSIS-SERVICE`
- **소유팀**: 데이터AI팀

## 서비스 개요

### 목적
국민연금 관련 컨텐츠에 대한 **기본 감성 분석, 트렌드 분석, 리포트 생성**을 제공하는 핵심 분석 마이크로서비스입니다.

### 핵심 기능
1. **감성 분석 (Sentiment Analysis)**: 텍스트의 긍정/부정/중립 분류
2. **트렌드 분석 (Trend Analysis)**: 시계열 감성 및 볼륨 트렌드 추적
3. **리포트 생성 (Report Generation)**: 자동화된 분석 리포트 생성
4. **ML 모델 관리**: 분석 모델 버전 관리

### ABSA Service와의 차이
- **Analysis Service**: 전체 텍스트 감성 분석 (단일 점수)
- **ABSA Service**: 속성별 감성 분석 (수익률, 안정성 등 개별 점수)

---

## 아키텍처

### 서비스 구조
```
BACKEND-ANALYSIS-SERVICE/
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── config.py            # 설정
│   ├── db.py                # DB 연결
│   ├── schemas.py           # Pydantic 스키마
│   ├── routers/
│   │   ├── sentiment.py     # 감성 분석 API
│   │   ├── trends.py        # 트렌드 분석 API
│   │   ├── reports.py       # 리포트 API
│   │   └── models.py        # ML 모델 관리 API
│   └── services/
│       ├── sentiment_service.py
│       ├── trend_service.py
│       └── report_service.py
├── Dockerfile
└── requirements.txt
```

### 의존성
- **Upstream**: Collector Service (데이터 수집)
- **Downstream**: API Gateway, ABSA Service, Frontend
- **Infrastructure**: PostgreSQL, Redis

---

## API 명세

### 1. Sentiment Analysis API

#### POST `/api/v1/sentiment/analyze`
단일 텍스트 감성 분석

**Request**:
```json
{
  "text": "국민연금 기금 운용 실적이 좋아졌습니다",
  "content_id": "content-123"
}
```

**Response**:
```json
{
  "content_id": "content-123",
  "text_preview": "국민연금 기금 운용...",
  "sentiment": {
    "label": "positive",
    "score": 0.75,
    "confidence": 0.88
  },
  "analyzed_at": "2025-09-30T09:16:00+09:00"
}
```

**감성 레이블**:
- `positive`: score > 0.3
- `neutral`: -0.3 ≤ score ≤ 0.3
- `negative`: score < -0.3

#### POST `/api/v1/sentiment/batch`
배치 감성 분석

**Request**:
```json
{
  "texts": [
    {"text": "텍스트 1", "content_id": "c1"},
    {"text": "텍스트 2", "content_id": "c2"}
  ]
}
```

**Response**:
```json
{
  "results": [...],
  "total_processed": 2,
  "success_count": 2,
  "error_count": 0,
  "processing_time_ms": 350
}
```

#### GET `/api/v1/sentiment/history/{content_id}`
감성 분석 히스토리 조회

**Query Params**:
- `limit`: 조회 개수 (기본 10)

**Response**:
```json
{
  "content_id": "content-123",
  "history": [
    {
      "analyzed_at": "2025-09-30T08:00:00+09:00",
      "sentiment": {"label": "positive", "score": 0.75}
    }
  ],
  "total": 5
}
```

#### GET `/api/v1/sentiment/stats`
감성 분석 통계

**Query Params**:
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Response**:
```json
{
  "period": {
    "start": "2025-09-01",
    "end": "2025-09-30"
  },
  "sentiment_distribution": {
    "positive": 450,
    "neutral": 320,
    "negative": 230
  },
  "percentages": {
    "positive": 45.0,
    "neutral": 32.0,
    "negative": 23.0
  },
  "avg_confidence": 0.82,
  "total_analyzed": 1000
}
```

---

### 2. Trend Analysis API

#### POST `/api/v1/trends/analyze`
트렌드 분석 수행

**Request**:
```json
{
  "period": "daily",
  "entity": "국민연금",
  "start_date": "2025-09-01",
  "end_date": "2025-09-30"
}
```

**Response**:
```json
{
  "entity": "국민연금",
  "period": "daily",
  "trends": [
    {
      "date": "2025-09-01",
      "sentiment_avg": 0.35,
      "volume": 150,
      "positive_count": 80,
      "neutral_count": 50,
      "negative_count": 20
    }
  ],
  "summary": {
    "sentiment_change": "+0.15",
    "volume_change": "+25%",
    "trending": "up"
  }
}
```

**Period 옵션**:
- `daily`: 일별 집계
- `weekly`: 주별 집계
- `monthly`: 월별 집계

#### GET `/api/v1/trends/entity/{entity}`
특정 엔티티 트렌드 조회

**Query Params**:
- `period`: daily/weekly/monthly (기본 weekly)
- `limit`: 조회 개수 (기본 30)

#### GET `/api/v1/trends/popular`
인기 트렌드 조회

**Query Params**:
- `period`: daily/weekly/monthly (기본 daily)
- `limit`: 조회 개수 (기본 10)

**Response**:
```json
{
  "popular_trends": [
    {
      "entity": "국민연금 개혁",
      "volume": 850,
      "sentiment_avg": -0.25,
      "change_rate": "+45%",
      "rank": 1
    }
  ]
}
```

#### GET `/api/v1/trends/keywords`
트렌딩 키워드 조회

**Query Params**:
- `period`: daily/weekly/monthly (기본 daily)
- `limit`: 조회 개수 (기본 20)

**Response**:
```json
{
  "keywords": [
    {
      "keyword": "기금운용",
      "frequency": 320,
      "sentiment_avg": 0.45,
      "trend": "rising"
    }
  ]
}
```

---

### 3. Report Generation API

#### POST `/api/v1/reports/generate`
리포트 생성

**Request**:
```json
{
  "report_type": "sentiment",
  "title": "9월 국민연금 감성 분석 리포트",
  "parameters": {
    "start_date": "2025-09-01",
    "end_date": "2025-09-30",
    "include_charts": true
  }
}
```

**Response**:
```json
{
  "report_id": 123,
  "title": "9월 국민연금 감성 분석 리포트",
  "report_type": "sentiment",
  "status": "completed",
  "generated_at": "2025-09-30T09:16:00+09:00",
  "download_url": "/api/v1/reports/123/download"
}
```

**Report Types**:
- `sentiment`: 감성 분석 리포트
- `trend`: 트렌드 분석 리포트
- `summary`: 종합 요약 리포트

#### GET `/api/v1/reports/`
리포트 목록 조회

**Query Params**:
- `report_type`: 타입 필터
- `limit`: 조회 개수 (기본 10)
- `offset`: 시작 위치 (기본 0)

**Response**:
```json
{
  "reports": [
    {
      "report_id": 123,
      "title": "리포트 제목",
      "report_type": "sentiment",
      "status": "completed",
      "generated_at": "2025-09-30T09:00:00+09:00"
    }
  ],
  "total": 45,
  "limit": 10,
  "offset": 0
}
```

#### GET `/api/v1/reports/{report_id}`
특정 리포트 조회

**Response**:
```json
{
  "report_id": 123,
  "title": "리포트 제목",
  "report_type": "sentiment",
  "status": "completed",
  "content": {
    "summary": "9월 한 달간 긍정적 의견이 45% 증가...",
    "sections": [...],
    "charts": [...]
  },
  "generated_at": "2025-09-30T09:00:00+09:00"
}
```

#### DELETE `/api/v1/reports/{report_id}`
리포트 삭제

**Response**:
```json
{
  "message": "Report deleted successfully"
}
```

#### GET `/api/v1/reports/{report_id}/download`
리포트 다운로드

**Query Params**:
- `format`: json/pdf/excel (기본 json)

**Response**: FileResponse (파일 다운로드)

---

### 4. ML Model Management API

#### GET `/api/v1/models/`
ML 모델 목록 조회

**Response**:
```json
{
  "models": [
    {
      "model_id": "sentiment-v2.1",
      "model_type": "sentiment_classifier",
      "version": "2.1",
      "accuracy": 0.87,
      "is_active": true,
      "created_at": "2025-09-15T10:00:00+09:00"
    }
  ]
}
```

#### POST `/api/v1/models/activate`
모델 활성화

**Request**:
```json
{
  "model_id": "sentiment-v2.1"
}
```

---

## 데이터 모델

### SentimentAnalysisResult
```python
{
  "id": "analysis-456",
  "content_id": "content-123",
  "text": "분석 대상 텍스트",
  "sentiment_label": "positive",
  "sentiment_score": 0.75,
  "confidence": 0.88,
  "analyzed_at": "2025-09-30T09:16:00+09:00"
}
```

### TrendData
```python
{
  "id": 789,
  "entity": "국민연금",
  "period": "daily",
  "date": "2025-09-30",
  "sentiment_avg": 0.35,
  "volume": 150,
  "positive_count": 80,
  "neutral_count": 50,
  "negative_count": 20
}
```

### Report
```python
{
  "id": 123,
  "title": "리포트 제목",
  "report_type": "sentiment",
  "status": "completed",
  "content": {...},
  "parameters": {...},
  "generated_at": "2025-09-30T09:00:00+09:00"
}
```

---

## 환경 변수

```bash
# 필수
DATABASE_URL=postgresql://user:pass@postgres:5432/analysis_db
REDIS_URL=redis://redis:6379

# 서비스
PORT=8001
LOG_LEVEL=INFO
DEBUG=false

# 보안
ALLOWED_HOSTS=["*"]

# ML 모델
MODEL_PATH=/app/models
DEFAULT_MODEL_VERSION=v2.1

# 성능
BATCH_SIZE=32
MAX_WORKERS=4
```

---

## 성능 목표

| 메트릭 | 목표 (p95) |
|--------|----------|
| 단일 감성 분석 | ≤ 150ms |
| 배치 분석 (10개) | ≤ 800ms |
| 트렌드 분석 | ≤ 1s |
| 리포트 생성 | ≤ 5s |
| 키워드 추출 | ≤ 500ms |

### 처리량
- 감성 분석: 100 req/s
- 트렌드 조회: 50 req/s
- 리포트 생성: 10 req/s

---

## 데이터 흐름

### 감성 분석 플로우
```mermaid
sequenceDiagram
    participant Client
    participant Analysis
    participant ML Model
    participant DB
    
    Client->>Analysis: POST /sentiment/analyze
    Analysis->>ML Model: Predict sentiment
    ML Model->>Analysis: Return score
    Analysis->>DB: Save result
    Analysis->>Client: Return analysis
```

---

## 테스트 전략

### 수용 기준
-  감성 분류 정확도 ≥ 85%
-  배치 처리 성공률 ≥ 99%
-  트렌드 계산 정확성 검증
-  리포트 생성 완료율 100%

---

## 관련 문서
- [ABSA Service PRD](absa-service-detailed-prd.md)
- [Collector Service PRD](collector-service-detailed-prd.md)

---

**작성일**: 2025-09-30
**작성자**: Platform Team
**리뷰 상태**: Approved
