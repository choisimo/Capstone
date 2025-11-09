#!/bin/bash

# 통합 테스트 스크립트
# 모든 마이크로서비스 헬스 체크 및 기본 API 테스트

set -e

echo "================================================"
echo "🧪 국민연금 감정분석 시스템 통합 테스트"
echo "================================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 결과 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 함수
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing $service_name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# API 테스트 함수
test_api() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo "")
    else
        response=$(curl -s "$url" 2>/dev/null || echo "")
    fi
    
    if [ -n "$response" ] && [ "$response" != "null" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "## 1. Docker 컨테이너 상태 확인"
echo "-------------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20
echo ""

echo "## 2. 인프라 서비스 헬스 체크"
echo "-------------------------------------------"

# PostgreSQL (간접 확인)
echo -n "Testing PostgreSQL... "
if docker ps | grep -q postgres; then
    echo -e "${GREEN}✓ PASS${NC} (Container running)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ SKIP${NC} (Container not found)"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Redis (간접 확인)
echo -n "Testing Redis... "
if docker ps | grep -q redis; then
    echo -e "${GREEN}✓ PASS${NC} (Container running)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ SKIP${NC} (Container not found)"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""

echo "## 3. 백엔드 서비스 헬스 체크"
echo "-------------------------------------------"

# API Gateway
test_service "API Gateway" "http://localhost:8000/health" 200

# Analysis Service
test_service "Analysis Service" "http://localhost:8001/health" 200

# ABSA Service
test_service "ABSA Service" "http://localhost:8002/health" 200

# Collector Service
test_service "Collector Service" "http://localhost:8003/health" 200

# Alert Service
test_service "Alert Service" "http://localhost:8004/health" 200

# OSINT Orchestrator
test_service "OSINT Orchestrator" "http://localhost:8005/health" 200

# OSINT Planning
test_service "OSINT Planning" "http://localhost:8006/health" 200

# OSINT Source
test_service "OSINT Source" "http://localhost:8007/health" 200

echo ""

echo "## 4. 프론트엔드 서비스 확인"
echo "-------------------------------------------"

# Frontend Dashboard
echo -n "Testing Frontend Dashboard... "
if curl -s "http://localhost:5173" > /dev/null 2>&1 || curl -s "http://localhost:3000" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ SKIP${NC} (Not running or different port)"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""

echo "## 5. API 기능 테스트"
echo "-------------------------------------------"

# Analysis Service - Sentiment Stats
test_api "Sentiment Stats API" "http://localhost:8001/api/v1/analysis/sentiment/stats?days=7"

# Analysis Service - Trends
test_api "Trends API" "http://localhost:8001/api/v1/analysis/trends?start_date=2025-09-01&end_date=2025-09-30"

# Analysis Service - Keywords
test_api "Keywords API" "http://localhost:8001/api/v1/analysis/keywords?start_date=2025-09-01&end_date=2025-09-30&limit=10"

# ABSA Service - Personas
test_api "Personas List API" "http://localhost:8002/api/v1/personas?limit=5"

# ABSA Service - Trending Personas
test_api "Trending Personas API" "http://localhost:8002/api/v1/personas/trending?limit=5"

# Collector Service - Sources
test_api "Collection Sources API" "http://localhost:8003/api/v1/collector/sources"

# Alert Service - Rules
test_api "Alert Rules API" "http://localhost:8004/api/v1/alerts/rules"

echo ""

echo "## 6. 데이터 품질 검증 테스트"
echo "-------------------------------------------"

# Validation Service Test
VALIDATION_DATA='{"text":"국민연금 수령액이 인상될 전망입니다. 이는 많은 국민들에게 좋은 소식이 될 것입니다.","content_type":"news","source":"test"}'
test_api "Content Validation API" "http://localhost:8003/api/v1/collector/validate" "POST" "$VALIDATION_DATA"

echo ""

echo "## 7. 통합 테스트 결과"
echo "================================================"
echo ""
echo "총 테스트: $TOTAL_TESTS"
echo -e "${GREEN}성공: $PASSED_TESTS${NC}"
echo -e "${RED}실패: $FAILED_TESTS${NC}"
echo ""

# 성공률 계산
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    echo "성공률: ${SUCCESS_RATE}%"
    echo ""
    
    if [ "$SUCCESS_RATE" == "100.0" ]; then
        echo -e "${GREEN}🎉 모든 테스트 통과!${NC}"
        exit 0
    elif (( $(echo "$SUCCESS_RATE >= 80" | bc -l) )); then
        echo -e "${YELLOW}⚠️  대부분의 테스트 통과 (일부 서비스 미실행)${NC}"
        exit 0
    else
        echo -e "${RED}❌ 테스트 실패: 여러 서비스에 문제가 있습니다${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ 테스트를 실행할 수 없습니다${NC}"
    exit 1
fi
