---
description: 실제 데이터 수집 워크플로우
---

# 실제 데이터 수집 워크플로우

## 📊 데이터 수집 프로세스

### Step 1: 데이터 소스 확인
```bash
// turbo
# 1. 공식 사이트 확인
curl -I https://www.nps.or.kr  # 국민연금공단
curl -I https://www.mohw.go.kr  # 보건복지부
```

### Step 2: URL 검증
```python
# 수집 전 URL이 실제 존재하는지 확인
import requests

def verify_url_exists(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except:
        return False

# 검증 후 수집
if verify_url_exists(url):
    # 수집 진행
    pass
```

### Step 3: 실제 데이터 수집
```python
# RSS 피드 수집 예시
import feedparser

# 실제 RSS URL만 사용
rss_urls = [
    "https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp",  # 국민연금공단
    "https://www.mohw.go.kr/rss/news.xml"  # 보건복지부
]

for url in rss_urls:
    if verify_url_exists(url):
        feed = feedparser.parse(url)
        # 실제 데이터 처리
```

### Step 4: 데이터 검증
```python
def validate_collected_data(data):
    """수집된 데이터 검증"""
    # 필수 필드 확인
    required = ['url', 'source', 'title', 'collected_at']
    
    for field in required:
        if field not in data or not data[field]:
            return False
    
    # URL 형식 확인
    if not data['url'].startswith(('http://', 'https://')):
        return False
    
    # 실제 URL인지 재확인
    if not verify_url_exists(data['url']):
        return False
    
    return True
```

### Step 5: 데이터 저장
```python
# 검증된 데이터만 저장
validated_data = []

for item in collected_data:
    if validate_collected_data(item):
        validated_data.append(item)
    else:
        print(f"Invalid data rejected: {item.get('url', 'unknown')}")

# 저장 시 메타데이터 포함
save_data = {
    "metadata": {
        "source": "real_websites",
        "collected_at": datetime.now().isoformat(),
        "total_items": len(validated_data),
        "all_urls_verified": True
    },
    "data": validated_data
}
```

## 🚫 하지 말아야 할 것

### 1. 가짜 URL 생성
```python
# ❌ 절대 금지
fake_url = f"https://example.com/post/{random.randint(1000, 9999)}"
```

### 2. Mock 데이터 생성
```python
# ❌ 절대 금지
mock_comment = {
    "author": f"user_{random.randint(1, 100)}",
    "content": "테스트 댓글입니다",
    "url": "https://fake-site.com/comment/123"
}
```

### 3. 랜덤 값 생성
```python
# ❌ 절대 금지
likes = random.randint(0, 1000)
views = random.randint(100, 10000)
```

## ✅ 올바른 데이터 소스

### 1. 공식 API
- 국민연금공단 공개 API
- 공공데이터포털 API
- 정부 부처 RSS 피드

### 2. 실제 웹페이지
- robots.txt 준수
- 과도한 요청 금지
- User-Agent 명시

### 3. 공개 데이터셋
- 정부 공공데이터
- 연구기관 데이터
- 오픈 라이센스 데이터

## 📝 데이터 수집 템플릿

```python
class RealDataCollector:
    """실제 데이터만 수집하는 클래스"""
    
    def __init__(self):
        self.verified_sources = [
            "https://www.nps.or.kr",
            "https://www.mohw.go.kr",
            # 검증된 소스만 추가
        ]
    
    def collect(self, source_url):
        # 1. URL 검증
        if not self.verify_url(source_url):
            raise ValueError(f"Invalid URL: {source_url}")
        
        # 2. 데이터 수집
        data = self.fetch_data(source_url)
        
        # 3. 데이터 검증
        if not self.validate_data(data):
            raise ValueError(f"Invalid data from: {source_url}")
        
        # 4. 원본 URL 포함하여 저장
        data['original_url'] = source_url
        data['verified'] = True
        data['collected_at'] = datetime.now().isoformat()
        
        return data
    
    def verify_url(self, url):
        """URL이 실제 존재하는지 확인"""
        # 실제 HTTP 요청으로 확인
        pass
    
    def fetch_data(self, url):
        """실제 데이터 가져오기"""
        # 실제 웹사이트에서 스크래핑
        pass
    
    def validate_data(self, data):
        """데이터 유효성 검증"""
        # 필수 필드, 형식 등 확인
        pass
```

## 🔍 검증 체크리스트

데이터 수집 전:
- [ ] URL이 실제로 존재하는가?
- [ ] robots.txt를 확인했는가?
- [ ] API 사용 약관을 확인했는가?

데이터 수집 중:
- [ ] 실제 응답을 받았는가?
- [ ] 데이터 형식이 올바른가?
- [ ] 원본 URL을 기록했는가?

데이터 수집 후:
- [ ] 모든 URL이 검증되었는가?
- [ ] 메타데이터를 포함했는가?
- [ ] 저장 형식이 올바른가?

## 💡 트러블슈팅

### 403 Forbidden 오류
```python
# User-Agent 추가
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; DataCollector/1.0)'
}
response = requests.get(url, headers=headers)
```

### 속도 제한
```python
# 요청 간 대기 시간 추가
import time

for url in urls:
    data = collect(url)
    time.sleep(1)  # 1초 대기
```

### SSL 인증서 오류
```python
# 신뢰할 수 있는 사이트만
response = requests.get(url, verify=True)
```

---
**실제 데이터만 수집하여 프로젝트의 신뢰성을 보장합니다.**
