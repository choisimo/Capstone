---
description: Mock 데이터 생성 금지 및 실제 데이터만 사용 정책
---

# Mock 데이터 생성 금지 정책

## 🚫 절대 금지 사항

### 1. Mock/Fake 데이터 생성 금지
- **NEVER** create mock data with fake URLs
- **NEVER** generate random test data
- **NEVER** create dummy content for testing
- **NEVER** make up user names, posts, or comments
- **NEVER** fabricate URLs that don't actually exist

### 2. 가짜 URL 생성 금지
```python
# ❌ 금지 - 가짜 URL
url = "https://gall.dcinside.com/board/view/?id=stock&no=1234567"  # 실제로 존재하지 않는 URL

# ✅ 허용 - 실제 존재하는 URL만
url = "https://gall.dcinside.com/board/lists?id=stock_new1"  # 실제 갤러리 목록 페이지
```

### 3. 랜덤 데이터 생성 금지
```python
# ❌ 금지
import random
sentiment = random.choice(['positive', 'negative'])
likes = random.randint(0, 1000)

# ✅ 허용 - 실제 분석 결과만
sentiment = analyze_real_text(actual_content)
likes = fetch_from_api(post_id)
```

## ✅ 허용된 데이터 소스

### 1. 공식 API
- 국민연금공단 RSS
- 보건복지부 RSS  
- 공개된 REST API (인증 불필요)

### 2. 실제 웹사이트
- 직접 스크래핑 (robots.txt 준수)
- 실제 존재하는 URL만 사용
- 수집한 데이터는 원본 URL과 함께 저장

### 3. 검증된 데이터셋
- 정부 공공데이터 포털
- 연구기관 공개 데이터
- 라이센스가 명확한 오픈 데이터

## 📋 데이터 수집 체크리스트

수집 전 확인:
- [ ] URL이 실제로 존재하는가?
- [ ] 데이터 소스가 신뢰할 수 있는가?
- [ ] 원본 링크를 추적할 수 있는가?
- [ ] 저작권/라이센스 문제가 없는가?
- [ ] robots.txt를 준수하는가?

## 🔍 검증 방법

### 1. URL 검증
```python
def verify_url(url):
    """URL이 실제 존재하는지 검증"""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except:
        return False

# 사용 전 항상 검증
if verify_url(url):
    # 데이터 수집 진행
    pass
else:
    # 수집 중단
    raise ValueError(f"Invalid URL: {url}")
```

### 2. 데이터 검증
```python
def validate_data(data):
    """수집된 데이터 검증"""
    required_fields = ['url', 'source', 'collected_at']
    
    for field in required_fields:
        if field not in data:
            return False
    
    # URL이 http/https로 시작하는지 확인
    if not data['url'].startswith(('http://', 'https://')):
        return False
    
    return True
```

## 💡 대안 접근법

Mock 데이터가 필요한 경우:
1. **실제 데이터 샘플 사용**: 공개된 실제 데이터의 일부를 샘플로 사용
2. **익명화된 실제 데이터**: 개인정보를 제거한 실제 데이터 사용
3. **공개 데이터셋**: 연구용으로 공개된 데이터셋 활용
4. **시뮬레이션 명시**: 불가피하게 시뮬레이션 데이터를 사용할 경우, 명확히 표시

## 🚨 위반 시 조치

Mock 데이터 생성 발견 시:
1. 즉시 해당 코드 삭제
2. 실제 데이터 소스로 대체
3. 데이터 출처 명확히 기록
4. 검증 가능한 URL/소스 제공

---
**이 정책은 프로젝트의 신뢰성과 데이터 무결성을 위해 반드시 준수되어야 합니다.**
