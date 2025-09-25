#!/bin/bash
#
# 프로젝트 검증 스크립트
# Mock 데이터, 중복 파일, 금지 패턴을 검사합니다.
#

echo "=========================================="
echo "🔍 프로젝트 검증 시작"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 에러 카운트
ERROR_COUNT=0

echo ""
echo "1️⃣ Mock 패턴 검색 중..."
echo "----------------------------------------"

# Mock 관련 패턴 검색
MOCK_PATTERNS="random\.\|mock\|fake\|dummy\|test_data\|sample_data"
MOCK_FILES=$(grep -r "$MOCK_PATTERNS" --include="*.py" --exclude-dir=".git" --exclude-dir="__pycache__" --exclude-dir="venv" . 2>/dev/null | grep -v "^Binary file")

if [ ! -z "$MOCK_FILES" ]; then
    echo -e "${RED}❌ Mock 패턴 발견!${NC}"
    echo "$MOCK_FILES" | head -20
    echo "..."
    ERROR_COUNT=$((ERROR_COUNT + $(echo "$MOCK_FILES" | wc -l)))
else
    echo -e "${GREEN}✅ Mock 패턴 없음${NC}"
fi

echo ""
echo "2️⃣ 중복/금지 파일명 검색 중..."
echo "----------------------------------------"

# 금지된 파일명 패턴
BANNED_FILES=$(find . -type f \( \
    -name "*_new.py" -o \
    -name "*_v2.py" -o \
    -name "*_backup.py" -o \
    -name "*_old.py" -o \
    -name "*_temp.py" -o \
    -name "*_copy.py" -o \
    -name "*_fake.py" -o \
    -name "*_mock.py" \
    \) 2>/dev/null | grep -v ".git")

if [ ! -z "$BANNED_FILES" ]; then
    echo -e "${RED}❌ 금지된 파일명 발견!${NC}"
    echo "$BANNED_FILES"
    ERROR_COUNT=$((ERROR_COUNT + $(echo "$BANNED_FILES" | wc -l)))
else
    echo -e "${GREEN}✅ 금지된 파일명 없음${NC}"
fi

echo ""
echo "3️⃣ Faker/Mock 라이브러리 import 검색 중..."
echo "----------------------------------------"

# 금지된 import 검색
BANNED_IMPORTS=$(grep -r "from faker\|import faker\|from unittest.mock\|import mock" --include="*.py" --exclude-dir=".git" --exclude-dir="__pycache__" . 2>/dev/null)

if [ ! -z "$BANNED_IMPORTS" ]; then
    echo -e "${RED}❌ 금지된 import 발견!${NC}"
    echo "$BANNED_IMPORTS"
    ERROR_COUNT=$((ERROR_COUNT + $(echo "$BANNED_IMPORTS" | wc -l)))
else
    echo -e "${GREEN}✅ 금지된 import 없음${NC}"
fi

echo ""
echo "4️⃣ 가짜 URL 패턴 검색 중..."
echo "----------------------------------------"

# 가짜 URL 패턴
FAKE_URLS=$(grep -r "example\.com\|test\.com\|fake\.com\|dummy\.com\|localhost:[0-9]*\/fake" --include="*.py" --include="*.json" --exclude-dir=".git" . 2>/dev/null | grep -v "^Binary file")

if [ ! -z "$FAKE_URLS" ]; then
    echo -e "${YELLOW}⚠️  의심스러운 URL 패턴 발견 (검토 필요)${NC}"
    echo "$FAKE_URLS" | head -10
    echo "..."
else
    echo -e "${GREEN}✅ 가짜 URL 패턴 없음${NC}"
fi

echo ""
echo "5️⃣ Random 모듈 사용 검색 중..."
echo "----------------------------------------"

# random 모듈 사용
RANDOM_USAGE=$(grep -r "import random\|random\.choice\|random\.randint\|random\.uniform" --include="*.py" --exclude-dir=".git" --exclude-dir="__pycache__" . 2>/dev/null)

if [ ! -z "$RANDOM_USAGE" ]; then
    echo -e "${RED}❌ Random 모듈 사용 발견!${NC}"
    echo "$RANDOM_USAGE" | head -10
    echo "..."
    ERROR_COUNT=$((ERROR_COUNT + $(echo "$RANDOM_USAGE" | wc -l)))
else
    echo -e "${GREEN}✅ Random 모듈 사용 없음${NC}"
fi

echo ""
echo "=========================================="
echo "📊 검증 결과"
echo "=========================================="

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ 프로젝트가 모든 규칙을 준수합니다!${NC}"
    echo "   - Mock 데이터 없음"
    echo "   - 중복 파일 없음"
    echo "   - 금지 패턴 없음"
    exit 0
else
    echo -e "${RED}❌ 총 ${ERROR_COUNT}개의 규칙 위반 발견!${NC}"
    echo ""
    echo "🔧 조치 방법:"
    echo "1. Mock 패턴이 있는 파일을 Edit 도구로 수정"
    echo "2. 중복 파일(*_new.py 등) 삭제"
    echo "3. Random 모듈 제거하고 실제 데이터로 대체"
    echo "4. 가짜 URL을 실제 URL로 변경"
    echo ""
    echo "자세한 내용은 .windsurf/workflows/MASTER_RULES.md 참조"
    exit 1
fi
