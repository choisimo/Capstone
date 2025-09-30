#!/bin/bash

# Docker Compose 실행 및 안정성 테스트
# 실제 프로덕션 환경과 유사한 조건에서 모든 서비스 테스트

set -e

echo "================================================"
echo "🐳 Docker Compose 통합 안정성 테스트"
echo "================================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
COMPOSE_FILE="docker-compose.production.yml"
STABILITY_CHECK_DURATION=60  # 안정성 체크 시간 (초)
HEALTH_CHECK_INTERVAL=10     # 헬스 체크 간격 (초)
MAX_RETRIES=5                # 최대 재시도 횟수

# 테스트 결과
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 테스트 함수
test_step() {
    local name=$1
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing $name... "
}

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

test_fail() {
    local reason=$1
    echo -e "${RED}✗ FAIL${NC} ($reason)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

# 1. 환경 변수 확인
echo -e "${BLUE}## 1. 환경 변수 확인${NC}"
echo "-------------------------------------------"

test_step ".env 파일 존재"
if [ -f .env ]; then
    test_pass
else
    log_warning ".env 파일이 없습니다. .env.example에서 생성합니다."
    if [ -f .env.example ]; then
        cp .env.example .env
        log_info "기본 비밀번호를 설정하세요!"
        test_pass
    else
        test_fail "No .env.example"
        log_error ".env.example 파일이 없습니다."
        exit 1
    fi
fi

echo ""

# 2. Docker 및 Docker Compose 확인
echo -e "${BLUE}## 2. Docker 환경 확인${NC}"
echo "-------------------------------------------"

test_step "Docker 설치"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ PASS${NC} ($DOCKER_VERSION)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    test_fail "Not installed"
    log_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi

test_step "Docker Compose 설치"
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "${GREEN}✓ PASS${NC} ($COMPOSE_VERSION)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    test_fail "Not installed"
    log_error "Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

test_step "Docker 데몬 실행"
if docker ps &> /dev/null; then
    test_pass
else
    test_fail "Not running"
    log_error "Docker 데몬이 실행되지 않고 있습니다."
    exit 1
fi

echo ""

# 3. 기존 컨테이너 정리
echo -e "${BLUE}## 3. 기존 환경 정리${NC}"
echo "-------------------------------------------"

log_info "기존 컨테이너 중지 및 제거..."
docker compose -f $COMPOSE_FILE down -v 2>/dev/null || true
log_success "정리 완료"

echo ""

# 4. Docker Compose 빌드 및 시작
echo -e "${BLUE}## 4. 서비스 빌드 및 시작${NC}"
echo "-------------------------------------------"

log_info "Docker 이미지 빌드 중... (시간이 걸릴 수 있습니다)"
if docker compose -f $COMPOSE_FILE build --no-cache 2>&1 | tee /tmp/docker-build.log; then
    log_success "빌드 완료"
else
    log_error "빌드 실패. 로그를 확인하세요: /tmp/docker-build.log"
    exit 1
fi

echo ""

log_info "서비스 시작 중..."
if docker compose -f $COMPOSE_FILE up -d 2>&1 | tee /tmp/docker-up.log; then
    log_success "서비스 시작 완료"
else
    log_error "서비스 시작 실패. 로그를 확인하세요: /tmp/docker-up.log"
    exit 1
fi

echo ""

# 5. 컨테이너 상태 확인
echo -e "${BLUE}## 5. 컨테이너 상태 확인${NC}"
echo "-------------------------------------------"

log_info "30초 대기 (초기화 시간)..."
sleep 30

log_info "실행 중인 컨테이너:"
docker compose -f $COMPOSE_FILE ps

echo ""

# 6. 헬스 체크 - 인프라 서비스
echo -e "${BLUE}## 6. 인프라 서비스 헬스 체크${NC}"
echo "-------------------------------------------"

test_step "PostgreSQL"
for i in {1..5}; do
    if docker compose -f $COMPOSE_FILE exec -T postgres pg_isready -U postgres &>/dev/null; then
        test_pass
        break
    fi
    if [ $i -eq 5 ]; then
        test_fail "Not ready after 5 attempts"
    fi
    sleep 5
done

test_step "Redis"
for i in {1..5}; do
    if docker compose -f $COMPOSE_FILE exec -T redis redis-cli ping | grep -q PONG; then
        test_pass
        break
    fi
    if [ $i -eq 5 ]; then
        test_fail "Not ready after 5 attempts"
    fi
    sleep 5
done

test_step "MongoDB"
for i in {1..5}; do
    if docker compose -f $COMPOSE_FILE exec -T mongo mongosh --eval "db.adminCommand('ping')" &>/dev/null; then
        test_pass
        break
    fi
    if [ $i -eq 5 ]; then
        test_fail "Not ready after 5 attempts"
    fi
    sleep 5
done

echo ""

# 7. 헬스 체크 - 백엔드 서비스
echo -e "${BLUE}## 7. 백엔드 서비스 헬스 체크${NC}"
echo "-------------------------------------------"

log_info "20초 추가 대기 (서비스 초기화)..."
sleep 20

services=(
    "api-gateway:8000"
    "analysis-service:8001"
    "collector-service:8002"
    "absa-service:8003"
    "alert-service:8004"
    "osint-orchestrator:8005"
    "osint-planning:8006"
    "osint-source:8007"
)

for service_port in "${services[@]}"; do
    service=$(echo $service_port | cut -d: -f1)
    port=$(echo $service_port | cut -d: -f2)
    
    test_step "$service"
    
    retry=0
    while [ $retry -lt $MAX_RETRIES ]; do
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ] || [ "$response" = "204" ]; then
            test_pass
            break
        fi
        
        retry=$((retry + 1))
        if [ $retry -eq $MAX_RETRIES ]; then
            test_fail "HTTP $response after $MAX_RETRIES attempts"
        else
            sleep 5
        fi
    done
