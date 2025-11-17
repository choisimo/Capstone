# event-analysis

## 개요
- 목적: ITS(Intervention Time Series) 기반 정책 이벤트 효과 추정 및 상관 분석.

## 인터페이스
- REST: `GET /v1/events/effect` (api-gateway 경유)
- 배치 잡: 이벤트 기준 윈도우 계산

## 데이터/스토리지
- 집계 테이블: 시계열 지표(긍/부/중/감정), 이벤트 메타

## 설정(ENV)
- `ITS_METHOD=bsts|cits`
- `WINDOW=[-7,+14]` 기본값

## 관측성
- Metrics: 계산시간, 신뢰구간 폭, 실패율

## 통신 프로토콜 (Kafka/Pub/Sub)
- 주 통신: REST 조회(`GET /v1/events/effect`), 배치 잡은 저장소에서 직접 읽기
- (옵션) 이벤트 발행: 분석 결과 요약 이벤트 `analytics.topic.v1` 또는 별도 `analytics.events.v1` 정의 가능
- 헤더 전달: `trace_id` 전파, 배치 잡은 run_id/trace_id 규칙 문서화

## 백로그
- 플라시보 테스트 자동화, 공변량 통제 옵션

## 실행 작업 매핑 (Execution Task Mapping)
이벤트 효과 추정 로드맵 EA1–EA9 매핑.

핵심 매핑:
- EA1 데이터 모델 스키마: 이벤트·시계열 집계 테이블 정의 ("데이터/스토리지")
- EA2 윈도우 추출 엔진: `WINDOW=[-7,+14]` 파라미터화 및 다중 이벤트 배치
- EA3 ITS 모델 플러그인: `ITS_METHOD=bsts|cits` 전략/팩토리
- EA4 신뢰구간 계산: 부트스트랩/Posterior 추정 및 폭 지표(Metrics 포함)
- EA5 효과 크기/지표 표준화: Δmean, relative %, cumulative, p-value
- EA6 품질/진단: 잔차 분석, 플라시보(백로그 항목 연결)
- EA7 결과 캐시/TTL: 동일 파라미터 재질의 최소화
- EA8 API 통합: `GET /v1/events/effect` 게이트웨이 확장 + AuthZ
- EA9 결과 이벤트 발행(옵션): `analytics.events.v1` 설계(스키마/활성 플래그)

교차 의존성:
- Gateway(G1–G5), Alert(AL3, AL5), Summarizer(R7 비용 모니터)
- 공통 X1–X3, X5(CI), X7(IaC), X10(비용)

추적:
- PR 태그 `[EA2][EA3]` 등; 초기 배포 기준 EA1–EA5 + EA8
- EA9 활성 조건: 외부 소비자가 2개 이상 + 안정화(오류율 <0.5%)
