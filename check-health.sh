#!/bin/bash

# 서비스 헬스체크 스크립트

echo "🏥 서비스 헬스체크 시작..."
echo "================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 서비스 목록
services=(
    "API Gateway:8000"
    "Analysis Service:8001"
    "Collector Service:8002"
    "ABSA Service:8003"
    "Alert Service:8004"
    "OSINT Orchestrator:8005"
    "OSINT Planning:8006"
    "OSINT Source:8007"
    "Frontend:3000"
)

# 헬스체크 함수
check_health() {
    local name=$1
    local port=$2
    local path="/health"
    
    # Frontend는 루트 경로로 헬스체크
    if [ "$name" = "Frontend" ]; then
        path="/"
    elif [ "$name" = "Collector Service" ]; then
        # Collector는 readiness 기준
        path="/ready"
    fi
    
    if curl -f -s "http://localhost:${port}${path}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${name} (port ${port}) - HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ ${name} (port ${port}) - UNHEALTHY${NC}"
        return 1
    fi
}

# 헬스체크 실행
failed=0
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if ! check_health "$name" "$port"; then
        ((failed++))
    fi
done

echo "================================"
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 서비스 정상${NC}"
else
    echo -e "${YELLOW}⚠️  ${failed}개 서비스 문제 발견${NC}"
fi
