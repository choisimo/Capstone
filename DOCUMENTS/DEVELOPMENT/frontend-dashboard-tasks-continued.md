---
docsync: true
last_synced: 2025-09-28T21:59:05+09:00
source_sha: af745df9851adc5c9bb20a05c6f65b6905f0ed33
coverage: 1.0
---

# Frontend Dashboard Plan (Continued)

## Implementation Backlog (Sequenced)
1. Initialize repo + dependency baseline (Day 1)
2. Add lint/format/test scripts (Day 1)
3. Layout shell & navigation (Day 2)
4. Theme provider + dark mode toggle (Day 2)
5. Auth service (login -> token -> refresh) (Day 3)
6. Protected route guard (Day 3)
7. Error boundary + fallback component (Day 3)
8. Stream View mock (Day 4)
9. API client (fetch wrapper w/ retry) (Day 4)
10. Real-time connector (SSE/WS abstraction) (Day 5)
11. Virtualized feed list (Day 5)
12. Loading skeleton components (Day 5)
13. Insights chart scaffolds (Day 6)
14. Role-based access wrapper (Day 6)
15. Sentiment trend chart (Day 7)
16. Topic distribution chart (Day 7)
17. Aspect heatmap/table (Day 8)
18. Alert subscription CRUD UI (Day 9)
19. Drilldown modal/page (Day 9)
20. A11y audit & keyboard navigation improvements (Day 10)
21. Performance instrumentation (web vitals) (Day 11)
22. Code splitting configuration (Day 11)
23. Prefetch hover strategy (Day 12)
24. Offline service worker baseline (Day 12)
25. SSO option integration (Day 13)
26. High contrast theme (Day 13)
27. User preferences persistence (Day 14)
28. Feature flag experiment panel (Day 14)
29. Advanced filtering (facets & search) (Day 15)
30. i18n scaffolding (Day 15)
31. Final QA sweep + polish (Day 16)

## Component Inventory
- Layout: `AppLayout`, `SidebarNav`, `TopBar`
- Auth: `LoginForm`, `RequireAuth`
- Feed: `LiveFeedList`, `FeedItem`, `FeedFilters`
- Charts: `SentimentTrendChart`, `TopicDistributionChart`, `AspectHeatmap`
- Alerts: `AlertForm`, `AlertList`
- Drilldown: `ItemDetailsModal`
- Shared: `ErrorBoundary`, `Skeleton`, `ThemeToggle`, `FeatureFlagPanel`

## State Management
- React Query (data fetching caches)
- Lightweight global store (Zustand/Context) for auth, flags
- WebSocket events dispatch -> query invalidations

## Performance Techniques
- Virtualization (react-window or react-virtualized)
- Avoid large bundle chart libs until needed (dynamic import)
- Memoization of heavy components
- Debounced filter inputs

## Accessibility Checklist
- Semantic landmarks (main, nav, header)
- Focus management on modal open/close
- ARIA roles for dynamic lists
- Color contrast lint rule
- Keyboard navigation: all interactive elements tabbable

## Testing Breakdown
- Unit: components with logic branches (Auth, FeedItem)
- Integration: real-time event push updating list
- E2E: login -> view feed -> create alert -> see alert in list
- Performance: budget test script (LCP, bundle size)

## Metrics Events (Illustrative)
- `feed_item_clicked`
- `alert_created`
- `chart_tab_viewed`
- `feature_flag_toggled`

## Security & Privacy
- Sanitize any HTML fragments (DOMPurify if needed)
- Enforce HTTPS only cookies for fallback session
- Avoid storing PII in local metrics events

## Rollout Strategy
- Behind feature flag until MVP stable
- Gradual enablement per org/tenant
- Collect usage metrics for adoption dashboard

## Task Master Alignment (Backlog IDs)
- **FD-B1**: Repo 및 스크립트 기초화 (Backlog ID T-FD-B1)
- **FD-B2**: 레이아웃/내비게이션 (T-FD-B2)
- **FD-B4**: 실시간 스트림 구현 (T-FD-B4)
- **FD-B5**: 차트 컴포넌트 세트 (T-FD-B5)
- **FD-B6**: 접근성 & A11y QA (T-FD-B6)
- **FD-B7**: 성능 최적화 패스 (T-FD-B7)
- **FD-B8**: 보안/프라이버시 가이드 (T-FD-B8)
- **FD-B9**: 롤아웃/피처 플래그 전략 (T-FD-B9)

## Definition of Done (추가)
- Backlog 항목별 테스트 통과 증빙(Jest/E2E) 첨부
- Lighthouse CI ≥ 85, 접근성 감사 리포트 첨부