---
description: 코드 변경 후 문서 동기화 워크플로우
---

# 📚 Documentation Sync Workflow - 코드-문서 동기화 규칙

## 🎯 목적
모든 코드 변경 작업 완료 후, 관련 문서를 자동으로 검토하고 최신화하여 코드와 문서의 일관성 유지

## ⚡ 트리거 조건
- 서비스 코드 변경 완료
- API 엔드포인트 추가/수정
- 데이터 모델 변경
- 설정 파일 업데이트
- 새로운 의존성 추가

## 📋 실행 절차

### 1단계: 변경 사항 스캔
```bash
# 최근 변경된 파일 목록 확인
git diff --name-only HEAD~1

# 변경 타입 분류
- *.py → 서비스 로직
- */schemas.py, */models.py → 데이터 모델
- */routers/*.py → API 엔드포인트
- requirements.txt, package.json → 의존성
- docker-compose*.yml → 인프라
```

### 2단계: 영향받는 문서 식별
```
변경 파일 → 관련 문서 매핑:
- BACKEND-*/app/main.py → DOCUMENTS/SERVICES/{service-name}.md
- */schemas.py → DOCUMENTS/CONTRACTS/{service}-api.md
- */models.py → DOCUMENTS/ARCHITECTURE/data-models.md
- docker-compose*.yml → DOCUMENTS/ARCHITECTURE/deployment.md
- BACKEND-CRAWLER/* → DOCUMENTS/SERVICES/crawler-services.md
```

### 3단계: 문서 검증 체크리스트
```markdown
□ API 엔드포인트 정의가 실제 코드와 일치하는가?
□ 데이터 스키마가 최신 상태인가?
□ 환경 변수와 설정이 문서화되어 있는가?
□ 의존성 버전이 명시되어 있는가?
□ 에러 코드와 응답 형식이 일치하는가?
□ 인증/권한 요구사항이 정확한가?
```

### 4단계: 문서 업데이트
```python
# 업데이트 필요 항목:
1. API 명세 (경로, 메서드, 파라미터)
2. Request/Response 스키마
3. 에러 코드 및 메시지
4. 환경 변수 및 설정
5. 의존성 및 버전
6. 배포 구성
7. 테스트 시나리오
```

### 5단계: 검증 및 커밋
```bash
# 문서 린트 체크
markdownlint DOCUMENTS/**/*.md

# 링크 유효성 검증
find DOCUMENTS -name "*.md" -exec grep -l "http" {} \; | xargs -I {} linkcheck {}

# 커밋 메시지 형식
git commit -m "docs: sync {service} documentation with code changes

- Updated API endpoints
- Fixed schema definitions
- Added new environment variables
- Aligned with commit {hash}"
```

## 🔍 자동화 도구

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: doc-sync-check
      name: Check documentation sync
      entry: ./scripts/check-doc-sync.sh
      language: script
      files: '\.(py|yml|yaml|json)$'
```

### GitHub Actions
```yaml
name: Documentation Sync Check
on: [pull_request]
jobs:
  doc-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check documentation
        run: |
          ./scripts/validate-docs.sh
          ./scripts/check-api-consistency.sh
```

## 📊 문서 상태 추적

### 문서 메타데이터 헤더
```markdown
---
last_sync: 2025-09-26
last_code_commit: abc123def
verified_endpoints: 15/15
schema_version: 1.2.0
status: synced | outdated | needs_review
---
```

### 동기화 상태 대시보드
```
SERVICE           | CODE_VERSION | DOC_VERSION | STATUS
------------------|--------------|-------------|--------
collector-service | v1.2.3       | v1.2.3      | ✅ Synced
crawler-service   | v2.0.1       | v1.9.0      | ⚠️  Outdated
absa-service      | v1.5.0       | v1.5.0      | ✅ Synced
```

## 🚨 위반 시 조치

### 레벨 1: 경고
- 문서와 코드 불일치 감지
- PR 코멘트로 알림

### 레벨 2: 차단
- CI/CD 파이프라인 중단
- 문서 업데이트 요구

### 레벨 3: 롤백
- 문서 없는 기능 자동 비활성화
- 이전 버전으로 복구

## 🎯 KPI

- **문서 커버리지**: 95% 이상
- **동기화 지연**: 24시간 이내
- **불일치 감지율**: 100%
- **자동 수정률**: 70% 이상

## 📝 예외 사항

### 문서 업데이트 불필요한 경우
- 내부 리팩토링 (인터페이스 변경 없음)
- 테스트 코드 수정
- 주석/로깅 개선
- 성능 최적화 (동작 변경 없음)

### 특별 검토 필요
- Breaking Changes
- 보안 관련 변경
- 데이터 마이그레이션
- 외부 API 연동 변경

## 🔄 주기적 검토

### 주간 검토
```bash
# 매주 월요일 실행
./scripts/weekly-doc-audit.sh
```

### 월간 전체 검증
```bash
# 매월 첫째 주 실행
./scripts/full-doc-validation.sh
```

---

**이 워크플로우는 코드의 신뢰성과 문서의 정확성을 보장합니다.**
**모든 팀원은 이 규칙을 준수해야 합니다.**
