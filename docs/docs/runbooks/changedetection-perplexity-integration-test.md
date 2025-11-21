# Changedetection + Perplexity + 커뮤니티 감지 통합 테스트 가이드

## 개요

- **목적**: changedetection 기반 웹 모니터링, Perplexity AI 검색, 커뮤니티 감지 기능의 통합 동작을 검증
- **대상 서비스**: analysis-service, changedetection, Perplexity API
- **테스트 소요 시간**: 약 15-20분

## 테스트 전제 조건

- Docker 및 Docker Compose 설치
- Perplexity API 키 보유
- Changedetection API 키 (선택사항)
- 충분한 디스크 공간 (최소 5GB)

---

## 1. 환경 기동

### 1.1 환경 변수 설정

`infra/.env` 파일에 필수 API 키 입력:

```bash
# API Keys
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxx
CHANGEDETECTION_API_KEY=your-api-key-here  # 선택사항

# 기타 필요한 환경 변수들은 .env.example 참조
```

### 1.2 Docker Compose 기동

```bash
cd /home/nodove/workspace/Capstone
docker compose --env-file infra/.env -f docker-compose.spring.yml up --build -d
```

### 1.3 초기화 작업 확인

다음 init 컨테이너들이 정상 종료되었는지 확인:

```bash
docker ps -a | grep -E '(consul-kv-init|changedetection-seed)'
```

**기대 결과**:

- `consul-kv-init` → `Exited (0)`
- `changedetection-seed` → `Exited (0)`

**오류 시 대응**:

```bash
# 로그 확인
docker logs consul-kv-init
docker logs changedetection-seed

# 재실행이 필요한 경우
docker compose --env-file infra/.env -f docker-compose.spring.yml up consul-kv-init changedetection-seed
```

### 1.4 서비스 헬스체크

모든 주요 서비스가 healthy 상태인지 확인:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E '(analysis|changedetection|postgres|consul)'
```

---

## 2. Changedetection 초기 데이터 확인

### 2.1 Web UI 접속

브라우저로 `http://localhost:5000` 접속

### 2.2 Watch 목록 확인

- 좌측 메뉴에서 "Watch List" 클릭
- **기대 결과**:
  - 총 35개의 watch가 등록되어 있어야 함
  - 태그: `news`, `community` 등이 표시됨

### 2.3 Watch 구성 검증

다음 카테고리의 watch들이 존재하는지 확인:

| 카테고리 | 예시 사이트                   | 태그            |
| -------- | ----------------------------- | --------------- |
| 뉴스     | 연합뉴스, 한겨레, 중앙일보 등 | `[news]`      |
| 커뮤니티 | 클리앙, 보배드림, 루리웹 등   | `[community]` |

### 2.4 스냅샷 수집 확인

- 임의의 watch 선택 → "History" 탭 클릭
- 최소 1개 이상의 스냅샷이 수집되었는지 확인
- **주의**: 초기 수집은 5-10분 소요될 수 있음

---

## 3. Agent 검색 검증

### 3.1 테스트 케이스 1: 통합 정책 분석

#### 3.1.1 API 호출 (curl)

```bash
curl -X POST http://localhost:8080/api/explore \
  -H "Content-Type: application/json" \
  -d '{
    "query": "청년 연금 정책과 관련된 최신 기사·커뮤니티 반응을 분석해 줘."
  }'
```

#### 3.1.2 프론트엔드 테스트

- 대시보드 접속: `http://localhost:3000/explore`
- 검색창에 입력: `청년 연금 정책과 관련된 최신 기사·커뮤니티 반응을 분석해 줘.`
- "검색" 버튼 클릭

#### 3.1.3 응답 검증

**기대 결과**:

```json
{
  "response": "청년 연금 정책에 대한 Perplexity AI 요약 텍스트...",
  "sources": [
    {
      "type": "news",
      "title": "[news] 연합뉴스 - 청년 연금 개편안 발표",
      "url": "https://www.yna.co.kr/...",
      "snippet": "스냅샷 내용..."
    },
    {
      "type": "community",
      "title": "[community] 클리앙 - 청년연금 논의 스레드",
      "url": "https://www.clien.net/...",
      "snippet": "커뮤니티 반응..."
    }
  ],
  "metadata": {
    "sources_count": 10,
    "query_time": "2025-11-19T10:30:00Z"
  }
}
```

**검증 포인트**:

