#!/bin/bash

# Project Validation Script
# 프로젝트 전체에서 금지 패턴을 검사하고 품질을 검증합니다.

set -e

echo "========================================="
echo "프로젝트 검증 시작: $(date)"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# 1. Mock/Fake 패턴 검색
echo -e "\n${YELLOW}[1/5] Mock/Fake 패턴 검사${NC}"
echo "----------------------------------------"

# Python 파일에서 mock 패턴 검색
MOCK_PATTERNS=$(grep -r "random\.\|faker\.\|Mock()\|from unittest.mock\|import mock" \
  --include="*.py" \
  --exclude-dir=tests --exclude-dir=test --exclude-dir=__pycache__ \
  --exclude-dir=venv --exclude-dir=env --exclude-dir=.venv --exclude-dir=node_modules \
  --exclude-dir=dist-packages --exclude-dir=site-packages \
  . 2>/dev/null | grep -v "test_" || true)
if [ ! -z "$MOCK_PATTERNS" ]; then
    echo -e "${RED}❌ Mock 패턴 발견:${NC}"
    echo "$MOCK_PATTERNS" | head -20
    ((ERRORS++))
else
    echo -e "${GREEN}✅ Mock 패턴 없음${NC}"
fi

# 2. 중복/버전 파일 검사
echo -e "\n${YELLOW}[2/5] 중복/버전 파일 검사${NC}"
echo "----------------------------------------"

DUPLICATE_FILES=$(find . -type f \( -name "*_v2.py" -o -name "*_new.py" -o -name "*_backup.py" -o -name "*_old.py" -o -name "*_temp.py" \) 2>/dev/null | grep -v "__pycache__" || true)
if [ ! -z "$DUPLICATE_FILES" ]; then
    echo -e "${RED}❌ 중복/버전 파일 발견:${NC}"
    echo "$DUPLICATE_FILES"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ 중복 파일 없음${NC}"
fi

# 3. 금지된 URL 패턴 검사
echo -e "\n${YELLOW}[3/5] 금지된 URL 패턴 검사${NC}"

FAKE_URLS=$(grep -r "example\.com\|test\.com\|localhost\.com\|dummy\.com" \
  --include="*.py" --include="*.js" --include="*.jsx" \
  --exclude-dir=tests --exclude-dir=test --exclude-dir=node_modules \
  --exclude-dir=venv --exclude-dir=.venv --exclude-dir=env . 2>/dev/null || true)
  if [ ! -z "$FAKE_URLS" ]; then
    echo -e "${YELLOW}⚠️  가짜 URL 패턴 발견:${NC}"
    echo "$FAKE_URLS" | head -10
    ((WARNINGS++))
  else
    echo -e "${GREEN}✅ 가짜 URL 패턴 없음${NC}"
  fi

  # 4. 환경변수 파일 검사
  echo -e "\n${YELLOW}[4/5] 환경변수 파일 검사${NC}"
  echo "----------------------------------------"

  ENV_FILES=$(find . -name ".env" 2>/dev/null | grep -v node_modules || true)
  if [ -n "$ENV_FILES" ]; then
    echo -e "${YELLOW}⚠️  .env 파일 발견 (커밋 금지):${NC}"
    echo "$ENV_FILES"
    ((WARNINGS++))
  fi

  ENV_EXAMPLE=$(find . -name ".env.example" -o -name ".env.sample" 2>/dev/null | head -5 || true)
  if [ -n "$ENV_EXAMPLE" ]; then
    echo -e "${GREEN}✅ .env.example 파일 존재${NC}"
  else
    echo -e "${YELLOW}⚠️  .env.example 파일 없음${NC}"
    ((WARNINGS++))
  fi

# 5. QA 설정 검증
echo -e "\n${YELLOW}[5/5] QA 설정 검증${NC}"
echo "----------------------------------------"

  if [ -f "BACKEND-COLLECTOR-SERVICE/app/config.py" ]; then
    QA_CONFIG=$(grep -E "qa_domain_whitelist|qa_min_content_length|qa_expected_keywords" BACKEND-COLLECTOR-SERVICE/app/config.py 2>/dev/null || true)
    if [ -n "$QA_CONFIG" ]; then
      echo -e "${GREEN}✅ Collector QA 설정 구현됨${NC}"
    else
      echo -e "${YELLOW}⚠️  Collector QA 설정 없음${NC}"
      ((WARNINGS++))
    fi
  else
    echo -e "${YELLOW}⚠️  Collector QA 설정 파일 없음${NC}"
    ((WARNINGS++))
  fi

  # 6. 프로젝트 구조 규칙 검사 (.windsurf/rules/project-structure-rules.md)
  echo -e "\n${YELLOW}[6/6] 프로젝트 구조 규칙 검사${NC}"
  echo "----------------------------------------"
  if [ -f ".github/workflows/ci.yml" ]; then
    echo -e "${GREEN}✅ CI/CD 파이프라인 존재${NC}"
  else
    echo -e "${RED}❌ CI/CD 파이프라인 없음${NC}"
    ((ERRORS++))
  fi
REQUIRED_DIRS=("docs" "scripts" "logs" "config" "tests" "data")
for d in "${REQUIRED_DIRS[@]}"; do
  if [ ! -d "$d" ]; then
    echo -e "${YELLOW}⚠️  필수 디렉토리 없음: $d${NC}"
    ((WARNINGS++))
  fi
