# dashboard-web

## 개요
- 목적: 분석 결과 시각화·조작 UI. React 기반.
- 위치: `FRONTEND-DASHBOARD/`

## 인터페이스
- 사용 API(게이트웨이 경유)
  - `GET /v1/sentiments`
  - `GET /v1/aspects`
  - `GET /v1/topics`
  - `POST /v1/summarize`
  - `GET /v1/events/effect`
  - `GET /ws/alerts`

## 설정
- `.env` 예시
  - `VITE_API_BASE_URL=http://localhost:8081`
  - `VITE_WS_BASE_URL=ws://localhost:8081`

## 데이터/상태
- React Query 캐시, 위젯 파라미터=캐시 키

## 관측성
- Web Vitals, Sentry(옵션), 분산 추적 헤더 전달

## 백로그
- Mock 제거 및 실제 API 연동, SSE/WS 알림 배지, i18n/권한 가드
