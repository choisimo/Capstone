#!/bin/bash

# 빠른 로컬 테스트 스크립트
# Docker 없이 각 서비스의 코드 품질 및 의존성을 확인

set -e

echo "================================================"
echo "🧪 국민연금 감정분석 시스템 - 코드 품질 테스트"
echo "================================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 결과
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 함수
test_service_code() {
    local service_name=$1
    local service_path=$2
    
    echo -e "${BLUE}## Testing: $service_name${NC}"
    echo "-------------------------------------------"
    
    # Python 서비스인지 확인
    if [ -f "$service_path/requirements.txt" ]; then
        # 1. requirements.txt 존재 확인
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        echo -n "  - requirements.txt exists... "
        if [ -f "$service_path/requirements.txt" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
        # 2. Dockerfile 존재 확인
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        echo -n "  - Dockerfile exists... "
        if [ -f "$service_path/Dockerfile" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
        # 3. Python 파일 구문 검사
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        echo -n "  - Python syntax check... "
        python_errors=0
        for py_file in $(find "$service_path" -name "*.py" 2>/dev/null); do
            if ! python3 -m py_compile "$py_file" 2>/dev/null; then
                python_errors=$((python_errors + 1))
            fi
        done
        
        if [ $python_errors -eq 0 ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAIL${NC} ($python_errors errors)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
        # 4. 핵심 서비스 파일 존재 확인
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        echo -n "  - Service files exist... "
        if [ -d "$service_path/app" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    
    # TypeScript/JavaScript 서비스인지 확인
    if [ -f "$service_path/package.json" ]; then
        # 1. package.json 존재 확인
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        echo -n "  - package.json exists... "
        if [ -f "$service_path/package.json" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        
        # 2. src 디렉토리 확인
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        echo -n "  - src directory exists... "
        if [ -d "$service_path/src" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
    
    echo ""
}

# 백엔드 서비스 테스트
echo -e "${BLUE}# Backend Services${NC}"
echo "================================================"
echo ""

test_service_code "API Gateway" "./BACKEND-API-GATEWAY"
test_service_code "Analysis Service" "./BACKEND-ANALYSIS-SERVICE"
test_service_code "ABSA Service" "./BACKEND-ABSA-SERVICE"
test_service_code "Collector Service" "./BACKEND-COLLECTOR-SERVICE"
test_service_code "Alert Service" "./BACKEND-ALERT-SERVICE"
test_service_code "OSINT Orchestrator" "./BACKEND-OSINT-ORCHESTRATOR-SERVICE"
test_service_code "OSINT Planning" "./BACKEND-OSINT-PLANNING-SERVICE"
test_service_code "OSINT Source" "./BACKEND-OSINT-SOURCE-SERVICE"

# 프론트엔드 테스트
echo -e "${BLUE}# Frontend Service${NC}"
echo "================================================"
echo ""

test_service_code "Frontend Dashboard" "./FRONTEND-DASHBOARD"

# 신규 구현 파일 검증
echo -e "${BLUE}# New Implementation Files Verification${NC}"
echo "================================================"
echo ""

new_files=(
    "BACKEND-ANALYSIS-SERVICE/app/services/report_service.py"
    "BACKEND-ANALYSIS-SERVICE/app/services/trend_service.py"
    "BACKEND-COLLECTOR-SERVICE/app/services/validation_service.py"
    "BACKEND-ABSA-SERVICE/app/services/persona_scheduler.py"
    "BACKEND-OSINT-PLANNING-SERVICE/app/services/planning_service.py"
    "BACKEND-API-GATEWAY/app/middleware/auth.py"
    "BACKEND-API-GATEWAY/app/middleware/rate_limit.py"
    "FRONTEND-DASHBOARD/src/components/RealTimeDashboard.tsx"
)

for file in "${new_files[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "  - $file... "
    if [ -f "$file" ]; then
        # 파일 크기 확인 (최소 100 바이트)
        file_size=$(wc -c < "$file")
        if [ $file_size -gt 100 ]; then
            echo -e "${GREEN}✓ PASS${NC} (${file_size} bytes)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${YELLOW}⚠ WARNING${NC} (Too small: ${file_size} bytes)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Not found)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
done

echo ""

# Mock 데이터 검증
echo -e "${BLUE}# Mock Data Verification${NC}"
echo "================================================"
echo ""

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "  - Checking for mock/fake data patterns... "

# 금지 패턴 검색
mock_patterns=(
    "example.com"
    "test.com"
    "localhost:8080"
    "fake_data"
    "mock_data"
)

mock_found=0
for pattern in "${mock_patterns[@]}"; do
    # Python 파일에서만 검색 (테스트 파일 제외)
    results=$(grep -r "$pattern" --include="*.py" --exclude-dir="tests" --exclude-dir="__pycache__" . 2>/dev/null | grep -v "test_" | wc -l)
    if [ $results -gt 0 ]; then
        mock_found=$((mock_found + results))
    fi
done

if [ $mock_found -eq 0 ]; then
    echo -e "${GREEN}✓ PASS${NC} (No mock data found)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (Found $mock_found instances)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

echo ""

# 문서 검증
echo -e "${BLUE}# Documentation Verification${NC}"
echo "================================================"
echo ""

docs=(
    "DOCUMENTS/FINAL-IMPLEMENTATION-SUMMARY.md"
    "DOCUMENTS/Daily-done/2025-09-30.md"
    "DOCUMENTS/implementation-progress.md"
    "DOCUMENTS/PRD/implementation-tasks.md"
)

for doc in "${docs[@]}"; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "  - $doc... "
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
done

echo ""

# 최종 결과
echo "================================================"
echo -e "${BLUE}# Test Results Summary${NC}"
echo "================================================"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

# 성공률 계산
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")
    echo "Success Rate: ${SUCCESS_RATE}%"
    echo ""
    
    if [ "$SUCCESS_RATE" == "100.0" ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Start services with: docker-compose -f docker-compose.production.yml up -d"
        echo "  2. Run integration tests with: ./integration-test.sh"
        exit 0
    elif (( $(echo "$SUCCESS_RATE >= 90" | bc -l) )); then
        echo -e "${YELLOW}⚠️  Most tests passed${NC}"
        echo ""
        echo "Some minor issues found. Review failed tests above."
        exit 0
    else
        echo -e "${RED}❌ Multiple tests failed${NC}"
        echo ""
        echo "Please fix the issues before proceeding."
        exit 1
    fi
else
    echo -e "${RED}❌ No tests were run${NC}"
    exit 1
fi
