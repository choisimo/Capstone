# 🧪 통합 테스트 가이드

## 📋 테스트 개요

이 프로젝트는 3단계 테스트 전략을 사용합니다:

1. **코드 품질 테스트** (`quick-test.sh`) - 로컬 코드 검증
2. **런타임 통합 테스트** (`integration-test.sh`) - 실행 중인 서비스 API 테스트
3. **안정성 테스트** (`docker-test-and-stability.sh`) - Docker 환경에서 완전한 통합 및 안정성 검증

---

## 🚀 빠른 시작

### 1단계: 코드 품질 테스트
```bash
./quick-test.sh
```

**검증 항목**:
- 8개 백엔드 서비스 구조
- 1개 프론트엔드 서비스 구조
- Python 구문 검사
- 신규 구현 파일 (8개, 101.8 KB)
- Mock 데이터 패턴
- 핵심 문서 존재

**예상 시간**: ~30초  
**성공 기준**: 100% (47/47 테스트)

---

### 2단계: 런타임 통합 테스트 (선택)
```bash
# 서비스가 이미 실행 중인 경우
./integration-test.sh
```

**검증 항목**:
- Docker 컨테이너 상태
- 인프라 서비스 (PostgreSQL, Redis, MongoDB)
- 백엔드 서비스 (8개) 헬스 체크
- API 엔드포인트 기능 테스트

**예상 시간**: ~1분  
**성공 기준**: 80% 이상

---

### 3단계: 완전 안정성 테스트 ⭐ (필수)
```bash
./docker-test-and-stability.sh
```

**검증 항목**:
- ✅ 환경 변수 설정
- ✅ Docker 환경 확인
- ✅ 이미지 빌드
- ✅ 서비스 시작
- ✅ 컨테이너 상태 확인
- ✅ 인프라 서비스 헬스 체크
- ✅ 백엔드 서비스 헬스 체크 (8개)
- ✅ API 기능 테스트
- ✅ **60초 안정성 모니터링**
- ✅ 리소스 사용량 확인
- ✅ 에러 로그 검사

**예상 시간**: 5-10분 (빌드 포함)  
**성공 기준**: 100% (모든 서비스 안정적 실행)

---

## 📊 테스트 세부 정보

### 코드 품질 테스트 (quick-test.sh)

**백엔드 서비스** (각 4개 테스트):
- API Gateway
- Analysis Service
- ABSA Service
- Collector Service
- Alert Service
- OSINT Orchestrator
- OSINT Planning
- OSINT Source

**프론트엔드**:
- Frontend Dashboard

**신규 파일**:
| 파일 | 크기 | 설명 |
|------|------|------|
| report_service.py | 20.7 KB | PDF/Excel 리포트 생성 |
| trend_service.py | 7.2 KB | 한국어 키워드 추출 |
| validation_service.py | 11.9 KB | 품질 검증 |
| persona_scheduler.py | 14.3 KB | 배치 재계산 |
| planning_service.py | 16.0 KB | OSINT 수집 계획 |
| auth.py | 9.2 KB | JWT 인증 |
| rate_limit.py | 9.6 KB | Rate Limiting |
| RealTimeDashboard.tsx | 12.9 KB | 실시간 대시보드 |

---

### 안정성 테스트 (docker-test-and-stability.sh)

#### 테스트 단계

**1. 환경 변수 확인**
- .env 파일 존재 여부
- 필수 환경 변수 설정

**2. Docker 환경 확인**
- Docker 설치 및 버전
- Docker Compose 설치 및 버전
- Docker 데몬 실행 상태

**3. 기존 환경 정리**
- 컨테이너 중지 및 제거
- 볼륨 정리

**4. 빌드 및 시작**
- Docker 이미지 빌드 (--no-cache)
- 서비스 시작 (detached mode)
- 초기화 대기 (30초)

**5. 헬스 체크 - 인프라**
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- MongoDB: `mongosh ping`

**6. 헬스 체크 - 백엔드**
각 서비스별 `/health` 엔드포인트 확인:
- API Gateway (8000)
- Analysis Service (8001)
- Collector Service (8002)
- ABSA Service (8003)
- Alert Service (8004)
- OSINT Orchestrator (8005)
- OSINT Planning (8006)
- OSINT Source (8007)

**7. API 기능 테스트**
- Analysis Service Health
- API Gateway Health