done

echo ""

# 8. API 기능 테스트
echo -e "${BLUE}## 8. API 기능 테스트${NC}"
echo "-------------------------------------------"

test_step "Analysis Service - Health"
response=$(curl -s http://localhost:8001/health)
if [ -n "$response" ]; then
    test_pass
else
    test_fail "No response"
fi

test_step "API Gateway - Health"
response=$(curl -s http://localhost:8000/health)
if [ -n "$response" ]; then
    test_pass
else
    test_fail "No response"
fi

echo ""

# 9. 안정성 테스트
echo -e "${BLUE}## 9. 안정성 테스트 (${STABILITY_CHECK_DURATION}초)${NC}"
echo "-------------------------------------------"

log_info "서비스 안정성 모니터링 시작..."

stability_checks=$((STABILITY_CHECK_DURATION / HEALTH_CHECK_INTERVAL))
unstable_services=()

for ((i=1; i<=stability_checks; i++)); do
    echo -n "Check $i/$stability_checks: "
    
    failed_in_check=0
    for service_port in "${services[@]}"; do
        service=$(echo $service_port | cut -d: -f1)
        port=$(echo $service_port | cut -d: -f2)
        
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null || echo "000")
        
        if [ "$response" != "200" ] && [ "$response" != "204" ]; then
            failed_in_check=$((failed_in_check + 1))
            if [[ ! " ${unstable_services[@]} " =~ " ${service} " ]]; then
                unstable_services+=("$service")
            fi
        fi
    done
    
    if [ $failed_in_check -eq 0 ]; then
        echo -e "${GREEN}✓ All services stable${NC}"
    else
        echo -e "${YELLOW}⚠ $failed_in_check services unstable${NC}"
    fi
    
    sleep $HEALTH_CHECK_INTERVAL
done

echo ""

test_step "안정성 검증"
if [ ${#unstable_services[@]} -eq 0 ]; then
    test_pass
    log_success "모든 서비스가 ${STABILITY_CHECK_DURATION}초 동안 안정적으로 실행되었습니다!"
else
    test_fail "${#unstable_services[@]} services unstable"
    log_warning "불안정한 서비스: ${unstable_services[*]}"
fi

echo ""

# 10. 리소스 사용량 확인
echo -e "${BLUE}## 10. 리소스 사용량${NC}"
echo "-------------------------------------------"

log_info "Docker 컨테이너 리소스 사용량:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -15

echo ""

# 11. 로그 확인
echo -e "${BLUE}## 11. 에러 로그 확인${NC}"
echo "-------------------------------------------"

log_info "최근 에러 로그 검사 중..."

error_count=0
for service_port in "${services[@]}"; do
    service=$(echo $service_port | cut -d: -f1)
    
    errors=$(docker compose -f $COMPOSE_FILE logs $service 2>&1 | grep -i "error\|exception\|fatal" | grep -v "error_handler" | wc -l)
    
    if [ $errors -gt 0 ]; then
        log_warning "$service: $errors error(s) found"
        error_count=$((error_count + errors))
    fi
done

test_step "로그 에러 확인"
if [ $error_count -eq 0 ]; then
    test_pass
    log_success "에러 로그가 없습니다"
else
    test_fail "$error_count errors found"
    log_warning "총 $error_count 개의 에러 로그가 발견되었습니다. 상세 로그를 확인하세요."
fi

echo ""

# 12. 최종 결과
echo "================================================"
echo -e "${BLUE}## 최종 테스트 결과${NC}"
echo "================================================"
echo ""

echo "총 테스트: $TOTAL_TESTS"
echo -e "${GREEN}성공: $PASSED_TESTS${NC}"
echo -e "${RED}실패: $FAILED_TESTS${NC}"
echo ""

if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    echo "성공률: ${SUCCESS_RATE}%"
    echo ""
    
    if [ "$SUCCESS_RATE" == "100.0" ]; then
        echo -e "${GREEN}🎉 모든 테스트 통과! 시스템이 안정적으로 실행 중입니다.${NC}"
        echo ""
        echo "서비스 접속 정보:"
        echo "  - API Gateway: http://localhost:8000"
        echo "  - Analysis Service: http://localhost:8001"
        echo "  - ABSA Service: http://localhost:8003"
        echo "  - Frontend Dashboard: http://localhost:3000"
        echo "  - Prometheus: http://localhost:9090"
        echo "  - Grafana: http://localhost:3001"
        echo ""
        echo "로그 확인: docker compose -f $COMPOSE_FILE logs -f"
        echo "중지: docker compose -f $COMPOSE_FILE down"
        exit 0
    elif (( $(echo "$SUCCESS_RATE >= 80" | bc -l) )); then
        echo -e "${YELLOW}⚠️  대부분의 테스트 통과 (일부 서비스 불안정)${NC}"
        echo ""
        echo "불안정한 서비스를 확인하고 수정이 필요합니다."
        echo "로그 확인: docker compose -f $COMPOSE_FILE logs -f <service-name>"
        exit 0
    else
        echo -e "${RED}❌ 테스트 실패: 여러 서비스에 문제가 있습니다${NC}"
        echo ""
        echo "문제 해결 단계:"
        echo "  1. 로그 확인: docker compose -f $COMPOSE_FILE logs"
        echo "  2. 개별 서비스 재시작: docker compose -f $COMPOSE_FILE restart <service>"
        echo "  3. 환경 변수 확인: cat .env"
        exit 1
    fi
else
    echo -e "${RED}❌ 테스트를 실행할 수 없습니다${NC}"
    exit 1
fi
