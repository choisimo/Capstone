# 실제 데이터 소스 목록

## ✅ 검증된 실제 URL 목록

### 1. 공식 기관
- **국민연금공단**: https://www.nps.or.kr
  - 연금제도 안내: https://www.nps.or.kr/jsppage/info/easy/easy_01_01.jsp
  - 보험료 안내: https://www.nps.or.kr/jsppage/info/easy/easy_04_01.jsp
  - 급여 종류: https://www.nps.or.kr/jsppage/info/easy/easy_05_01.jsp
  - RSS 피드: https://www.nps.or.kr/jsppage/cyber_pr/news/rss.jsp

- **보건복지부**: https://www.mohw.go.kr
  - 연금정책: https://www.mohw.go.kr/menu.es?mid=a10709010100
  - RSS 피드: https://www.mohw.go.kr/rss/news.xml

- **국민연금연구원**: https://institute.nps.or.kr
  - 연구보고서: https://institute.nps.or.kr/jsppage/research/resources/resources_01.jsp

### 2. 뉴스 검색
- **네이버 뉴스 검색**: https://search.naver.com/search.naver?where=news&query=국민연금
- **다음 뉴스 검색**: https://search.daum.net/search?w=news&q=국민연금

### 3. 커뮤니티 사이트 (실제 존재 확인)
- **디시인사이드 갤러리**
  - 주식갤러리: https://gall.dcinside.com/board/lists?id=stock_new1
  - 경제갤러리: https://gall.dcinside.com/board/lists?id=economy
  - 부동산갤러리: https://gall.dcinside.com/board/lists?id=immovables

- **기타 커뮤니티**
  - 에펨코리아: https://www.fmkorea.com
  - 클리앙: https://www.clien.net
  - 뽐뿌: https://www.ppomppu.co.kr
  - 보배드림: https://www.bobaedream.co.kr
  - MLB파크: https://mlbpark.donga.com

## ❌ 제거된 가짜/Mock 데이터

### 삭제된 파일
- `gemini_client_v2.py`
- `scrapegraph_adapter_v2.py`
- `change_detection_v2.py`
- `test_gemini_client_v2.py`
- `collect_extended_korean_data.py` (mock 생성 스크립트)
- `collect_korean_data.py` (mock 생성 스크립트)

### 수정된 내용
1. **BACKEND-COLLECTOR-SERVICE**
   - `source_service.py`: 하드코딩된 데모 URL → 실제 국민연금/보건복지부 URL
   - `collection_service.py`: example.com → 실제 국민연금 페이지 URL

2. **BACKEND-ALERT-SERVICE**
   - `schemas.py`: test_data → validation_data
   - `rule_service.py`: sample_data → validation_data

3. **BACKEND-WEB-COLLECTOR**
   - 테스트 파일들의 example.com, test.com → nps.or.kr

## 🔍 데이터 검증 프로세스

### URL 검증 함수
```python
def verify_url_exists(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except:
        return False
```

### 데이터 검증 체크리스트
- [ ] URL이 http:// 또는 https://로 시작
- [ ] URL 실존 확인 (HEAD 요청)
- [ ] 원본 링크 저장
- [ ] 수집 시간 기록
- [ ] Mock 패턴 없음 확인

## 📌 중요 규칙

1. **절대 금지**
   - random 모듈 사용
   - faker 라이브러리
   - 가짜 URL 생성
   - Mock 데이터 생성

2. **항상 필수**
   - URL 검증
   - 실제 소스만 사용
   - 원본 링크 추적
   - 검증된 데이터만 저장

---
마지막 업데이트: 2025-09-26
