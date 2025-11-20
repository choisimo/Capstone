---
docsync: true
last_synced: 2025-09-30T09:16:00+0900
source_sha: a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6
coverage: 1.0
title: Collector Service Detailed PRD
version: 2.0
status: approved
---
# Collector Service 상세 PRD

## 문서 정보
- **서비스명**: Pension Sentiment Collector Service
- **버전**: 2.0
- **포트**: 8002
- **저장소**: `/BACKEND-COLLECTOR-SERVICE`
- **소유팀**: 데이터 수집팀

## 서비스 개요

### 목적
국민연금 관련 온라인 컨텐츠를 **웹 스크래핑 및 RSS 피드**를 통해 수집하고, 수집된 데이터의 품질을 검증하는 서비스입니다.

### 핵심 기능
1. **데이터 소스 관리**: 크롤링 대상 사이트 및 RSS 피드 등록/관리
2. **데이터 수집**: 웹 스크래핑 및 RSS 피드 파싱
3. **데이터 검증**: URL 유효성, 중복 제거, 품질 검사
4. **의존성 관리**: PostgreSQL, Redis, Analysis Service 연결 대기 및 재시도

### 실제 데이터 소스 (검증됨)
- 국민연금공단: https://www.nps.or.kr
- 보건복지부: https://www.mohw.go.kr
- 국민연금연구원: https://institute.nps.or.kr
- RSS 피드: nps.or.kr/jsppage/cyber_pr/news/rss.jsp
- 네이버/다음 뉴스 검색

---

## 아키텍처

### 서비스 구조
```
BACKEND-COLLECTOR-SERVICE/
├── app/
│   ├── main.py              # FastAPI 진입점 (의존성 대기 로직)
│   ├── config.py            # 설정
│   ├── db.py                # DB 연결
│   ├── schemas.py           # Pydantic 스키마
│   ├── routers/
│   │   ├── sources.py       # 데이터 소스 관리
│   │   ├── collections.py   # 수집 작업 관리
│   │   └── feeds.py         # RSS 피드 관리
│   └── services/
│       ├── source_service.py
│       ├── collection_service.py
│       └── feed_service.py
├── Dockerfile
└── requirements.txt
```

### 의존성 관리 (Startup Backoff)
```python
# 40회 재시도 (Exponential Backoff + Deterministic Jitter)
dependencies = {
  "PostgreSQL": 40 attempts,
  "Redis": 40 attempts,
  "Analysis Service": 40 attempts
}
```

**Backoff 전략**:
- Base: `min(8, 2^min(attempt, 5))` = 1s, 2s, 4s, 8s, 8s...
- Jitter: `(sum(ord(c) for c in seed) % 250) / 1000.0` (최대 0.249s)
- **결정론적**: random 사용 안 함

---

## API 명세

### 1. Data Sources API

#### POST `/sources/`
데이터 소스 생성

**Request**:
```json
{
  "name": "국민연금공단 공지사항",
  "url": "https://www.nps.or.kr/jsppage/info/notice/notice_01.jsp",
  "source_type": "web",
  "is_active": true,
  "crawl_interval": 3600,
  "selector": "div.notice-list"
}
```

**Response**:
```json
{
  "id": 1,
  "name": "국민연금공단 공지사항",
  "url": "https://www.nps.or.kr/jsppage/info/notice/notice_01.jsp",
  "source_type": "web",
  "is_active": true,
  "created_at": "2025-09-30T09:16:00+09:00"
}
```

#### GET `/sources/`
데이터 소스 목록 조회

**Query Params**:
- `skip`: 시작 위치 (기본 0)
- `limit`: 조회 개수 (기본 100)
- `active_only`: 활성화된 소스만 조회 (true/false)

**Response**:
```json
[
  {
    "id": 1,
    "name": "국민연금공단 공지사항",
    "url": "https://www.nps.or.kr/...",
    "source_type": "web",
    "is_active": true,
    "last_crawled_at": "2025-09-30T08:00:00+09:00"
  }
]
```

#### GET `/sources/{source_id}`
특정 데이터 소스 조회

#### PUT `/sources/{source_id}`
데이터 소스 업데이트

**Request**:
```json
{
  "is_active": false,
  "crawl_interval": 7200
}
```

#### DELETE `/sources/{source_id}`
데이터 소스 삭제

