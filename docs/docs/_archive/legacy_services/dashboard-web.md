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

## 실행 작업 매핑 (Execution Task Mapping)
프론트엔드 주요 기능을 W1–W11 (Dashboard Web 섹션) 및 교차 작업과 연결.

핵심 매핑:
- W1 인증 통합/세션: 로그인/토큰/리프레시 로직 (`GET /v1/sentiments` 보호)
- W2 레이아웃/테마: 글로벌 네비+다크모드 (Theme Toggle)
- W9 에러 바운더리: 예외 캡처 & 폴백 UI
- W3 실시간 업데이트: `GET /ws/alerts` + SSE/WS 커넥터 추상화
- W4 시각화 컴포넌트: sentiment/topic/aspect 차트 (차트 Lazy Load)
- W5 접근성 감사: WCAG 대비 개선
- W6 성능 예산: LCP, 번들 크기 측정 & 경보
- W8 피처 플래그 배선: 실험/롤아웃 토글
- W10 UI 테스트 하네스: E2E/통합 테스트 파이프라인
- W11 SSO 통합: OIDC/OAuth 플로우 확장

추가 백로그 매핑:
- 고대비 테마/사용자 설정: Phase 5
- 고급 필터/국제화: 패싯+i18n 스캐폴드

교차 의존성:
- G1–G5 Gateway 라우팅/권한 선행
- X1–X3 Observability (web vitals -> backend ingest)

추적:
- 컴포넌트/PR 네이밍: `[W3] Realtime connector` 등
