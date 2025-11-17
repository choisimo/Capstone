# mesh-aggregator

## 개요
- 목적: 감정-페르소나-경험-키워드 상호 연관 메쉬(노드/링크) 계산과 캐시 관리.
- 담당 범위: 필터/윈도우 기반 공동출현/연관성 지표 산출(PMI/NGMI/Jaccard) 및 축약.
- 운영 프로파일: `PLATFORM_PROFILE=gcp|linux-server`

## 인터페이스
- 내부 RPC/잡 트리거
  - `RebuildMesh(scope: global|article, window: {from,to,agg}, filters)` → `mesh_cache` upsert
  - `WarmupCaches(windows[])`
- REST: 없음(analysis-service가 읽기)
- 스키마: `analysis-service`의 `mesh_cache` 문서 구조 사용

## 데이터/스토리지
- 입력: MongoDB `documents`(태그/키워드), `articles`
- 출력: MongoDB `mesh_cache`
- 보관/TTL/인덱싱 정책: `mesh_cache.expires_at` TTL, `scope+window+filters_hash` 유니크 인덱스

## 알고리즘
- 노드: {emotion, persona, experience, keyword, source/channel(옵션)}
- 엣지 가중치: 동시 발생 카운트→PMI/NGMI 산출, 최소 지지도/리프트 필터
- 축약: 커뮤니티 감지(louvain, leiden 옵션), 상위 k 노드/엣지 선택
- 안정성: 샘플링 기반 추정(대량 데이터), 랩탑 환경 가속(PyTorch sparse/NumPy)

## 설정(ENV)
- 필수: `MONGO_URI`, `MONGO_DB`
- 선택: `MESH_CACHE_TTL_SEC`, `AGG_MIN_SUPPORT`, `MAX_NODES`, `MAX_LINKS`, `COMMUNITY_METHOD`

## 의존성
- 내부 서비스: ingest-worker, tagging-service, analysis-service
- 외부 서비스/OSS: MongoDB, networkx/igraph, numpy/scipy, OpenTelemetry

## 로컬 실행(예시)
- 주기적 빌드: `python jobs/mesh_rebuilder.py --window day --ttl 6h`

## 관측성
- Metrics: `mesh_build_latency_ms`, `edges_count`, `nodes_count`, `cache_hit`
- Traces: 집계 단계별 span(쿼리→공출→지표→축약→쓰기)
- Logs: 윈도우/필터/상한/커뮤니티 방식 요약

## 보안
- 인증/인가: 내부 네트워크 제한
- 비밀/키 관리: DB 크리덴셜 비밀관리

## SLO/성능
- 지연: 글로벌 메쉬 P95 < 2m(10M 문서 기준 배치)
- 증분: 변경량 기반 증분 갱신 옵션

## 운영/장애 대응
- 실패 시 이전 캐시 유지 서빙, 실패율 알람

## 통신 프로토콜 (Kafka/Pub/Sub)
- 기본 사용 안 함. 필요 시 리빌드 요청 이벤트 `ops.mesh.rebuild.v1` 도입 검토

## 백로그
- 2.5D 좌표 선계산/캐시, 레이아웃 안정화 메타 저장

## 실행 작업 매핑 (Execution Task Mapping)
메쉬 집계 파이프라인 작업 M1–M9.

핵심 매핑:
- M1 입력 스키마 정합성: documents/articles 필드 검증 & 인덱스 확인
- M2 필터 해시/키 정책: `scope+window+filters_hash` 유니크 (TTL 전략)
- M3 공출현 빈도 집계: 다단계 파이프라인(쿼리→카운트)
- M4 지표 산출 모듈: PMI/NGMI/Jaccard 전략 플러그
- M5 커뮤니티 탐지/축약: Louvain/Leiden + 상위 k 제한
- M6 증분 갱신(Incremental): 변경 문서 기반 부분 재계산
- M7 캐시 저장/TTL 관리: expires_at 관리 + 히트 메트릭
- M8 성능 최적화: Sparse 계산, 병렬/배치 튜닝
- M9 안정성/폴백: 실패 시 이전 캐시 서빙 + 알람

교차 의존성:
- Analysis(AN4–AN7), NLP 임베딩(N6), Tagging(T3), Ingest(IW4)
- 공통 X1–X3, X5, X7, X10

추적:
- PR 태그 `[M3][M4]` 등; 초기 기능 컷: M1–M5 + M7
- 증분(M6) 활성 후 목표: 전체 리빌드 대비 평균 60% 시간 절감
