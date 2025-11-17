---
docsync: true
last_synced: 2025-09-30T09:16:00+0900
source_sha: c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1
coverage: 1.0
title: Alert Service Detailed PRD
version: 2.0
status: approved
---
# Alert Service 상세 PRD

## 문서 정보
- **서비스명**: Alert Service
- **버전**: 2.0
- **포트**: 8004
- **저장소**: `/BACKEND-ALERT-SERVICE`
- **소유팀**: Platform Team

## 서비스 개요

### 목적
국민연금 관련 **이상 감지 및 알림 발송**을 담당하는 서비스로, 규칙 기반 알림 및 다채널 통지를 제공합니다.

### 핵심 기능
1. **알림 규칙 관리**: 임계값 기반, 트렌드 기반, 키워드 기반 규칙 설정
2. **알림 발송**: 이메일, 슬랙, 웹훅, (SMS 준비중)
3. **알림 히스토리**: 발송 기록 조회 및 통계
4. **규칙 테스트**: 실제 데이터로 규칙 시뮬레이션

---

## 아키텍처

### 서비스 구조
```
BACKEND-ALERT-SERVICE/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── schemas.py
│   ├── routers/
│   │   ├── rules.py         # 알림 규칙 API
│   │   └── notifications.py # 알림 발송 API
│   └── services/
│       ├── rule_service.py
│       └── notification_service.py
├── Dockerfile
└── requirements.txt
```

### 알림 플로우
```
Data Change → Rule Evaluation → Alert Triggered → Notification Sent
     ↓              ↓                  ↓                ↓
  Analysis      Conditions        Alert Record      Email/Slack
```

---

## API 명세

### 1. Alert Rules API

#### POST `/api/v1/alerts/rules/`
알림 규칙 생성

**Request**:
```json
{
  "name": "부정 감성 급증 알림",
  "description": "부정 감성 비율이 50% 초과 시 알림",
  "alert_type": "threshold",
  "severity": "high",
  "conditions": {
    "metric": "negative_sentiment_ratio",
    "operator": ">",
    "threshold": 0.5
  },
  "notification_channels": ["email", "slack"],
  "recipients": {
    "email": ["admin@example.com"],
    "slack": ["#alerts"]
  },
  "is_active": true,
  "cooldown_minutes": 60
}
```

**Alert Types**:
- `threshold`: 임계값 기반 (sentiment_score, volume 등)
- `trend`: 트렌드 변화 감지 (급증/급락)
- `keyword`: 특정 키워드 출현
- `anomaly`: 이상치 감지

**Severity Levels**:
- `low`: 정보성
- `medium`: 주의
- `high`: 경고
- `critical`: 긴급

**Response**:
```json
{
  "id": 123,
  "name": "부정 감성 급증 알림",
  "alert_type": "threshold",
  "severity": "high",
  "is_active": true,
  "created_at": "2025-09-30T09:16:00+09:00"
}
```

#### GET `/api/v1/alerts/rules/`
알림 규칙 목록 조회

**Query Params**:
- `skip`: 시작 위치 (기본 0)
- `limit`: 조회 개수 (기본 100)
- `is_active`: true/false
- `alert_type`: threshold/trend/keyword/anomaly
- `severity`: low/medium/high/critical

**Response**:
```json
[
  {
    "id": 123,
    "name": "부정 감성 급증 알림",
    "alert_type": "threshold",
    "severity": "high",
    "is_active": true,
    "last_triggered_at": "2025-09-30T08:45:00+09:00"
  }
]
```

#### GET `/api/v1/alerts/rules/{rule_id}`
특정 규칙 상세 조회

#### PUT `/api/v1/alerts/rules/{rule_id}`
규칙 업데이트

**Request**:
```json
{
  "is_active": false,
  "cooldown_minutes": 120
}
```

#### DELETE `/api/v1/alerts/rules/{rule_id}`
규칙 삭제

#### POST `/api/v1/alerts/rules/{rule_id}/test`
규칙 테스트

**Request**:
```json
{
  "validation_data": {
    "negative_sentiment_ratio": 0.6,
    "volume": 150
  }
}
```

**Response**:
```json
{
  "rule_id": 123,
  "would_trigger": true,
  "matched_conditions": ["negative_sentiment_ratio > 0.5"],
  "simulated_alert": {
    "severity": "high",
    "message": "부정 감성 비율이 60%로 임계값 초과"
  }
}
```

---

### 2. Notifications API

#### GET `/api/v1/alerts/notifications/`
알림 히스토리 조회

