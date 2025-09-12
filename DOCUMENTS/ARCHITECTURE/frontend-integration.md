# 프론트엔드 통합 아키텍처

## 렌더링/배포 전략(GCP-first, Linux 호환)
- 프레임워크: Next.js(SSR+ISR 혼합) 또는 React CSR + Nginx. 권장: Next.js.
- GCP: Cloud Run 배포 + Cloud CDN/Global LB, IAP(옵션) 보호.
- Linux: Nginx Reverse Proxy + Docker Compose/K8s, certbot 자동 TLS.
- 라우팅: 앱 라우터, 페이지별 데이터 프리페치, ISR(홈/요약), CSR(대시보드 상호작용).
- 에셋: CDN 캐싱, 차트 라이브러리 코드 스플리팅.

## 인증/인가
- OIDC(OAuth2) Authorization Code + PKCE.
- 토큰 저장: Access Token은 메모리, Refresh는 HttpOnly Secure SameSite=strict 쿠키.
- 역할 기반 라우트 가드(admin/analyst/comms/viewer).

## 데이터 접근 레이어
- BFF(Backend-for-Frontend) 혹은 API Gateway 경유. 모든 호출은 게이트웨이 통일.
- GCP: API Gateway/Cloud Run, (옵션) Cloud Endpoints.
- Linux: Nginx + FastAPI BFF.
- 캐시: SWR/React Query + HTTP 캐시 제어 + Edge 캐시(ISR). 키=필터 파라미터 해시.
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
- `/v1/sentiments`: 대시보드 요약/시계열/히트맵 데이터 소스.
- `/v1/aspects`: ABSA 위젯 및 근거 스팬.
- `/v1/topics`: 토픽 목록/추이/용어.
- `/v1/summarize`: Explore 요약/논거. 프롬프트 파라미터 별 캐시 키 분리.
- `/v1/events/effect`: ITS 그래프/표.
- `/ws/alerts`: 실시간 알림 스트림.

## 상태 관리
- 전역: auth, 필터, 즐겨찾기/저장 뷰(서버 동기화), 알림 카운터.
- 로컬: 각 위젯 상태(정렬, 페이지), UI 모달.

## 접근성/국제화
- i18n(ko/en), 키보드 네비게이션, 스크린리더 라벨, 색각보정 팔레트.

## 배포 파이프라인
- PR 미리보기(Preview), Storybook 시각회귀 테스트, Lighthouse 자동 측정.
- 환경 분리: dev/stage/prod, Feature Flag로 점진 릴리즈.
