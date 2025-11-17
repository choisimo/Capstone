# Linux 서버 배포·운영 부록

## 1. 대상
- 단일/소규모 VM 환경(Ubuntu 22.04+, 8vCPU/32GB+, SSD)에서 GCP-first 설계를 호환 운용.

## 2. 구성 맵핑
- Event Bus: Kafka/Redpanda 도커, 스키마 레지스트리(옵션)
- Warehouse: ClickHouse(파티션=날짜, 샤딩 불필요 시 단일 노드)
- Lake: MinIO 또는 로컬 파일시스템
- Vector DB: PostgreSQL + pgvector
- Serving: FastAPI + Uvicorn, Nginx Reverse Proxy, Certbot
- Scheduler: Airflow Docker Compose
- Monitoring: Prometheus+Grafana+Loki, OTel Collector

## 3. 배포 순서(Compose 예)
1) 네트워킹/포트: UFW 규칙 적용(80/443/9090/9093/3000/9000 등)
2) 도커 설치 및 compose 플러그인, 스왑 오프(선택)
3) `.env`에 `PLATFORM_PROFILE=linux-server` 등 변수 정의
4) `docker compose --profile linux-server up -d`
5) Nginx 리버스 프록시 설정(Cloud CDN 대체), TLS 자동화(certbot)

## 4. 운영 팁
- ClickHouse: TTL/Partition 관리, 머지쿼리 리밸런싱, 백업 `BACKUP TABLE`
- Kafka: 토픽 파라미터(retention.ms, segment.bytes) 조정, 메시지 키 균형화
- 자원: 차트 집계는 사전 다운샘플링, Redis 캐시 키는 필터 해시 사용
- 보안: OS 보안 업데이트 자동화, fail2ban, Docker daemon rootless(옵션)
