---
description: 코드 리팩토링 규칙 - 기존 파일 직접 수정
---

# 코드 리팩토링 규칙

## 🔧 기본 원칙: 기존 파일 직접 수정

### ❌ 금지된 방식
```bash
# 절대 하지 말 것!
service.py → service_new.py     # ❌ 새 파일 생성 금지
service.py → service_v2.py      # ❌ 버전 파일 생성 금지  
service.py → service_backup.py  # ❌ 백업 파일 생성 금지
```

### ✅ 올바른 방식
```bash
# 반드시 이렇게!
service.py → service.py  # ✅ 기존 파일 직접 수정
```

## 📝 리팩토링 워크플로우

### 1. 기존 코드 확인
```bash
// turbo
# 먼저 현재 코드 상태 확인
cat app/services/absa_service.py
```

### 2. 직접 수정
```python
# Edit 또는 MultiEdit 도구 사용
# 기존 파일을 직접 수정
Edit(
    file_path="/path/to/existing/file.py",
    old_string="현재 코드",
    new_string="수정된 코드"
)
```

### 3. 수정 사항 검증
```bash
// turbo
# 수정 후 파일 확인
cat app/services/absa_service.py
```

## 🚫 절대 금지 사항

### 1. 새 파일 생성 금지
```python
# ❌ 금지
write_to_file("service_new.py", new_code)
write_to_file("service_refactored.py", new_code)
write_to_file("service_v2.py", new_code)

# ✅ 허용
Edit("service.py", old_code, new_code)
```

### 2. 임시 파일 생성 금지
```python
# ❌ 금지
write_to_file("temp_service.py", code)
write_to_file("service.tmp", code)

# ✅ 허용 - 직접 수정만
MultiEdit("service.py", edits=[...])
```

### 3. 백업 파일 생성 금지
```python
# ❌ 금지
shutil.copy("service.py", "service_backup.py")
write_to_file("service.bak", original_code)

# ✅ 허용 - Git이 버전 관리
# Git이 자동으로 이전 버전을 관리함
```

## 🔄 리팩토링 체크리스트

리팩토링 시작 전:
- [ ] 기존 파일 위치 확인
- [ ] 현재 코드 상태 파악
- [ ] 수정 범위 명확히 정의
- [ ] Edit/MultiEdit 도구 준비

리팩토링 중:
- [ ] 기존 파일 직접 수정
- [ ] 새 파일 생성하지 않음
- [ ] 임시 파일 만들지 않음
- [ ] 수정 사항 즉시 적용

리팩토링 후:
- [ ] 수정된 파일 검증
- [ ] 기능 정상 작동 확인
- [ ] 불필요한 파일 없음 확인

## 💡 올바른 리팩토링 예시

### Mock 데이터 제거 리팩토링
```python
# 1. 기존 파일 확인
Read("/app/services/absa_service.py")

# 2. Mock 코드 찾기
# random.choice(['positive', 'negative']) 같은 부분 찾기

# 3. 직접 수정
Edit(
    file_path="/app/services/absa_service.py",
    old_string="sentiment = random.choice(['positive', 'negative'])",
    new_string="sentiment = self.analyze_sentiment(text)"
)

# 4. 절대 하지 말 것
# ❌ write_to_file("/app/services/absa_service_real.py", ...)
```

### 함수 리팩토링
```python
# ✅ 올바른 방법
MultiEdit(
    file_path="/app/services/persona_analyzer.py",
    edits=[
        {
            "old_string": "def get_mock_data():",
            "new_string": "def get_real_data():"
        },
        {
            "old_string": "return fake_data",
            "new_string": "return fetch_from_api()"
        }
    ]
)

# ❌ 잘못된 방법
# write_to_file("persona_analyzer_v2.py", updated_code)
```

## 🛠 도구 사용 가이드

### Read 도구
- 현재 코드 상태 확인용
- 수정 전 필수 실행

### Edit 도구  
- 작은 수정 사항에 사용
- 한 곳만 수정할 때

### MultiEdit 도구
- 여러 곳 동시 수정
- 대규모 리팩토링에 적합
- 한 파일 내 여러 수정 사항

### ❌ write_to_file 도구
- 리팩토링에는 사용 금지
- 새 설정 파일 생성 시에만 사용

## 📌 기억하세요

1. **기존 파일 = 직접 수정**
2. **새 파일 = 생성 금지**
3. **Git = 버전 관리**
4. **Edit/MultiEdit = 리팩토링 도구**

---
**이 규칙을 따르면 깔끔하고 관리하기 쉬운 코드베이스를 유지할 수 있습니다.**
