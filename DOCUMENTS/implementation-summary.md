# 미구현 기능 요약 (Quick Reference)

## 🎯 우선순위별 작업 (2025-09-30 기준)

### 🔴 HIGH (즉시 착수)

#### 1. Analysis Service - 트렌드 분석 ⏱️ 3일
**상태**: 스켈레톤만 존재  
**필요**: 시계열 집계, 변화율 계산, 키워드 추출  
**담당**: 데이터AI팀  
**블로커**: 없음

#### 2. Analysis Service - 리포트 생성 ⏱️ 4일
**상태**: 미구현  
**필요**: PDF/Excel 출력, 차트 생성, 백그라운드 작업  
**담당**: 데이터AI팀  
**블로커**: 트렌드 분석 완성 필요

#### 3. Frontend - 실시간 대시보드 ⏱️ 5일
**상태**: 샘플 화면만 존재  
**필요**: API 연동, WebSocket, 차트 통합  
**담당**: Frontend팀  
**블로커**: Analysis API 완성 필요

---

### 🟡 MEDIUM (2-3주 내)

#### 4. Collector Service - 품질 검증 ⏱️ 3일
**상태**: 기본 검증만 구현  
**필요**: 품질 점수, 중복 감지, 스팸 필터  
**담당**: 데이터수집팀

#### 5. ABSA Service - 배치 재계산 ⏱️ 3일
**상태**: 단건만 구현  
**필요**: Celery 큐, 스케줄러, 진행 추적  
**담당**: 데이터AI팀

#### 6. OSINT Planning Service ⏱️ 4일
**상태**: 기본 구조만  
**필요**: 계획 알고리즘, Orchestrator 연동  
**담당**: OSINT팀

#### 7. OSINT Source - 크롤러 통합 ⏱️ 5일
**상태**: Mock 감지만  
**필요**: 실제 크롤러 연동, 결과 집계  
**담당**: OSINT팀 + 데이터수집팀

---

### 🟢 LOW (향후)

#### 8. API Gateway - 인증/인가 ⏱️ 3일
**상태**: CORS만 구현  
**필요**: JWT, RBAC, Rate Limiting  
**담당**: Platform팀  
**비고**: 현재 내부망 운영으로 우선순위 낮음

---

## 📅 Sprint 계획

| Sprint | 주차 | 목표 | 작업 |
|--------|------|------|------|
| Sprint 1 | 1-2주 | 핵심 분석 | 트렌드, 리포트, API 클라이언트 |
| Sprint 2 | 3-4주 | 데이터 품질 & UI | 검증, 대시보드, 배치 재계산 |
| Sprint 3 | 5-6주 | OSINT 완성 | Planning, Source 통합 |
| Sprint 4 | 7주+ | 프로덕션 준비 | 인증, 최적화 |

---

## 📊 진행률

| 서비스 | 구현률 | 주요 미구현 |
|--------|--------|------------|
| Alert | 95% | 없음 (완성) |
| Analysis | 80% | 트렌드, 리포트 |
| ABSA | 85% | 배치 재계산 |
| Collector | 85% | 품질 검증 |
| OSINT Orchestrator | 70% | 우선순위 큐 최적화 |
| OSINT Planning | 30% | 대부분 미구현 |
| OSINT Source | 40% | 크롤러 통합 |
| API Gateway | 60% | 인증/인가 |
| Frontend | 40% | 실시간 대시보드 |

**전체 평균**: **67% 완성**

---

## 🚀 빠른 시작

1. **상세 문서 확인**: [implementation-tasks.md](PRD/implementation-tasks.md)
2. **작업 선택**: 우선순위와 팀 배분 확인
3. **코드 리뷰**: 해당 서비스 코드 검토
4. **개발 시작**: TODO 주석 위치에서 구현

---

**문서 위치**: `/DOCUMENTS/PRD/implementation-tasks.md`  
**최종 업데이트**: 2025-09-30