- ✅ `response` 필드에 Perplexity 요약 포함
- ✅ `sources` 배열에 `[news]`, `[community]` 태그가 붙은 여러 출처 포함
- ✅ changedetection에서 가져온 스냅샷이 포함되어 있음
- ✅ URL과 snippet이 올바르게 파싱됨

### 3.2 테스트 케이스 2: URL 기반 크롤링 검증

#### 3.2.1 API 호출

```bash
curl -X POST http://localhost:8080/api/explore \
  -H "Content-Type: application/json" \
  -d '{
    "query": "https://www.yna.co.kr/view/AKR20250115000100001 이 기사의 주요 내용과 여론 반응을 요약해 줘."
  }'
```

#### 3.2.2 응답 검증

**기대 결과**:

- Crawl4ai를 통한 실시간 크롤링 결과 포함
- 해당 URL의 본문 내용이 분석에 포함됨
- changedetection 스냅샷과 Crawl4ai 결과가 함께 활용됨

**검증 포인트**:

- ✅ URL이 감지되고 Crawl4ai가 호출됨
- ✅ 크롤링된 콘텐츠가 분석에 활용됨
- ✅ Perplexity API와 함께 통합된 응답 제공

### 3.3 테스트 케이스 3: 커뮤니티 중심 검색

#### 3.3.1 API 호출

```bash
curl -X POST http://localhost:8080/api/explore \
  -H "Content-Type: application/json" \
  -d '{
    "query": "청년 일자리 정책에 대한 온라인 커뮤니티 반응은 어때?"
  }'
```

#### 3.3.2 응답 검증

**기대 결과**:

- `[community]` 태그가 붙은 출처가 우선적으로 포함
- 클리앙, 보배드림, 루리웹 등의 스냅샷 포함

---

## 4. 로그 및 에러 체크

### 4.1 Analysis Service 로그 확인

```bash
docker logs analysis-service-spring --tail=100 -f
```

**체크 포인트**:

- ✅ Perplexity API 호출 성공 로그 확인
- ✅ changedetection API 호출 성공 로그 확인
- ✅ 응답 파싱 및 통합 성공 로그 확인
- ❌ 에러 스택 트레이스가 없어야 함
- ❌ `401 Unauthorized` 또는 `403 Forbidden` 에러 없음

**주요 로그 패턴**:

```
INFO  - Calling Perplexity API with query: 청년 연금 정책...
INFO  - Perplexity API response received: 200 OK
INFO  - Fetching changedetection snapshots for tags: [news, community]
INFO  - Retrieved 15 snapshots from changedetection
INFO  - Merged sources: 15 total (10 news, 5 community)
```

### 4.2 Changedetection 서비스 로그 확인

```bash
docker logs changedetection --tail=100 -f
```

**체크 포인트**:

- ✅ Watch 갱신 작업이 주기적으로 실행됨
- ✅ 스냅샷 생성 성공 로그 확인
- ❌ 크롤링 실패 에러가 과도하게 발생하지 않음 (일부 사이트는 정상)

### 4.3 Changedetection Web UI에서 History 갱신 확인

1. `http://localhost:5000` 접속
2. 임의의 watch 선택 (예: "연합뉴스 청년정책")
3. "History" 탭 클릭
4. **기대 결과**: 최근 5-10분 내에 새로운 스냅샷이 추가됨

---

## 5. 통합 검증 시나리오

### 5.1 End-to-End 워크플로우

다음 단계를 순서대로 실행하여 전체 파이프라인을 검증:

1. **데이터 수집**:

   - changedetection이 주기적으로 35개 사이트 모니터링
   - 변경 감지 시 스냅샷 생성
2. **검색 요청**:

   - 프론트엔드에서 "청년 연금 정책" 검색
3. **Agent 처리**:

   - Perplexity API로 최신 정보 검색
   - changedetection에서 관련 스냅샷 조회
   - Crawl4ai로 URL 기반 콘텐츠 추출 (필요 시)
4. **결과 통합**:

   - 모든 출처를 통합하여 `sources` 배열 구성
   - Perplexity 요약과 함께 응답
5. **프론트엔드 표시**:

   - 요약 텍스트와 출처 목록 표시
   - 사용자가 출처 클릭 시 원본 URL로 이동

### 5.2 성능 검증

- **응답 시간**: 5초 이내
- **동시 요청**: 3개 이상 처리 가능
- **메모리 사용량**: analysis-service < 2GB

---

## 6. 트러블슈팅

### 6.1 Perplexity API 에러

