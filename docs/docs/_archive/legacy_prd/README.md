---
docsync: true
last_synced: 2025-09-30T09:16:00+0900
title: PRD 문서 디렉토리 인덱스
version: 1.0
---
# PRD (Product Requirements Document) 디렉토리

## 개요
국민연금 감정분석 마이크로서비스 시스템의 모든 서비스에 대한 상세 PRD 문서입니다.

## 서비스별 상세 PRD (2025-09-30)

### 1. [ABSA Service 상세 PRD](absa-service-detailed-prd.md)
- **포트**: 8003
- **핵심 기능**: 속성 기반 감성 분석, 페르소나 분석, 네트워크 분석, RBAC 기반 신원 링크
- **주요 API**:
  - `POST /aspects/extract` - 속성 추출
  - `POST /analysis/analyze` - ABSA 분석
  - `GET /personas/{user}/analyze` - 페르소나 분석
  - `POST /identities/links/requests` - 신원 링크 요청

### 2. [Analysis Service 상세 PRD](analysis-service-detailed-prd.md)
- **포트**: 8001
- **핵심 기능**: 기본 감성 분석, 트렌드 분석, 리포트 생성, ML 모델 관리
- **주요 API**:
  - `POST /sentiment/analyze` - 감성 분석
  - `POST /trends/analyze` - 트렌드 분석
  - `POST /reports/generate` - 리포트 생성
  - `GET /keywords` - 트렌딩 키워드

### 3. [Collector Service 상세 PRD](collector-service-detailed-prd.md)
- **포트**: 8002
- **핵심 기능**: 웹 스크래핑, RSS 피드 수집, 데이터 검증, 의존성 관리
- **주요 API**:
  - `POST /sources/` - 데이터 소스 등록
  - `POST /collections/start` - 수집 작업 시작
  - `GET /ready` - 의존성 준비 상태 체크
- **특징**: Startup Backoff (40 attempts), Mock 데이터 감지

### 4. [Alert Service 상세 PRD](alert-service-detailed-prd.md)
- **포트**: 8004
- **핵심 기능**: 알림 규칙 관리, 다채널 통지 (Email, Slack, Webhook)
- **주요 API**:
  - `POST /rules/` - 알림 규칙 생성
  - `GET /notifications/` - 알림 히스토리
  - `POST /rules/{id}/test` - 규칙 테스트
- **Alert Types**: threshold, trend, keyword, anomaly

### 5. [API Gateway 상세 PRD](api-gateway-detailed-prd.md)
- **포트**: 8000
- **핵심 기능**: 단일 진입점, 요청 라우팅, 헬스 체크, CORS 처리
- **주요 API**:
  - `GET /health` - 전체 시스템 헬스 체크
  - `/api/v1/*` - 각 마이크로서비스 프록시
- **에러 처리**: 504 Timeout, 503 Service Unavailable

### 6. [OSINT Services 상세 PRD](osint-services-detailed-prd.md)
- **포트**: 8005 (Orchestrator), 8006 (Planning), 8007 (Source)
- **핵심 기능**: 작업 오케스트레이션, 수집 계획, 소스 관리
- **상태**: Draft (초기 구현 단계)
- **통합**: Collector Service와 협력

---

## 시스템 아키텍처

```
                    API Gateway (8000)
                           |
        +------------------+------------------+
        |                  |                  |
   Analysis (8001)   Collector (8002)    ABSA (8003)
        |                  |                  |
        +--------+---------+--------+---------+
                 |                  |
            Alert (8004)      OSINT Services
                              (8005/8006/8007)
```

---

## 서비스별 의존성

| 서비스 | Upstream | Downstream |
|--------|----------|------------|
| API Gateway | - | 모든 서비스 |
| Analysis | Collector | API Gateway, ABSA |
| Collector | PostgreSQL, Redis, Analysis | API Gateway |
| ABSA | Collector, Analysis | API Gateway, Frontend |
| Alert | Analysis | API Gateway |
| OSINT | Collector | - |

---

## 성능 요구사항 요약

| 서비스 | 주요 메트릭 | 목표 (p95) |
|--------|------------|-----------|
| ABSA | 속성 추출 | ≤ 200ms |
| ABSA | 페르소나 분석 | ≤ 5s |
| Analysis | 감성 분석 | ≤ 150ms |
| Analysis | 트렌드 분석 | ≤ 1s |
| Collector | 크롤링 속도 | 100 pages/min |
| Alert | 규칙 평가 | ≤ 100ms |
| Gateway | 프록시 오버헤드 | ≤ 10ms |

---

## 공통 보안 및 검증

### Mock 데이터 금지
모든 서비스에서 아래 패턴 금지:
```
example.com, test.com, localhost, javascript:,
mock, fake, test, dummy, sample, random
```

### 실제 데이터 소스
- 국민연금공단: https://www.nps.or.kr
- 보건복지부: https://www.mohw.go.kr
- 국민연금연구원: https://institute.nps.or.kr

### 인증
- RBAC: admin, analyst, user
- JWT 기반 토큰 검증 (일부 서비스)

---

## 관련 문서

### 아키텍처
- [시스템 아키텍처](../ARCHITECTURE/mas-architecture.md)
- [프론트엔드 통합 아키텍처](../ARCHITECTURE/frontend-integration.md)

### 개발 가이드
- [개발 가이드](../DEVELOPMENT/development-guide.md)
- [GCP 배포 런북](../DEVELOPMENT/gcp-deployment-runbook.md)

### 계약 및 규칙
- [API 및 이벤트 계약](../CONTRACTS/api-and-events.md)
- [Production Stability Rules](../../.cursor/rules/production-stability.mdc)
- [Documentation Rules](../../.cursor/rules/documentation-rules.mdc)

---

## 문서 동기화

모든 PRD 문서는 DocSync 워크플로우를 따릅니다:
- Front-matter에 `docsync: true` 설정
- `last_synced` 타임스탬프 관리
- 코드 변경 시 24시간 이내 문서 업데이트

---

## 기타 문서

### [전체 시스템 PRD](pensions-sentiment-prd.md)
- 시스템 전체 비전, 목표, 사용자 페르소나
- 핵심 기능 및 기술 스택
- 비기능 요구사항 및 제약사항

### 특화 문서
- [Identity Linking PRD](identity-linking-prd.md) - 교차 플랫폼 신원 연계
- [Persona Scheduler PRD](persona-scheduler-prd.md) - 페르소나 재계산 스케줄러
- [Frontend PRD](frontend-prd.md) - 대시보드 UI/UX
- [CI/CD Pipeline PRD](cicd-pipeline-prd.md) - 배포 파이프라인
- [Monitoring & Observability PRD](monitoring-observability-prd.md) - 관찰성

### 작업 관리
- **[미구현 기능 작업 배분](implementation-tasks.md)** ⭐ NEW
  - 실제 코드 리뷰 기반 미구현 기능 파악
  - 8개 주요 작업 정의 (우선순위별)
  - 4 Sprint 계획 (6주)
  - 팀별 작업 배분

---

**최종 업데이트**: 2025-09-30
**작성자**: Platform Team
**문서 커버리지**: 6/6 서비스 (100%)
**중복 제거 완료**: 2025-09-30
