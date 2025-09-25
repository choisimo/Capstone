---
description: 프로젝트 핵심 규칙 - 반드시 준수
---

# 🔴 프로젝트 핵심 규칙

## 1️⃣ Mock/Fake 데이터 완전 금지

### 절대 금지 사항
```python
# ❌❌❌ 절대 하지 말 것
import random
fake_data = {
    "author": f"user_{random.randint(1, 100)}",  # ❌ 가짜 사용자
    "url": "https://example.com/fake/123",        # ❌ 가짜 URL
    "likes": random.randint(0, 1000),             # ❌ 랜덤 값
    "content": "테스트 내용입니다"                  # ❌ 가짜 내용
}

# ✅✅✅ 반드시 이렇게
real_data = {
    "author": scraped_author,                      # ✅ 실제 수집된 작성자
    "url": verified_url,                          # ✅ 검증된 실제 URL
    "likes": actual_likes_from_api,               # ✅ API에서 받은 실제 값
    "content": actual_scraped_content             # ✅ 실제 스크래핑한 내용
}
```

## 2️⃣ 리팩토링 = 기존 파일 직접 수정

### 절대 금지 사항
```bash
# ❌❌❌ 새 파일 생성 금지
service.py → service_new.py        # ❌
service.py → service_v2.py         # ❌
service.py → service_refactored.py # ❌
service.py → service2.py           # ❌
service.py → service_real.py       # ❌
```

### 반드시 이렇게
```bash
# ✅✅✅ 기존 파일 직접 수정
service.py → service.py  # ✅ Edit/MultiEdit 사용
```

## 3️⃣ 실제 데이터 소스만 사용

### 허용된 데이터 소스
1. **공식 웹사이트**
   - 국민연금공단: https://www.nps.or.kr
   - 보건복지부: https://www.mohw.go.kr
   - 국민연금연구원: https://institute.nps.or.kr

2. **뉴스 사이트**
   - 주요 언론사 공식 사이트
   - RSS 피드
   - 공개 API

3. **커뮤니티 사이트**
   - 실제 게시판 URL
   - 검증 가능한 링크
   - robots.txt 준수

## 4️⃣ 코드 수정 워크플로우

### Step 1: 기존 코드 확인
```python
# 항상 먼저 읽기
Read("/path/to/existing/file.py")
```

### Step 2: 직접 수정
```python
# Edit 또는 MultiEdit 사용
Edit(
    file_path="/path/to/existing/file.py",  # 기존 파일
    old_string="mock_data = generate_fake()",
    new_string="real_data = fetch_from_api()"
)
```

### Step 3: 새 파일 생성 금지
```python
# ❌ 절대 금지
write_to_file("new_version.py", code)

# ✅ 허용 - 설정 파일만
write_to_file(".env", config)  # 설정 파일은 OK
write_to_file("config.json", settings)  # 설정 파일은 OK
```

## 5️⃣ 데이터 검증 필수

### 모든 데이터 검증
```python
def validate_before_use(data):
    # 1. URL 검증
    if not data.get('url', '').startswith(('http://', 'https://')):
        raise ValueError("Invalid URL")
    
    # 2. 실제 존재 확인
    if not verify_url_exists(data['url']):
        raise ValueError("URL does not exist")
    
    # 3. 필수 필드 확인
    required = ['url', 'source', 'collected_at']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing field: {field}")
    
    return True
```

## 6️⃣ 금지 패턴 감지

### 감지 시 즉시 수정
```python
# 금지 패턴 발견 시
forbidden_patterns = [
    "random.choice",
    "random.randint", 
    "faker.",
    "mock_",
    "fake_",
    "dummy_",
    "test_data",
    "sample_data"
]

# 발견되면 즉시 제거하고 실제 구현으로 교체
```

## 7️⃣ 파일명 규칙

### 금지된 파일명
```
❌ *_new.py
❌ *_v2.py
❌ *_backup.py
❌ *_old.py
❌ *_temp.py
❌ *_test.py (테스트 파일 제외)
❌ *_mock.py
❌ *_fake.py
```

### 허용된 파일명
```
✅ service.py
✅ analyzer.py
✅ collector.py
✅ config.py
✅ test_*.py (테스트 파일만)
```

## 8️⃣ 주석 규칙

### Mock 관련 주석 제거
```python
# ❌ 제거해야 할 주석
# TODO: Replace with real data
# FIXME: This is mock data
# NOTE: Temporary fake implementation

# ✅ 올바른 주석
# Fetches real data from API
# Validates actual URL
# Processes scraped content
```

## 9️⃣ Import 규칙

### 금지된 Import
```python
# ❌ 제거
import random  # Mock 데이터용
from faker import Faker
from unittest.mock import Mock
```

### 허용된 Import
```python
# ✅ 실제 데이터 처리용
import requests  # API 호출
import feedparser  # RSS 파싱
from bs4 import BeautifulSoup  # 웹 스크래핑
```

## 🔟 검증 명령어

### 프로젝트 검증
```bash
// turbo
# Mock 패턴 검색
grep -r "random\." --include="*.py" .
grep -r "mock" --include="*.py" .
grep -r "fake" --include="*.py" .

# 중복 파일 확인
find . -name "*_new.py" -o -name "*_v2.py"
```

---

## ⚠️ 위반 시 조치

1. **즉시 중단** - Mock 데이터 생성 중단
2. **코드 삭제** - 가짜 데이터 관련 코드 제거
3. **파일 정리** - 중복 파일 삭제
4. **실제 구현** - 실제 데이터 소스로 대체

---

## 📌 항상 기억하세요

> **"Real Data Only, Direct Modification Only"**
> 
> - 실제 데이터만 사용
> - 기존 파일 직접 수정
> - 검증 가능한 소스만
> - Mock/Fake 완전 금지

---

**이 규칙은 예외 없이 항상 적용됩니다.**
