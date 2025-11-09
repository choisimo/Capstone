#!/bin/bash

# MSA 통합 테스트 스크립트
# 각 서비스의 상태와 서비스 간 통신을 검증합니다.

set -e

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 서비스 URL 정의
API_GATEWAY="http://localhost:8000"
ANALYSIS_SERVICE="http://localhost:8001"
COLLECTOR_SERVICE="http://localhost:8002"
ABSA_SERVICE="http://localhost:8003"
ALERT_SERVICE="http://localhost:8004"
DASHBOARD="http://localhost:3000"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  연금 감성 분석 플랫폼 MSA 테스트${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# 함수: 서비스 헬스 체크
check_service_health() {
    local service_name=$1
    local service_url=$2
    
    echo -e "${YELLOW}Checking $service_name...${NC}"
    
    if curl -s -f "$service_url/health" > /dev/null 2>&1; then
        response=$(curl -s "$service_url/health")
        echo -e "${GREEN}✓ $service_name is healthy${NC}"
        echo "  Response: $response"
    else
        echo -e "${RED}✗ $service_name is not responding${NC}"
        return 1
    fi
    echo
}

# 함수: API Gateway 프록시 테스트
test_gateway_proxy() {
    echo -e "${BLUE}=== Testing API Gateway Proxy ===${NC}"
    echo
    
    # Analysis service proxy
    echo -e "${YELLOW}Testing /analysis proxy...${NC}"
    if curl -s -f "$API_GATEWAY/analysis/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Analysis proxy working${NC}"
    else
        echo -e "${RED}✗ Analysis proxy failed${NC}"
    fi
    
    # ABSA service proxy
    echo -e "${YELLOW}Testing /absa proxy...${NC}"
    if curl -s -f "$API_GATEWAY/absa/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ABSA proxy working${NC}"
    else
        echo -e "${RED}✗ ABSA proxy failed${NC}"
    fi
    
    # Alert service proxy
    echo -e "${YELLOW}Testing /alerts proxy...${NC}"
    if curl -s -f "$API_GATEWAY/alerts/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Alert proxy working${NC}"
    else
        echo -e "${RED}✗ Alert proxy failed${NC}"
    fi
    
    # Collector service proxy
    echo -e "${YELLOW}Testing /collector proxy...${NC}"
    if curl -s -f "$API_GATEWAY/collector/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Collector proxy working${NC}"
    else
        echo -e "${RED}✗ Collector proxy failed${NC}"
    fi
    echo
}

# 함수: 데이터베이스 연결 테스트
test_database_connection() {
    echo -e "${BLUE}=== Testing Database Connection ===${NC}"
    echo
    
    echo -e "${YELLOW}Testing PostgreSQL connection...${NC}"
    if PGPASSWORD=password psql -h localhost -U postgres -d pension_sentiment -c '\l' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is accessible${NC}"
    else
        echo -e "${RED}✗ PostgreSQL connection failed${NC}"
    fi
    
    echo -e "${YELLOW}Testing Redis connection...${NC}"
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is accessible${NC}"
    else
        echo -e "${RED}✗ Redis connection failed${NC}"
    fi
    echo
}

# 함수: 통합 시나리오 테스트
test_integration_scenario() {
    echo -e "${BLUE}=== Running Integration Scenario ===${NC}"
    echo
    
    # 1. 감성 분석 요청 테스트
    echo -e "${YELLOW}1. Testing sentiment analysis...${NC}"
    SENTIMENT_REQUEST='{"text":"국민연금 정책이 매우 만족스럽습니다.","content_id":"test-001"}'
    
    response=$(curl -s -X POST "$API_GATEWAY/analysis/sentiment/analyze" \
        -H "Content-Type: application/json" \
        -d "$SENTIMENT_REQUEST" 2>/dev/null) || true
    
    if [ -n "$response" ]; then
        echo -e "${GREEN}✓ Sentiment analysis successful${NC}"
        echo "  Response: $response"
    else
        echo -e "${RED}✗ Sentiment analysis failed${NC}"
    fi
    echo
    
    # 2. ABSA 분석 테스트
    echo -e "${YELLOW}2. Testing ABSA analysis...${NC}"
    ABSA_REQUEST='{"text":"보험료는 높지만 안정성은 좋습니다.","aspects":["보험료","안정성"]}'
    
    response=$(curl -s -X POST "$API_GATEWAY/absa/analyze" \
        -H "Content-Type: application/json" \
        -d "$ABSA_REQUEST" 2>/dev/null) || true
    
    if [ -n "$response" ]; then
        echo -e "${GREEN}✓ ABSA analysis successful${NC}"
        echo "  Response: $response"
    else
        echo -e "${RED}✗ ABSA analysis failed${NC}"
    fi
    echo
    
    # 3. 알림 규칙 조회 테스트
    echo -e "${YELLOW}3. Testing alert rules...${NC}"
    response=$(curl -s "$API_GATEWAY/alerts/rules" 2>/dev/null) || true
    
    if [ -n "$response" ]; then
        echo -e "${GREEN}✓ Alert rules query successful${NC}"
    else
        echo -e "${RED}✗ Alert rules query failed${NC}"
    fi
    echo
}

# 함수: 서비스 로그 확인
check_service_logs() {
    echo -e "${BLUE}=== Recent Service Logs ===${NC}"
    echo
    
    services=("pension-api-gateway" "pension-analysis-service" "pension-absa-service" "pension-alert-service" "pension-collector-service")
    
    for service in "${services[@]}"; do
        echo -e "${YELLOW}Recent logs for $service:${NC}"
        docker logs --tail 5 "$service" 2>&1 | head -n 5 || echo "  Service not running"
        echo
    done
}

# 메인 실행 로직
main() {
    # 1. 인프라 서비스 체크
    echo -e "${BLUE}=== Infrastructure Services ===${NC}"
    echo
    test_database_connection
    
    # 2. 각 마이크로서비스 헬스 체크
    echo -e "${BLUE}=== Microservices Health Check ===${NC}"
    echo
    check_service_health "API Gateway" "$API_GATEWAY"
    check_service_health "Analysis Service" "$ANALYSIS_SERVICE"
    check_service_health "ABSA Service" "$ABSA_SERVICE"
    check_service_health "Alert Service" "$ALERT_SERVICE"
    check_service_health "Collector Service" "$COLLECTOR_SERVICE"
    
    # 3. API Gateway 프록시 테스트
    test_gateway_proxy
    
    # 4. 통합 시나리오 테스트
    test_integration_scenario
    
    # 5. 서비스 로그 확인
    if [ "$1" == "--with-logs" ]; then
        check_service_logs
    fi
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}MSA 테스트 완료!${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 스크립트 실행
main "$@"