done

  # 루트 디렉토리 보호: 특정 파일 유형은 전용 디렉토리에만 위치해야 함
  ALLOW_ROOT_FILES=(
    ".gitignore" ".editorconfig" "README.md" "LICENSE" \
    "Makefile" "Makefile.osint" \
    "package.json" "package-lock.json" \
    "docker-compose.yml" "docker-compose.production.yml" \
    "validate_project.sh" "check-health.sh" \
    "requirements-docsync.txt" \
    ".github" ".windsurf" \
    "BACKEND-ABSA-SERVICE" "BACKEND-COLLECTOR-SERVICE" "BACKEND-WEB-COLLECTOR" \
    "FRONTEND-DASHBOARD" "data" "scripts" "docs" \
    "logs" "config" "tests"
  )

# 함수: 루트 허용 여부 판정
is_allowed_root() {
  local item="$1"
  for allowed in "${ALLOW_ROOT_FILES[@]}"; do
    if [ "$item" = "$allowed" ]; then
      return 0
    fi
  done
  return 1
}

  # 루트에 존재하는 파일/폴더 점검 (숨김 제외)
  ROOT_ISSUES=()
  for item in $(ls -A1 | grep -v '^\.' || true); do
  if ! is_allowed_root "$item"; then
    if [[ "$item" == *.md ]]; then
      ROOT_ISSUES+=("문서 파일은 docs/ 하위로 이동 필요: ./$item")
    elif [[ "$item" == *.sh ]]; then
      # 핵심 검증 스크립트 이외는 scripts/ 하위 요구
      if [ "$item" != "validate_project.sh" ] && [ "$item" != "check-health.sh" ]; then
        ROOT_ISSUES+=("스크립트는 scripts/ 하위로 이동 필요: ./$item")
      fi
    elif [[ "$item" == *.log ]]; then
      ROOT_ISSUES+=("로그 파일은 커밋 금지 또는 logs/ + .gitignore 처리 필요: ./$item")
    elif [ -f "$item" ]; then
      ROOT_ISSUES+=("루트 보호 규칙 위반(파일): ./$item → 적절한 디렉토리로 이동 필요")
    fi
  fi
done

if [ ${#ROOT_ISSUES[@]} -gt 0 ]; then
  echo -e "${RED}❌ 루트 디렉토리 보호 규칙 위반 발견:${NC}"
  for msg in "${ROOT_ISSUES[@]}"; do
    echo "- $msg"
  done
  ((WARNINGS++))
else
  echo -e "${GREEN}✅ 루트 디렉토리 보호 규칙 위반 없음${NC}"
fi
# Select python binary
echo -e "\n${YELLOW}[DocSync] 문서 동기화 검증${NC}"
echo "----------------------------------------"
if command -v python3 >/dev/null 2>&1; then
  PYBIN=python3
else
  PYBIN=python
fi

if [ -f "tools/doc_sync/cli.py" ]; then
  if $PYBIN tools/doc_sync/cli.py check --strict; then
    echo -e "${GREEN}✅ DocSync 검증 통과${NC}"
  else
    echo -e "${RED}❌ DocSync 검증 실패: 문서 동기화 누락 또는 메타데이터 문제${NC}"
    ((ERRORS++))
  fi
else
  echo -e "${YELLOW}⚠️  DocSync CLI 미존재: tools/doc_sync/cli.py (검증 건너뜀)${NC}"
  ((WARNINGS++))
fi

# 7. 작업 히스토리 기록 검사
echo -e "\n${YELLOW}[7/7] 작업 히스토리 기록 검사${NC}"
echo "----------------------------------------"

HISTORY_DIR="DOCUMENTS/HISTORY"
if [ -d "$HISTORY_DIR" ]; then
  LATEST_HISTORY=$(ls "${HISTORY_DIR}"/*-history.md 2>/dev/null | sort -r | head -1)
  if [ -z "$LATEST_HISTORY" ]; then
    echo -e "${RED}❌ 히스토리 파일 없음: history-log-prompt.md 규칙 위반${NC}"
    ((ERRORS++))
  else
    LAST_MODIFIED=$(stat -c %Y "$LATEST_HISTORY")
    NOW=$(date +%s)
    AGE_HOURS=$(( (NOW - LAST_MODIFIED) / 3600 ))
    if [ $AGE_HOURS -gt 24 ]; then
      echo -e "${YELLOW}⚠️  최근 24시간 내 히스토리 파일 없음 (${AGE_HOURS}시간 경과)${NC}"
      ((WARNINGS++))
    else
      echo -e "${GREEN}✅ 최근 히스토리 파일: $(basename "$LATEST_HISTORY")${NC}"
    fi
  fi
else
  echo -e "${RED}❌ 히스토리 디렉터리 없음: DOCUMENTS/HISTORY${NC}"
  ((ERRORS++))
fi

# 결과 요약
echo "========================================="
echo -e "${YELLOW}검증 완료${NC}"
echo -e "오류: ${RED}$ERRORS${NC}"
echo -e "경고: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -gt 0 ]; then
    echo -e "\n${RED}❌ 검증 실패: 오류를 수정하세요${NC}"
    exit 1
elif [ "${RULES_ENFORCE_STRICT}" = "true" ] && [ $WARNINGS -gt 0 ]; then
    echo -e "\n${RED}❌ 규칙 위반(엄격 모드): 경고를 오류로 처리합니다${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  경고 있음: 검토 필요 (엄격 모드 비활성)${NC}"
    exit 0
else
    echo -e "\n${GREEN}✅ 모든 검증 통과${NC}"
    exit 0
fi
