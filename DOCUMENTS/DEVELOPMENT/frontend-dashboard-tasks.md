---
docsync: true
last_synced: 2025-09-28T21:58:45+09:00
source_sha: af745df9851adc5c9bb20a05c6f65b6905f0ed33
coverage: 1.0
---

# Frontend Dashboard Plan

## Objective
Deliver an interactive dashboard for exploring processed data (sentiment, topics, alerts) with real-time updates, strong performance, and accessibility.

## Architecture Snapshot
Stack: React (or Next.js), Component Library (MUI/Chakra or custom), State (Query library + lightweight global store), Real-time (WebSocket/SSE), Auth (JWT via Gateway), Theming (light/dark), Build (Vite/Next).

## Core Views
- Stream View (live feed of processed items)
- Insights Overview (sentiment distribution, top aspects/topics)
- Detail Drilldown (document or event timeline)
- Alerts Management (subscriptions, history)
- Settings (feature flags, API keys placeholder)

## Phase Breakdown
### Phase 1 (Weeks 1-2) Foundation — Tasks FD-1 ~ FD-6
- Repo scaffold & tooling (lint, format, test) (Week1)
- Auth integration (login flow, token refresh) (Week1-2)
- Global layout (nav, header, responsive grid) (Week1)
- Theme system (light/dark) + switch (Week1)
- Error boundary + fallback UI (Week2)
- Basic Stream View static mock (Week2)

### Phase 2 (Weeks 3-4) Data & Real-Time — Tasks FD-7 ~ FD-12
- API client abstraction (typed) (Week3)
- Real-time connection (SSE or WS) baseline (Week3)
- Live feed integration (virtualized list) (Week3-4)
- Insights placeholders (charts scaffolds) (Week4)
- Loading skeleton components (Week3)
- Access control wrappers (roles) (Week4)

### Phase 3 (Weeks 5-6) Visualization & UX — Tasks FD-13 ~ FD-18
- Sentiment trend chart (time series)
- Topic distribution chart
- Aspect heatmap/table
- Alert subscription UI (create/edit)
- Drilldown modal/page (document + metadata)
- Keyboard navigation & a11y audit fixes

### Phase 4 (Weeks 7-8) Performance & Hardening — Tasks FD-19 ~ FD-24
- Performance budget checks (LCP, CLS instrumentation)
- Code splitting & route-based chunks
- Prefetch strategies (hover/intention)
- Offline fallback (service worker minimal)
- SSO integration option
- UI test coverage expansion (critical flows)

### Phase 5 (Weeks 9-10) Polish & Enhancements — Tasks FD-25 ~ FD-30

## Task Master Alignment
- **FD-1**: Repo scaffold 및 툴링 구성 (`task-master` ID T-FD1)
- **FD-2**: 인증 플로우 구축 (ID T-FD2)
- **FD-3**: 글로벌 레이아웃/내비게이션 (ID T-FD3)
- **FD-4**: 테마 시스템/토글 (ID T-FD4)
- **FD-5**: 에러 바운더리 도입 (ID T-FD5)
- **FD-6**: 스트림 뷰 초기 목업 (ID T-FD6)
- **FD-7**: API 클라이언트 추상화 (ID T-FD7)
- **FD-8**: 실시간 연결 (ID T-FD8)
- **FD-9**: 라이브 피드 통합 (ID T-FD9)
- **FD-10**: 인사이트 차트 스캐폴드 (ID T-FD10)
- **FD-11**: 로딩 스켈레톤 (ID T-FD11)
- **FD-12**: 역할 기반 접근 제어 (ID T-FD12)
- **FD-13**: 감정 추세 시각화 (ID T-FD13)
- **FD-14**: 토픽 분포 차트 (ID T-FD14)
- **FD-15**: 속성 히트맵 (ID T-FD15)
- **FD-16**: 알림 구독 UI (ID T-FD16)
- **FD-17**: 드릴다운 모달 (ID T-FD17)
- **FD-18**: 접근성 개선/키보드 네비게이션 (ID T-FD18)
- **FD-19**: 성능 계측/웹 바이탈 (ID T-FD19)
- **FD-20**: 코드 스플리팅 전략 (ID T-FD20)
- **FD-21**: 프리페치 전략 (ID T-FD21)
- **FD-22**: 오프라인 모드 베이스라인 (ID T-FD22)
- **FD-23**: SSO 통합 준비 (ID T-FD23)
- **FD-24**: 고대비 테마 (ID T-FD24)
- **FD-25**: 사용자 환경설정 저장 (ID T-FD25)
- **FD-26**: 기능 플래그 패널 (ID T-FD26)
- **FD-27**: 고급 필터링 (ID T-FD27)
- **FD-28**: 국제화 스캐폴딩 (ID T-FD28)
- **FD-29**: QA 폴리시/테스트 (ID T-FD29)
- **FD-30**: 롤아웃 준비 및 피처 플래그 관리 (ID T-FD30)

## Definition of Done / Non-Functional Requirements
- LCP ≤ 2.5s on median hardware
- Lighthouse Performance ≥ 85 initial
- Accessible color contrast (WCAG AA)
- Real-time latency < 2s from backend event

## Testing Strategy
- Unit: pure components + utils
- Integration: API client hooks + mock server
- E2E: critical flows (login, view feed, set alert)
- Performance: Lighthouse CI in pipeline

## Metrics & Observability
- Web vitals (FID, LCP, CLS) -> analytics endpoint
- User interaction events (anonymized) for feature adoption
- Error boundary counts by feature area

## Security
- Token stored in memory (avoid localStorage if possible)
- CSP headers (script-src 'self') via Gateway config
- Input sanitization (dangerous HTML rendering avoided)

## Risks
- Real-time performance: mitigate with virtualization & batching
- Chart rendering overhead: lazy load heavy libs
- Auth complexity with expiring tokens: central refresh logic

(END OF DRAFT)