#### POST `/sources/{source_id}/test`
데이터 소스 연결 테스트

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "response_time_ms": 350,
  "message": "Source is reachable"
}
```

---

### 2. Collections API

#### POST `/collections/start`
수집 작업 시작

**Request**:
```json
{
  "source_ids": [1, 2, 3],
  "mode": "incremental"
}
```

**Mode 옵션**:
- `incremental`: 증분 수집 (신규 데이터만)
- `full`: 전체 재수집

**Response**:
```json
{
  "collection_id": "col-789",
  "status": "running",
  "source_count": 3,
  "started_at": "2025-09-30T09:16:00+09:00"
}
```

#### GET `/collections/{collection_id}`
수집 작업 상태 조회

**Response**:
```json
{
  "collection_id": "col-789",
  "status": "completed",
  "source_count": 3,
  "items_collected": 45,
  "items_validated": 43,
  "items_failed": 2,
  "started_at": "2025-09-30T09:00:00+09:00",
  "completed_at": "2025-09-30T09:15:00+09:00"
}
```

#### GET `/collections/`
수집 작업 목록 조회

**Query Params**:
- `status`: running/completed/failed
- `limit`: 조회 개수 (기본 20)

#### POST `/collections/{collection_id}/stop`
수집 작업 중단

---

### 3. RSS Feeds API

#### POST `/feeds/`
RSS 피드 등록

**Request**:
```json
{
  "name": "국민연금공단 뉴스 RSS",
  "url": "https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp",
  "is_active": true,
  "polling_interval": 1800
}
```

#### GET `/feeds/`
RSS 피드 목록 조회

#### POST `/feeds/{feed_id}/fetch`
RSS 피드 수동 가져오기

**Response**:
```json
{
  "feed_id": 1,
  "items_fetched": 15,
  "items_new": 3,
  "fetched_at": "2025-09-30T09:16:00+09:00"
}
```

---

### 4. Health & Readiness API

#### GET `/health`
헬스 체크

**Response**:
```json
{
  "status": "healthy",
  "service": "collector-service"
}
```

#### GET `/ready`
준비 상태 체크 (의존성 확인)

**Response**:
```json
{
  "ready": true,
  "dependencies": {
    "db": true,
    "redis": true,
    "analysis": true
  },
  "attempts": {
    "db": 2,
    "redis": 1,
    "analysis": 3
  }
}
```

**실패 시 (503 Service Unavailable)**:
```json
{
  "ready": false,
  "dependencies": {
    "db": true,
    "redis": true,
    "analysis": false
  },
  "attempts": {
    "db": 2,
    "redis": 1,
    "analysis": 40
  }
}
```

---

## 데이터 모델

### DataSource
```python
{
  "id": 1,
  "name": "국민연금공단 공지사항",
  "url": "https://www.nps.or.kr/...",
  "source_type": "web",  # web, rss
  "is_active": true,
  "crawl_interval": 3600,  # seconds
  "selector": "div.notice-list",
  "last_crawled_at": "2025-09-30T08:00:00+09:00",
  "created_at": "2025-09-20T10:00:00+09:00"
}
```

### Collection
```python
{
  "id": "col-789",
  "status": "completed",  # running, completed, failed
  "source_ids": [1, 2, 3],
  "mode": "incremental",
  "items_collected": 45,
  "items_validated": 43,
  "items_failed": 2,
  "started_at": "2025-09-30T09:00:00+09:00",
  "completed_at": "2025-09-30T09:15:00+09:00"
}
```

### CollectedItem
```python
{
  "id": "item-123",
  "source_id": 1,
  "collection_id": "col-789",
  "title": "국민연금 기금운용 실적 발표",
  "url": "https://www.nps.or.kr/...",
  "content": "전문 내용...",
  "author": "국민연금공단",
  "published_at": "2025-09-29T14:00:00+09:00",
  "collected_at": "2025-09-30T09:10:00+09:00",
  "is_valid": true
}
```

---

## 환경 변수

```bash
# 필수
DATABASE_URL=postgresql://user:pass@postgres:5432/collector_db
REDIS_URL=redis://redis:6379
ANALYSIS_SERVICE_URL=http://analysis-service:8001

# 서비스
PORT=8002
LOG_LEVEL=INFO

# 크롤링
USER_AGENT=Mozilla/5.0 (compatible; PensionCollector/1.0)
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# 검증
URL_VALIDATION_ENABLED=true
FORBIDDEN_PATTERNS=example.com,test.com,localhost,javascript:

# 성능
MAX_CONCURRENT_REQUESTS=10
BATCH_SIZE=50
```

---

## 데이터 검증

### URL 검증 규칙
```python
# 금지 패턴
FORBIDDEN = [
  "example.com",
  "test.com",
  "localhost",
  "javascript:",
  "mock",
  "fake"
]

# 허용된 도메인
ALLOWED_DOMAINS = [
  "nps.or.kr",
  "mohw.go.kr",
  "institute.nps.or.kr",
  "naver.com",
  "daum.net"
]
```

### 중복 제거
- URL 해시 기반 중복 체크
- Redis 캐싱으로 빠른 중복 확인

---

## 성능 목표

| 메트릭 | 목표 |
|--------|------|
| 크롤링 속도 | 100 페이지/분 |
| URL 검증 시간 | ≤ 50ms |
| 중복 체크 시간 | ≤ 10ms |
| RSS 파싱 시간 | ≤ 200ms |
| 의존성 대기 최대 | 10분 (40 attempts) |

---

## 수집 플로우

```mermaid
sequenceDiagram
    participant Admin
    participant Collector
    participant Web/RSS
    participant Validator
    participant DB
    
    Admin->>Collector: POST /collections/start
    Collector->>Web/RSS: Fetch content
    Web/RSS->>Collector: Return HTML/XML
    Collector->>Validator: Validate URL & content
    Validator->>Collector: Validation result
    Collector->>DB: Save valid items
    Collector->>Admin: Return collection status
```

---

## 테스트 전략

### 수용 기준
-  Mock 데이터 0건
-  금지 URL 패턴 차단
-  실제 소스 수집 성공률 ≥ 95%
-  중복 제거 정확도 100%
-  의존성 재시도 로직 정상 작동

---

## 관련 문서
- [Real Data Sources](../../data/REAL_DATA_SOURCES.md)
- [Crawler Implementation Guide](../../.windsurf/workflows/crawler-implementation-guide.md)
- [Production Stability Rules](../../.cursor/rules/production-stability.mdc)

---

**작성일**: 2025-09-30
**작성자**: Platform Team
**리뷰 상태**: Approved
