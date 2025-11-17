---
docsync: true
last_synced: 2025-10-15T20:03:08+0900
source_sha: 733a9bd12e34e77d0e4054796389a7477c15b29d
coverage: 1.0
title: ABSA Service Detailed PRD
version: 2.0
status: approved
---
# ABSA Service 상세 PRD

## 문서 정보
- **서비스명**: Pension Sentiment ABSA Service
- **버전**: 2.0
- **포트**: 8003
- **저장소**: `/BACKEND-ABSA-SERVICE`
- **소유팀**: 데이터AI팀

## 서비스 개요

### 목적
국민연금 관련 컨텐츠에 대한 **속성 기반 감성 분석(ABSA)**을 제공하며, 사용자 페르소나 분석 및 네트워크 시각화를 통해 여론 형성 주체와 영향력을 추적합니다.

### 핵심 기능
1. **속성 추출 (Aspect Extraction)**: 수익률, 안정성, 관리비용 등 세부 속성 식별
2. **속성별 감성 분석 (ABSA)**: 각 속성에 대한 독립적인 감성 평가
3. **페르소나 분석**: 사용자 히스토리 기반 종합 프로필 생성
4. **네트워크 분석**: 사용자 간 연결 및 영향력 관계 파악
5. **신원 링크 관리**: RBAC 기반 교차 플랫폼 신원 연계
6. **트렌딩 분석**: 실시간 이슈 및 영향력 있는 페르소나 감지

---

## 아키텍처

### 서비스 구조
```
BACKEND-ABSA-SERVICE/
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── config.py            # 설정
│   ├── db.py                # DB 연결
│   ├── models.py            # 페르소나/신원 모델
│   ├── security.py          # RBAC
│   ├── routers/
│   │   ├── aspects.py       # 속성 추출 API
│   │   ├── analysis.py      # ABSA 분석 API
│   │   ├── models.py        # 모델 관리 API
│   │   └── personas.py      # 페르소나 API (26KB)
│   └── services/
│       ├── aspect_service.py
│       └── persona_analyzer.py
├── Dockerfile
└── requirements.txt
```

### 의존성
- **Upstream**: Collector Service, Analysis Service
- **Downstream**: API Gateway, Frontend Dashboard
- **Infrastructure**: PostgreSQL, Redis

---

## 핵심 데이터 모델

### 1. ABSAAnalysis (분석 결과)
```python
{
  "id": "analysis-456",
  "content_id": "content-123",
  "aspects": ["수익률", "안정성"],
  "aspect_sentiments": {
    "수익률": {
      "sentiment_score": 0.6,      # -1 ~ 1
      "sentiment_label": "positive",
      "confidence": 0.8             # 0.5 ~ 1.0
    }
  },
  "overall_sentiment": 0.05,
  "confidence_score": 0.775
}
```

### 2. UserPersona (페르소나)
```python
{
  "user_id": "user123",
  "platform": "reddit",
  "last_calculated_at": "2025-09-30T07:00:00+09:00",
  "profile_data": {
    "emotional_patterns": {
      "dominant_sentiment": "neutral",
      "sentiment_distribution": {"positive": 45, "neutral": 35, "negative": 20},
      "volatility": 0.3
    },
    "topics": ["국민연금", "기금운용"],
    "influence_score": 0.65,
    "activity_level": "active"
  }
}
```

### 3. UserConnection (네트워크)
```python
{
  "from_user_id": "user1",
  "to_user_id": "user2",
  "connection_strength": 0.7,
  "interaction_count": 15,
  "avg_sentiment": 0.5
}
```

---

## 주요 API 엔드포인트

### Aspect Extraction

#### POST `/aspects/extract`
텍스트에서 속성 추출

**Request**:
```json
{"text": "국민연금 수익률이 좋아졌지만 관리비용이 높다"}
```

**Response**:
```json
{
  "text": "국민연금 수익률이 좋아졌지만 관리비용이 높다",
  "aspects": [
    {"aspect": "수익률", "confidence": 0.85, "keywords_found": ["수익률"]},
    {"aspect": "관리비용", "confidence": 0.85, "keywords_found": ["관리비용"]}
  ],
  "total_aspects": 2,
  "model_version": "v1.0.0"
}
```

---

### ABSA Analysis

#### POST `/analysis/analyze`
속성별 감성 분석

**Request**:
```json
{
  "text": "수익률은 상승했으나 관리비용 증가가 우려된다",
  "aspects": ["수익률", "관리비용"]
}
```

