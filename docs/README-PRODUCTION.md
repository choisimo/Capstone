---
docsync: true
last_synced: 2025-09-30T01:41:06+0000
source_sha: 6e9c96accdc46e88c87c4fe11f49aa2efddb98d8
coverage: 1.0
---
# 🚀 프로덕션 배포 가이드

## 📋 개요

국민연금 감정분석 시스템을 **단일 명령**으로 프로덕션 환경에 배포할 수 있습니다.
모든 서비스, 데이터베이스, 모니터링이 자동으로 설정됩니다.

## ⚡ 빠른 시작

```bash
# 전체 시스템 시작 (1줄 명령)
./production-start.sh

# 모니터링 포함 시작
./production-start.sh --with-monitoring

# 클린 시작 (볼륨 초기화)
./production-start.sh --clean --with-monitoring
```

## 📦 포함 구성요소

### 핵심 서비스
- ✅ API Gateway (포트 8000)
- ✅ Analysis Service (포트 8001)
- ✅ Collector Service (포트 8002)
- ✅ ABSA Service (포트 8003)
- ✅ Alert Service (포트 8004)

### OSINT 서비스
- ✅ OSINT Orchestrator (포트 8005)
- ✅ OSINT Planning (포트 8006)
- ✅ OSINT Source (포트 8007)

### 인프라
- ✅ PostgreSQL with pgvector
- ✅ Redis
- ✅ MongoDB

### 프론트엔드
- ✅ React Dashboard (포트 3000)

### 모니터링 (선택)
- ✅ Prometheus (포트 9090)
- ✅ Grafana (포트 3001)

## 🔧 자동 설정 내용

### 1. 데이터베이스 초기화
- PostgreSQL: 테이블 생성, 인덱스, 기본 데이터
- MongoDB: 컬렉션 생성, 인덱스, 소스 메타데이터
- Redis: 자동 설정 완료

### 2. 헬스체크
- 모든 서비스에 `/health` 엔드포인트
- Docker 헬스체크 자동 실행
- 재시작 정책 적용

### 3. 네트워크
- 격리된 Docker 네트워크
- 서비스 간 내부 통신
- 외부 접근은 API Gateway 통해서만

### 4. 보안
- 강력한 기본 비밀번호
- JWT 인증 준비
- CORS 설정

### 5. 리소스 관리
- CPU/메모리 제한 설정
- 로그 로테이션
- 볼륨 영속성

## 🌐 접속 정보

| 서비스 | URL | 인증 정보 |
|--------|-----|----------|
| **Frontend** | http://localhost:3000 | - |
| **API Gateway** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3001 | admin / Gr@fana2025 |
| **Prometheus** | http://localhost:9090 | - |

## 📝 환경 설정

### 기본 설정 변경
`.env.production` 파일을 수정하여 설정을 변경할 수 있습니다.

```bash
# 예: 포트 변경
GATEWAY_PORT=8080
FRONTEND_PORT=3001

# 예: 비밀번호 변경  
POSTGRES_PASSWORD=MyNewPassword
JWT_SECRET_KEY=MySecretKey
```

## 🔍 서비스 관리

### 상태 확인
```bash
# 전체 상태
docker-compose -f docker-compose.production.yml ps

# 헬스체크
./check-health.sh
```

### 로그 확인
```bash
# 특정 서비스 로그
docker-compose -f docker-compose.production.yml logs -f api-gateway

# 전체 로그
docker-compose -f docker-compose.production.yml logs -f
```

### 서비스 재시작
```bash
# 특정 서비스
docker-compose -f docker-compose.production.yml restart api-gateway

# 전체 재시작
docker-compose -f docker-compose.production.yml restart
```

### 중지 및 제거
```bash
# 중지 (데이터 유지)
docker-compose -f docker-compose.production.yml down

# 완전 제거 (데이터 삭제)
docker-compose -f docker-compose.production.yml down -v
```

## 🎯 특징

### Zero-Configuration
- 추가 설정 없이 바로 실행
- 모든 초기화 자동 수행
- 기본값으로 완벽 작동

### Production Ready
- 헬스체크 및 자동 재시작
- 로깅 및 모니터링
- 리소스 제한 설정

### 확장 가능
- 수평 확장 가능한 구조
- 마이크로서비스 아키텍처
- 독립적 배포 가능

## 📊 모니터링

### Prometheus
- 메트릭 수집: http://localhost:9090
- 모든 서비스 메트릭 자동 수집

### Grafana
- 대시보드: http://localhost:3001
- 로그인: admin / Gr@fana2025
- 사전 구성된 대시보드 제공

## 🐛 문제 해결

### 서비스가 시작되지 않을 때
```bash
# 로그 확인
docker-compose -f docker-compose.production.yml logs service-name

# 컨테이너 상태 확인
docker ps -a

# 리소스 확인
docker system df
```

### 데이터베이스 연결 실패
```bash
# PostgreSQL 확인
docker exec -it postgres-prod psql -U postgres -c "SELECT 1;"

# Redis 확인
docker exec -it redis-prod redis-cli ping
```

### 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -tulpn | grep :8000

# .env.production에서 포트 변경
GATEWAY_PORT=8080
```

## 📋 체크리스트

### 시작 전
- [ ] Docker 설치 확인
- [ ] Docker Compose 설치 확인
- [ ] 8GB 이상 여유 메모리
- [ ] 포트 8000, 3000 사용 가능

### 시작 후
- [ ] Frontend 접속 가능 (http://localhost:3000)
- [ ] API Gateway 응답 (http://localhost:8000/health)
- [ ] 데이터베이스 연결 정상
- [ ] 헬스체크 통과

## 🎉 완료!

이제 국민연금 감정분석 시스템이 프로덕션 환경에서 실행 중입니다.
http://localhost:3000 에서 대시보드에 접속할 수 있습니다.

---

문제가 발생하면 로그를 확인하고, 필요시 이슈를 등록해주세요.
