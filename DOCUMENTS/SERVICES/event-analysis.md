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