**8. 안정성 모니터링 (60초)**
- 10초 간격으로 6회 체크
- 모든 서비스 헬스 상태 확인
- 불안정한 서비스 감지

**9. 리소스 사용량**
- CPU 사용률
- 메모리 사용량

**10. 로그 검사**
- 에러 로그 검색
- Exception 검색
- Fatal 로그 검색

---

## ⚙️ 환경 설정

### .env 파일 (자동 생성됨)

```bash
# Database
POSTGRES_PASSWORD=test_password_123
DATABASE_URL=postgresql://postgres:test_password_123@postgres:5432/pension_sentiment

# MongoDB
MONGO_ROOT_PASSWORD=test_mongo_123
MONGO_URL=mongodb://admin:test_mongo_123@mongo:27017/osint_data?authSource=admin

# Security
JWT_SECRET_KEY=test_jwt_secret_key_change_in_production

# Grafana
GF_ADMIN_PASSWORD=test_grafana_123
```

**⚠️ 주의**: 프로덕션에서는 강력한 비밀번호로 변경하세요!

---

## 📈 성공 기준

### 코드 품질 테스트
- **성공률**: 100% (47/47)
- **Python 구문 오류**: 0개
- **Mock 데이터**: 프로덕션 코드에 없음

### 안정성 테스트
- **서비스 시작**: 모든 8개 서비스 정상 실행
- **헬스 체크**: 100% 통과 (인프라 + 백엔드)
- **안정성**: 60초 동안 무중단 실행
- **에러 로그**: Critical 에러 없음

---

## 🔧 문제 해결

### 빌드 실패
```bash
# 로그 확인
cat /tmp/docker-build.log

# 개별 서비스 빌드
docker compose -f docker-compose.production.yml build <service-name>
```

### 서비스 시작 실패
```bash
# 로그 확인
docker compose -f docker-compose.production.yml logs <service-name>

# 특정 서비스 재시작
docker compose -f docker-compose.production.yml restart <service-name>
```

### 헬스 체크 실패
```bash
# 서비스 로그 실시간 확인
docker compose -f docker-compose.production.yml logs -f <service-name>

# 컨테이너 상태 확인
docker compose -f docker-compose.production.yml ps

# 컨테이너 내부 진입
docker compose -f docker-compose.production.yml exec <service-name> /bin/bash
```

### 환경 변수 문제
```bash
# .env 파일 확인
cat .env

# 특정 서비스 환경 변수 확인
docker compose -f docker-compose.production.yml config | grep -A 20 <service-name>
```

---

## 📝 테스트 리포트

테스트 완료 후 생성되는 파일:
- `/tmp/docker-build.log` - 빌드 로그
- `/tmp/docker-up.log` - 서비스 시작 로그
- `DOCUMENTS/INTEGRATION-TEST-REPORT.md` - 코드 품질 리포트

---

## 🎯 다음 단계

### 테스트 통과 후
1. **서비스 접속**
   - API Gateway: http://localhost:8000
   - Analysis Service: http://localhost:8001
   - Frontend: http://localhost:3000
   - Grafana: http://localhost:3001

2. **모니터링**
   - Prometheus: http://localhost:9090
   - Grafana 대시보드 설정

3. **로그 확인**
   ```bash
   docker compose -f docker-compose.production.yml logs -f
   ```

4. **중지**
   ```bash
   docker compose -f docker-compose.production.yml down
   ```

### 프로덕션 배포
1. **.env 파일 보안 강화**
   - 강력한 비밀번호 설정
   - JWT Secret Key 변경
   - CORS Origins 업데이트

2. **스케일링 설정**
   ```bash
   docker compose -f docker-compose.production.yml up -d --scale analysis-service=3
   ```

3. **백업 설정**
   - PostgreSQL 백업 스크립트
   - MongoDB 백업 스크립트
   - 볼륨 백업

---

## 🎉 최종 검증

**모든 테스트가 통과하면**:
- ✅ 코드 품질: 100% (47/47)
- ✅ 서비스 실행: 8/8 정상
- ✅ 안정성: 60초 무중단
- ✅ API 기능: 정상 작동

**시스템 상태**: **프로덕션 배포 가능** 🚀

---

**작성일**: 2025-09-30  
**버전**: 1.0  
**시스템 완성도**: 85%