**증상**: `401 Unauthorized`
**원인**: API 키가 올바르지 않음
**해결**:

```bash
# infra/.env 파일 확인
cat infra/.env | grep PERPLEXITY_API_KEY

# 환경 변수 재설정 후 재시작
docker compose --env-file infra/.env -f docker-compose.spring.yml restart analysis-service-spring
```

### 6.2 Changedetection 스냅샷 미수집

**증상**: sources 배열이 비어 있음
**원인**: watch가 아직 실행되지 않았거나 크롤링 실패
**해결**:

```bash
# changedetection 로그 확인
docker logs changedetection --tail=50

# 수동으로 watch 실행 (Web UI)
# http://localhost:5000 → Watch 선택 → "Run" 버튼 클릭
```

### 6.3 서비스 응답 없음

**증상**: curl 요청이 timeout
**원인**: 서비스가 시작되지 않았거나 네트워크 문제
**해결**:

```bash
# 서비스 상태 확인
docker ps | grep analysis-service-spring

# 헬스체크 확인
curl http://localhost:8080/actuator/health

# 재시작
docker compose --env-file infra/.env -f docker-compose.spring.yml restart analysis-service-spring
```

### 6.4 출처에 `[news]`, `[community]` 태그가 없음

**증상**: sources의 title에 태그가 표시되지 않음
**원인**: changedetection seed 스크립트가 실행되지 않음
**해결**:

```bash
# seed 컨테이너 재실행
docker compose --env-file infra/.env -f docker-compose.spring.yml up changedetection-seed

# changedetection Web UI에서 태그 수동 추가
```

---

## 7. 검증 완료 체크리스트

테스트 완료 후 다음 항목을 확인:

- [ ] changedetection에 35개 watch 등록 확인
- [ ] `[news]`, `[community]` 태그 존재 확인
- [ ] 스냅샷이 주기적으로 수집됨 확인
- [ ] Agent 검색 시 Perplexity 요약 포함
- [ ] sources 배열에 여러 출처 포함
- [ ] URL 기반 검색 시 Crawl4ai 동작 확인
- [ ] 로그에 에러 없음
- [ ] 응답 시간 5초 이내
- [ ] 프론트엔드에서 결과 정상 표시

---

## 8. 테스트 결과 보고

테스트 완료 후 다음 정보를 포함하여 보고:

### 8.1 환경 정보

- 테스트 일시:
- Docker 버전:
- OS:

### 8.2 테스트 결과

| 테스트 케이스               | 결과    | 비고 |
| --------------------------- | ------- | ---- |
| 환경 기동                   | ✅ / ❌ |      |
| Changedetection 초기 데이터 | ✅ / ❌ |      |
| 통합 정책 분석 검색         | ✅ / ❌ |      |
| URL 기반 크롤링             | ✅ / ❌ |      |
| 커뮤니티 중심 검색          | ✅ / ❌ |      |
| 로그 에러 체크              | ✅ / ❌ |      |

### 8.3 발견된 이슈

- 이슈 1: [설명]
- 이슈 2: [설명]

### 8.4 개선 제안

- 제안 1: [설명]
- 제안 2: [설명]

---

## 9. 참고 문서

- [Changedetection 공식 문서](https://changedetection.io/docs/)
- [Perplexity API 문서](https://docs.perplexity.ai/)
- [Analysis Service 상세 스펙](./analysis-service.md)
- [환경 설정 가이드](../../DEVELOPMENT/development-guide.md)

---

## 10. 자주 묻는 질문 (FAQ)

**Q1: changedetection seed가 실패합니다.**
A: `init-scripts/changedetection/seed-watches.sh` 스크립트를 확인하고, changedetection 서비스가 완전히 기동된 후 실행되는지 확인하세요.

**Q2: Perplexity API 할당량을 초과했습니다.**
A: 무료 티어는 제한이 있습니다. 테스트 시 요청 횟수를 제한하거나 유료 플랜을 고려하세요.

**Q3: 특정 사이트의 스냅샷이 수집되지 않습니다.**
A: 일부 사이트는 anti-scraping 정책이 있을 수 있습니다. changedetection Web UI에서 해당 watch의 로그를 확인하고, 필요 시 User-Agent 또는 헤더를 조정하세요.

**Q4: 프론트엔드에서 결과가 표시되지 않습니다.**
A: 브라우저 개발자 도구(F12)에서 Network 탭을 확인하여 API 요청이 성공했는지, CORS 에러가 없는지 확인하세요.
