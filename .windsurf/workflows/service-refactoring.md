---
description: 서비스 코드 리팩토링 가이드
---

# 서비스 코드 리팩토링 가이드

## 📋 리팩토링 전 체크리스트

### 1. 현재 서비스 파일 확인
```bash
// turbo
# ABSA Service 확인
ls -la BACKEND-ABSA-SERVICE/app/services/

# 파일 내용 확인
cat BACKEND-ABSA-SERVICE/app/services/absa_service.py
```

### 2. Mock 데이터 패턴 검색
```bash
// turbo
# Mock 패턴 찾기
grep -n "random" BACKEND-ABSA-SERVICE/app/services/*.py
grep -n "mock" BACKEND-ABSA-SERVICE/app/services/*.py
grep -n "fake" BACKEND-ABSA-SERVICE/app/services/*.py
```

## 🔧 Mock 데이터 제거 리팩토링

### ABSA Service 리팩토링 예시

#### Step 1: 현재 코드 확인
```python
# Read 도구 사용
Read("/home/nodove/workspace/Capstone/BACKEND-ABSA-SERVICE/app/services/absa_service.py")
```

#### Step 2: Mock 코드 식별
```python
# 찾아야 할 패턴들:
# - random.choice()
# - random.randint()
# - 하드코딩된 가짜 데이터
# - 임시 구현 (_get_random_* 함수들)
```

#### Step 3: 직접 수정 (새 파일 생성 금지!)
```python
# ❌ 절대 하지 말 것
write_to_file("absa_service_real.py", new_code)  # 금지!

# ✅ 반드시 이렇게
Edit(
    file_path="/home/nodove/workspace/Capstone/BACKEND-ABSA-SERVICE/app/services/absa_service.py",
    old_string="""def _get_random_sentiment(self) -> str:
        sentiments = ["positive", "negative", "neutral"]
        return random.choice(sentiments)""",
    new_string="""def _analyze_sentiment(self, text: str) -> str:
        # 실제 감성 사전 기반 분석
        score = self._calculate_sentiment_score(text)
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        else:
            return "neutral" """
)
```

## 📁 각 서비스별 리팩토링 포인트

### 1. BACKEND-ABSA-SERVICE
```python
# 확인할 파일
/app/services/absa_service.py
/app/services/persona_analyzer.py

# 제거할 것
- random 모듈 사용
- _get_random_* 함수들
- 하드코딩된 테스트 데이터

# 대체할 것
- 실제 감성 사전
- 실제 분석 로직
- DB에서 가져온 실제 데이터
```

### 2. BACKEND-COLLECTOR-SERVICE
```python
# 확인할 파일
/app/services/source_service.py
/app/services/collection_service.py

# 제거할 것
- 하드코딩된 데모 소스
- uuid로 생성한 가짜 ID
- 샘플 URL

# 대체할 것
- 실제 RSS 피드
- 실제 웹사이트 URL
- API 응답 데이터
```

### 3. BACKEND-ALERT-SERVICE
```python
# 확인할 파일
/app/services/alert_service.py
/app/services/notification_service.py

# 수정할 것
- 정적 메서드 패턴 일관성
- 실제 알림 전송 로직
```

## 🛠 리팩토링 도구 사용법

### Edit 도구 (단일 수정)
```python
Edit(
    file_path="/absolute/path/to/file.py",
    old_string="찾을 코드",
    new_string="바꿀 코드"
)
```

### MultiEdit 도구 (다중 수정)
```python
MultiEdit(
    file_path="/absolute/path/to/file.py",
    edits=[
        {"old_string": "mock_1", "new_string": "real_1"},
        {"old_string": "mock_2", "new_string": "real_2"},
        {"old_string": "mock_3", "new_string": "real_3"}
    ]
)
```

## 📝 리팩토링 후 검증

### 1. Mock 패턴 재검색
```bash
// turbo
# 제거 확인
grep -n "random\." BACKEND-*/app/services/*.py
# 결과가 없어야 함
```

### 2. 서비스 테스트
```bash
// turbo
# 수정된 서비스 테스트
curl http://localhost:8003/health
curl -X POST http://localhost:8003/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "실제 텍스트", "aspects": ["수익률"]}'
```

### 3. 로그 확인
```bash
// turbo
# 에러 로그 확인
docker logs absa-service --tail 50
```

## ⚠️ 주의사항

### 절대 하지 말 것
1. `_new.py` 파일 생성
2. `_v2.py` 파일 생성  
3. 백업 파일 생성
4. 임시 파일 생성

### 반드시 할 것
1. 기존 파일 직접 수정
2. Git으로 버전 관리
3. 실제 데이터로 교체
4. 검증 로직 추가

## 📊 진행 상황 추적

### 완료된 리팩토링
- [x] ABSA Service - Mock 데이터 제거 (persona_analyzer.py 제외)
- [ ] Collector Service - 하드코딩 소스 제거
- [ ] Alert Service - 정적 메서드 수정
- [ ] Analysis Service - Mock 응답 제거

### 다음 작업
1. 각 서비스 파일 검토
2. Mock 패턴 제거
3. 실제 구현으로 교체
4. 통합 테스트

---

**Remember: No new files, only direct modifications!**