**Query Params**:
- `skip`: 시작 위치 (기본 0)
- `limit`: 조회 개수 (기본 50)
- `rule_id`: 특정 규칙 필터
- `status`: sent/failed/pending
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Response**:
```json
{
  "notifications": [
    {
      "id": 456,
      "rule_id": 123,
      "rule_name": "부정 감성 급증 알림",
      "severity": "high",
      "message": "부정 감성 비율이 60%로 임계값 초과",
      "channels": ["email", "slack"],
      "status": "sent",
      "sent_at": "2025-09-30T08:45:00+09:00"
    }
  ],
  "total": 120,
  "skip": 0,
  "limit": 50
}
```

#### GET `/api/v1/alerts/notifications/{notification_id}`
특정 알림 상세 조회

**Response**:
```json
{
  "id": 456,
  "rule_id": 123,
  "severity": "high",
  "message": "부정 감성 비율이 60%로 임계값 초과",
  "channels": {
    "email": {
      "recipients": ["admin@example.com"],
      "status": "sent",
      "sent_at": "2025-09-30T08:45:00+09:00"
    },
    "slack": {
      "channels": ["#alerts"],
      "status": "sent",
      "sent_at": "2025-09-30T08:45:01+09:00"
    }
  },
  "triggered_at": "2025-09-30T08:45:00+09:00"
}
```

#### POST `/api/v1/alerts/notifications/{notification_id}/retry`
실패한 알림 재전송

---

### 3. Stats API

#### GET `/api/v1/alerts/stats`
알림 통계

**Query Params**:
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `group_by`: rule/severity/channel

**Response**:
```json
{
  "period": {
    "start": "2025-09-01",
    "end": "2025-09-30"
  },
  "total_alerts": 450,
  "by_severity": {
    "critical": 15,
    "high": 80,
    "medium": 200,
    "low": 155
  },
  "by_status": {
    "sent": 440,
    "failed": 10,
    "pending": 0
  },
  "top_rules": [
    {
      "rule_id": 123,
      "rule_name": "부정 감성 급증 알림",
      "trigger_count": 45
    }
  ]
}
```

---

## 데이터 모델

### AlertRule
```python
{
  "id": 123,
  "name": "부정 감성 급증 알림",
  "description": "...",
  "alert_type": "threshold",
  "severity": "high",
  "conditions": {...},
  "notification_channels": ["email", "slack"],
  "recipients": {...},
  "is_active": true,
  "cooldown_minutes": 60,
  "last_triggered_at": "2025-09-30T08:45:00+09:00",
  "created_at": "2025-09-20T10:00:00+09:00"
}
```

### Notification
```python
{
  "id": 456,
  "rule_id": 123,
  "severity": "high",
  "message": "알림 메시지",
  "channels": ["email", "slack"],
  "status": "sent",
  "triggered_at": "2025-09-30T08:45:00+09:00",
  "sent_at": "2025-09-30T08:45:01+09:00"
}
```

---

## 환경 변수

```bash
# 필수
DATABASE_URL=postgresql://user:pass@postgres:5432/alert_db
REDIS_URL=redis://redis:6379

# 서비스
PORT=8004
LOG_LEVEL=INFO

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=your-password
SMTP_FROM=alerts@example.com

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_BOT_TOKEN=xoxb-your-token

# SMS (준비중)
# SMS_API_KEY=your-api-key
# SMS_FROM=+821012345678

# Cooldown
DEFAULT_COOLDOWN_MINUTES=60
MAX_ALERTS_PER_HOUR=100
```

---

## Notification Channels

### Email (SMTP)
-  구현 완료
- 템플릿 기반 HTML 이메일
- 첨부 파일 지원

### Slack
-  구현 완료
- Webhook 및 Bot Token 지원
- Rich formatting (Blocks API)

### Webhook
-  구현 완료
- 커스텀 URL로 POST 요청
- JSON payload

### SMS
- ⏳ 준비중 (Placeholder 존재)
- Twilio/AWS SNS 통합 예정

---

## 성능 목표

| 메트릭 | 목표 |
|--------|------|
| 규칙 평가 시간 | ≤ 100ms |
| 알림 발송 시간 | ≤ 3s |
| 규칙 조회 | ≤ 50ms |
| 동시 알림 처리 | 100+ |

---

## 테스트 전략

### 수용 기준
-  규칙 조건 검증 정확성
-  이메일/슬랙 발송 성공률 ≥ 99%
-  Cooldown 로직 검증
-  규칙 테스트 시뮬레이션 정확성

---

## 관련 문서
- [Analysis Service PRD](analysis-service-detailed-prd.md)
- [Alert Service PRD (기존)](alert-service-prd.md)

---

**작성일**: 2025-09-30
**작성자**: Platform Team
**리뷰 상태**: Approved
