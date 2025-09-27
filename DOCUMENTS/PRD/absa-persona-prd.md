---
제목: ABSA/Persona 서비스 PRD
버전: 1.0
작성일: 2025-09-26
소유팀: 데이터AI
last_synced_at: 2025-09-26T16:41:40+09:00
sync_status: updated
---

# 개요
속성 기반 감성 분석(ABSA)과 페르소나 분석/네트워크/트렌딩/신선도 관리/신원 링크 워크플로우를 제공합니다.

# 코드 기준
- 라우터: `BACKEND-ABSA-SERVICE/app/routers/personas.py`
- 분석: `BACKEND-ABSA-SERVICE/app/services/persona_analyzer.py`
- 모델: `BACKEND-ABSA-SERVICE/app/models.py`
- 보안: `BACKEND-ABSA-SERVICE/app/security.py`
- 설정: `BACKEND-ABSA-SERVICE/app/config.py`, `app/main.py`

# 데이터 모델(요약)
- `UserPersona(last_calculated_at, profile_data JSON)`
- `UserConnection(connection_strength, avg_sentiment, topics)`
- `Content`, `Comment`, `UserActivity`
- `ABSAAnalysis`, `TrendingTopic`
- `IdentityLinkRequest`, `IdentityAuditLog`

# API
- 분석 실행: `GET /api/v1/personas/{user_identifier}/analyze?platform=&depth=`
- 상세 조회(평탄화/신선도): `GET /api/v1/personas/{persona_id}/details`
- 네트워크: `GET /api/v1/personas/network/{user_id}`
- 트렌딩: `GET /api/v1/personas/trending?time_window=&limit=&sentiment_filter=`
- 활동 트래킹: `POST /api/v1/personas/{user_identifier}/track`
- 연결 업데이트: `POST /api/v1/personas/connections/update`
- 재계산(단건): `POST /api/v1/personas/recalculate/{persona_id}` (admin/analyst)
- 신원 링크 요청: `POST /api/v1/personas/identities/links/requests` (admin/analyst/user)
- 링크 승인/거절: `POST /api/v1/personas/identities/links/requests/{id}/approve|reject` (admin)

# 신선도 모델
- 기준: `last_calculated_at` + `PERSONA_STALENESS_HOURS_DEFAULT(기본 24h)`
- 최근 활동 발생 시 stale
- Details 응답에 `last_calculated_at`, `stale`, `staleness_reason` 노출

# 인증/인가(RBAC)
- 승인/거절: admin 전용, 요청 생성: admin/analyst/user
- 모든 변경 행위 감사 로그 기록 필수

# 비기능
- 분석 깊이/타임아웃, 캐시, 런타임 안전 마이그레이션(`last_calculated_at`)

# 모니터링/KPI
- stale 페르소나 수, 재계산 지연, 트렌딩/네트워크 응답 시간

# 테스트/수용 기준
- Details 평탄화/신선도 필드 정확
- RBAC 차단/허용 동작 정확
- 트렌딩 `recent_activity_count` 실제 집계값

## 시퀀스 다이어그램

### Persona Details 조회 + 신선도 계산
```mermaid
sequenceDiagram
  autonumber
  participant C as Client
  participant S as ABSA/Persona Service
  participant DB as PostgreSQL

  C->>S: GET /api/v1/personas/{persona_id}/details
  S->>DB: SELECT * FROM user_personas WHERE user_id = :persona_id
  DB-->>S: persona(row: last_calculated_at, profile_data, username)
  S->>DB: SELECT id FROM user_activities WHERE user_identifier=:username AND tracked_at>:last_calc LIMIT 1
  DB-->>S: maybe(row)
  S-->>C: 200 OK { flattened fields + last_calculated_at + stale + reason }
```

### Persona 재계산(단건)
```mermaid
sequenceDiagram
  autonumber
  participant C as Client(admin/analyst)
  participant S as ABSA/Persona Service
  participant DB as PostgreSQL

  C->>S: POST /api/v1/personas/recalculate/{persona_id}?platform=...
  S->>DB: SELECT * FROM user_personas WHERE user_id=:id
  alt found
    S->>S: Background task analyze_user_persona()
    S-->>C: 200 OK { scheduled }
  else not found
    S-->>C: 404 Not Found
  end
```

### Identity Link Request 생성/승인/거절(RBAC)
```mermaid
sequenceDiagram
  autonumber
  participant U as User/Analyst
  participant A as Admin
  participant S as ABSA/Persona Service
  participant DB as PostgreSQL

  U->>S: POST /personas/identities/links/requests {platform, identifier, evidence_*}
  S->>DB: INSERT INTO identity_link_requests (..., status=pending)
  S->>DB: INSERT INTO identity_audit_logs(action=link_request,...)
  S-->>U: 200 {request_id, status=pending}

  A->>S: POST /personas/identities/links/requests/{id}/approve
  S->>DB: UPDATE identity_link_requests SET status=approved, decided_at=NOW(), decided_by=:sub
  S->>DB: INSERT INTO identity_audit_logs(action=approve,...)
  S-->>A: 200 {status=approved}

  A->>S: POST /personas/identities/links/requests/{id}/reject
  S->>DB: UPDATE identity_link_requests SET status=rejected, decided_at=NOW(), decided_by=:sub
  S->>DB: INSERT INTO identity_audit_logs(action=reject,...)
  S-->>A: 200 {status=rejected}
```

## 상태도(State Diagrams)

### Persona Freshness
```mermaid
stateDiagram-v2
  [*] --> Fresh
  Fresh --> Stale: now - last_calculated_at > threshold
  Fresh --> Stale: new activity after last_calculated_at
  Stale --> Fresh: Recalculated
```

### IdentityLinkRequest Workflow
```mermaid
stateDiagram-v2
  [*] --> pending
  pending --> approved: Admin approve
  pending --> rejected: Admin reject
  approved --> [*]
  rejected --> [*]
```

## 메트릭 테이블

| Metric | Type | Labels | Description | Target/SLO |
|---|---|---|---|---|
| persona_details_latency_seconds | histogram | persona_id | 상세 조회 p95 | p95 ≤ 400ms |
| persona_trending_latency_seconds | histogram | time_window | 트렌딩 응답 p95 | p95 ≤ 500ms |
| persona_stale_total | gauge | | stale인 페르소나 수 | 감소 추세 |
| persona_recalc_duration_seconds | histogram | persona_id | 재계산 소요시간 | p95 ≤ 5s (샘플) |
| identity_link_requests_total | counter | action | 요청/승인/거절 이벤트 수 | n/a |
| identity_approval_tat_seconds | histogram | | 요청→승인 소요 | 하향 추세 |
