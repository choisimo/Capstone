# 프론트엔드 통합 아키텍처

## 렌더링/배포 전략(GCP-first, Linux 호환)
- 프레임워크: Vite + React CSR 기반 대시보드(`FRONTEND-DASHBOARD`).
- GCP: Cloud Run 배포 + Cloud CDN/Global LB, IAP(옵션) 보호.
- Linux: docker-compose.spring.yml 기준 `frontend-dashboard` 컨테이너를 Reverse Proxy(Nginx 등) 뒤에서 제공.
- 라우팅: 클라이언트 사이드 라우팅(React Router), 대시보드 상호작용은 CSR.
- 에셋: CDN 캐싱, 차트 라이브러리 코드 스플리팅.

## 인증/인가
- OIDC(OAuth2) Authorization Code + PKCE.
- 토큰 저장: Access Token은 메모리, Refresh는 HttpOnly Secure SameSite=strict 쿠키.
- 역할 기반 라우트 가드(admin/analyst/comms/viewer).

## 데이터 접근 레이어
- 현재 구현: Spring Boot 기반 API Gateway(포트 8080)를 경유하며, 프론트엔드의 모든 `/api/v1/*` 호출은 게이트웨이로 통일.
- GCP: API Gateway/Cloud Run, (옵션) Cloud Endpoints.
- Linux: docker-compose.spring.yml의 `api-gateway` 서비스가 BFF 역할을 수행.
- 캐시: React Query/SWR 스타일 클라이언트 캐시 + HTTP 캐시 제어. 키=필터 파라미터 해시.
- 대용량 전송: 서버 페이지네이션 + 가상 스크롤, CSV는 비동기 생성 후 링크.

## 실시간
- Alerts: WebSocket(SockJS/Fallback), 지연/중복 방지 디바운스, 역추적 토큰(lastEventId)로 재동기화.
- 라이브 지표: 서버 Sentiment snapshot은 폴링(30–60s) 또는 SSE.

## 오류/회복력
- 전역 에러 경계, 지수 백오프 재시도, 사용자 친화적 오류코드 맵핑.
- 네트워크 오프라인 시 읽기 전용 캐시 사용, 온라인 시 동기화.

## 성능 최적화
- 차트 렌더링: 캔버스 기반(Chart.js/ECharts) + 데이터 다운샘플링/윈도우링.
- 메모리: 리스트 가상화, Suspense/Streaming SSR.
- 번들: Route-level code splitting, 분석/차트 별도 청크.

## 보안
- CSP, Subresource Integrity, iframe/worker 격리, 민감 데이터 마스킹.
- 로깅: PII 저장 금지, trace_id 헤더 전달.

## 관측성
- 프론트 텔레메트리: Web Vitals, 사용자 이벤트(analytics), error reporting(Sentry), 분산 추적 헤더(W3C Trace Context) → API에 전달.

## API 연동 매핑
- `/api/v1/sentiment/stats`: 대시보드·실시간 보드·Analytics의 전체 감성 통계.
- `/api/v1/trends/analyze`: 시계열 트렌드 분석(RealTimeDashboard, Explore, Analytics 그래프).
- `/api/v1/trends/popular`: 인기 이슈 목록(Dashboard 이슈 카드, Analytics 토픽 분석).
- `/api/v1/trends/keywords`: 키워드 랭킹 및 Mesh 그래프 기초 데이터.
- `/api/v1/alerts`, `/api/v1/alerts/rules`: 알림/규칙 목록 및 상태 변경(Alerts 페이지).
- `/api/v1/personas/network`, `/api/v1/personas/{id}/details`: 페르소나 네트워크 및 상세(PersonaNetwork 컴포넌트).

## 상태 관리
- 전역: auth, 필터, 즐겨찾기/저장 뷰(서버 동기화), 알림 카운터.
- 로컬: 각 위젯 상태(정렬, 페이지), UI 모달.

## 접근성/국제화
- i18n(ko/en), 키보드 네비게이션, 스크린리더 라벨, 색각보정 팔레트.

## 배포 파이프라인
- PR 미리보기(Preview), Storybook 시각회귀 테스트, Lighthouse 자동 측정.
- 환경 분리: dev/stage/prod, Feature Flag로 점진 릴리즈.
