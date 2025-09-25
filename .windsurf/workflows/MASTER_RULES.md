---
description: 마스터 규칙 - 모든 작업에 최우선 적용
---

# 🚨 MASTER RULES - 절대 준수 사항

## 🔴 규칙 1: NO MOCK DATA - 가짜 데이터 절대 금지

### ❌ 즉시 중단해야 할 코드
```python
# 발견 즉시 삭제
import random
from faker import Faker
from unittest.mock import Mock

# 절대 금지 패턴
fake_url = "https://example.com/post/123"  # ❌
mock_user = f"user_{random.randint(1,100)}"  # ❌
test_data = generate_dummy_data()  # ❌
sample_comment = "테스트 댓글입니다"  # ❌
```

### ✅ 유일하게 허용되는 방식
```python
# 실제 소스에서만
real_url = "https://www.nps.or.kr/jsppage/info/easy/easy_01_01.jsp"  # ✅
real_data = fetch_from_actual_api()  # ✅
verified_content = scrape_real_website()  # ✅
```

## 🔴 규칙 2: DIRECT MODIFICATION ONLY - 직접 수정만

### ❌ 절대 금지 - 새 파일 생성
```bash
# 이런 파일명 절대 금지
service_new.py      # ❌
service_v2.py       # ❌
service_real.py     # ❌
service_updated.py  # ❌
service2.py         # ❌
service_backup.py   # ❌
```

### ✅ 유일한 방법 - 기존 파일 수정
```python
# Edit/MultiEdit만 사용
Edit(
    file_path="/existing/file.py",  # 기존 파일
    old_string="수정 전",
    new_string="수정 후"
)
```

## 🔴 규칙 3: VERIFY BEFORE USE - 사용 전 검증

### 모든 데이터 검증 필수
```python
def must_verify(data):
    # 1. URL 실존 확인
    assert verify_url_exists(data['url'])
    
    # 2. 필수 필드 확인
    assert 'source' in data
    assert 'collected_at' in data
    
    # 3. Mock 패턴 없음 확인
    assert 'mock' not in str(data)
    assert 'fake' not in str(data)
    assert 'test' not in str(data)
    
    return True
```

## 🟡 워크플로우 순서

### 코드 수정 시
1. **READ** → 기존 코드 확인
2. **SEARCH** → Mock 패턴 검색
3. **EDIT** → 직접 수정
4. **VERIFY** → 수정 확인
5. **TEST** → 실제 동작 테스트

### 데이터 수집 시
1. **VERIFY URL** → URL 실존 확인
2. **COLLECT** → 실제 데이터 수집
3. **VALIDATE** → 데이터 검증
4. **SAVE** → 원본 URL과 함께 저장

## 🟡 즉시 조치 사항

### Mock 코드 발견 시
```bash
# 1. 찾기
grep -r "random\." --include="*.py"
grep -r "mock" --include="*.py"
grep -r "fake" --include="*.py"

# 2. 제거
# Edit 도구로 즉시 수정

# 3. 확인
# 다시 검색하여 완전 제거 확인
```

### 중복 파일 발견 시
```bash
# 1. 찾기
find . -name "*_new.py" -o -name "*_v2.py"

# 2. 삭제
rm -f *_new.py *_v2.py

# 3. 원본만 유지
ls -la *.py
```

## 📌 Quick Reference

### 🚫 BANNED WORDS
```
mock, fake, dummy, sample, test_data, 
random, example, demo, temp, placeholder
```

### 🚫 BANNED PATTERNS
```python
random.*
faker.*
Mock()
"test"
"example.com"
uuid.uuid4()  # for fake IDs
```

### 🚫 BANNED FILES
```
*_new.py
*_v2.py
*_backup.py
*_temp.py
*_old.py
```

### ✅ REQUIRED CHECKS
```python
□ URL exists?
□ Data verified?
□ No mock patterns?
□ Direct modification?
□ Original file only?
```

## 🔥 ENFORCEMENT

### 위반 발견 시
1. **STOP** - 즉시 중단
2. **DELETE** - 위반 코드 삭제
3. **FIX** - 올바른 방식으로 수정
4. **VERIFY** - 규칙 준수 확인

### 검증 명령
```bash
// turbo
# 전체 프로젝트 검증
./validate_project.sh

# Mock 패턴 검색
grep -r "random\|mock\|fake" --include="*.py" .

# 중복 파일 검색
find . -regex ".*_\(new\|v2\|backup\|old\)\.py$"
```

---

# ⚡ ONE-LINE RULE

> **"REAL DATA ONLY, ORIGINAL FILES ONLY, VERIFY EVERYTHING"**

---

**이 규칙을 위반하면 프로젝트 신뢰도가 0이 됩니다.**
**예외는 없습니다. 항상 적용됩니다.**