**Response**:
```json
{
  "analysis_id": "c0f6b7b0-...",
  "content_id": "content-123",
  "text_preview": "수익률은 상승했으나 관리비용 증가가 우려된다",
  "aspects_analyzed": ["수익률", "관리비용"],
  "aspect_sentiments": {
    "수익률": {"sentiment_score": 0.6, "sentiment_label": "positive", "confidence": 0.8},
    "관리비용": {"sentiment_score": -0.5, "sentiment_label": "negative", "confidence": 0.75}
  },
  "overall_sentiment": {"score": 0.05, "label": "neutral"},
  "confidence": 0.775,
  "analyzed_at": "2025-10-15T11:00:00Z"
}
```

#### POST `/analysis/batch`
배치 분석 (여러 텍스트 동시 처리)

---

### Persona Analysis

#### GET `/api/v1/personas/{user_identifier}/analyze`
페르소나 분석

**Query Params**:
- `platform`: reddit, twitter, news_comment 등 [필수]
- `depth`: 분석할 게시물 수 (1~500, 기본 50)
- `force_refresh`: 캐시 무시 (기본 false)

**Response**:
```json
{
  "profile": {
    "emotional_patterns": {...},
    "topics": ["국민연금", "기금운용"],
    "language_style": {...},
    "influence_score": 0.65,
    "post_count": 50
  }
}
```

#### GET `/api/v1/personas/network/{user_id}`
사용자 네트워크 조회

**Response**:
```json
{
  "nodes": [
    {"id": "user1", "influence_score": 0.8, "dominant_sentiment": "positive"}
  ],
  "links": [
    {"source": "user1", "target": "user2", "strength": 0.7, "sentiment": 0.5}
  ]
}
```

#### GET `/api/v1/personas/trending`
트렌딩 페르소나 조회

**Query Params**:
- `time_window`: 24h, 7d, 30d (기본 24h)
- `limit`: 조회 개수 (기본 20)
- `sentiment_filter`: positive, negative, neutral

---

### Identity Link (RBAC)

#### POST `/api/v1/personas/identities/links/requests`
신원 링크 요청 생성 (admin/analyst/user)

**Request**:
```json
{
  "platform": "twitter",
  "identifier": "user_twitter_123",
  "evidence_type": "email_match"
}
```

#### POST `/api/v1/personas/identities/links/requests/{id}/approve`
신원 링크 승인 (admin only)

#### POST `/api/v1/personas/identities/links/requests/{id}/reject`
신원 링크 거절 (admin only)

---

## 인증 및 인가

### 역할별 권한

| 엔드포인트 | admin | analyst | user |
|-----------|-------|---------|------|
| 페르소나 분석 |  |  |  |
| 네트워크 조회 |  |  |  |
| 재계산 |  |  |  |
| 링크 요청 생성 |  |  |  |
| 링크 승인/거절 |  |  |  |

### 감사 로그
모든 신원 링크 작업은 `identity_audit_logs`에 기록

---

## 환경 변수

```bash
# 필수
DATABASE_URL=postgresql://user:pass@postgres:5432/pension_sentiment
REDIS_URL=redis://redis:6379
ANALYSIS_SERVICE_URL=http://analysis-service:8001

# 페르소나
PERSONA_STALENESS_HOURS_DEFAULT=24
PERSONA_MAX_DEPTH=500

# 인증
AUTH_REQUIRED=true
AUTH_JWT_SECRET=your-secret
AUTH_JWT_ALGORITHM=HS256

# 서비스
PORT=8003
LOG_LEVEL=INFO
```

---

## 성능 목표

| 메트릭 | 목표 (p95) |
|--------|----------|
| 속성 추출 | ≤ 200ms |
| ABSA 분석 | ≤ 500ms |
| 배치 분석 (10개) | ≤ 2s |
| 페르소나 분석 | ≤ 5s |
| 네트워크 조회 | ≤ 800ms |
| 트렌딩 조회 | ≤ 500ms |

### 처리량
- 단일 분석: 50 req/s
- 페르소나 분석: 5 req/s

---

## 테스트 전략

### 수용 기준
-  속성 추출 정확도 ≥ 85%
-  감성 분류 정확도 ≥ 80%
-  페르소나 신선도 체크 정상 작동
-  RBAC 권한 체크 통과
-  감사 로그 기록 완료

---

## 신선도(Freshness) 관리

### 기준
- `last_calculated_at` 기준 24시간 이내: Fresh
- 24시간 초과 OR 최근 활동 발생: Stale
- Details 응답에 `stale`, `staleness_reason` 포함

### 재계산 트리거
- 수동: POST `/personas/recalculate/{persona_id}` (admin/analyst)
- 자동: 스케줄러 (별도 구현 필요)

---

## 관련 문서
- [ABSA/Persona 서비스 PRD](absa-persona-prd.md)
- [Alert 서비스 PRD](alert-service-prd.md)
- [Production Stability Rules](../../.cursor/rules/production-stability.mdc)

---

**작성일**: 2025-09-30
**작성자**: Platform Team
**리뷰 상태**: Approved
