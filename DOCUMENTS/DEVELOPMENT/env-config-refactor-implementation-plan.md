# 환경 변수/비밀 관리 통합 구현 계획서 (개정판)

본 문서는 `tasks-refactor-envmanage.json`의 P1 거버넌스 표준(@DOCUMENTS/DEVELOPMENT/environment-governance-p1.md)과 코드베이스 현황을 바탕으로 Consul 기반 환경 변수 및 비밀 관리를 서비스 전반에 적용하기 위한 구현 계획을 정리한다. 본 개정판은 코드 리뷰 결과를 반영하여 키/네임스페이스 규약, 공통 로더 인터페이스, 보안/운영 기준, 테스트/마이그레이션 절차를 구체화한다.

## 1. 코드베이스 현황 요약

| 서비스                                                  | 설정 로딩 패턴                             | 주요 문제점                                 |
| ------------------------------------------------------- | ------------------------------------------ | ------------------------------------------- |
| API Gateway @BACKEND-API-GATEWAY/app/config.py#1-68     | `BaseSettings` 사용, 기본값 다수         | Consul 미사용, dotenv 우선                  |
| Collector @BACKEND-COLLECTOR-SERVICE/app/config.py#1-45 | `BaseSettings` + `os.getenv` 혼용      | Consul hook 없음, 기본값에 민감 정보 가능성 |
| Analysis @BACKEND-ANALYSIS-SERVICE/app/config.py#1-54   | `BaseSettings`, `SECRET_KEY` 하드코딩  | Consul/KV 분리 미적용                       |
| Alert @BACKEND-ALERT-SERVICE/app/config.py#1-210        | `BaseSettings`이나 기본값/빈 문자열 다수 | 자격증명 기본값 빈 문자열                   |
| ABSA @BACKEND-ABSA-SERVICE/app/config.py#1-53           | 단순 클래스 +`os.getenv`                 | 타입 검증 부재                              |
| OSINT Orchestrator/Planning/Source                      | 단순 클래스/수동 `__init__`              | 기본값/시크릿 내장                          |

## 2. 목표 상태 요건

1. 모든 서비스 설정은 Consul KV(`config/<service>/<env>/...`, `secrets/<service>/<env>/...`)를 1차 소스로 사용한다. `.env`는 로컬 개발 보조 용도로만 사용하며 민감값을 포함하지 않는다.
2. `shared/`에 공통 설정 로더 모듈을 추가하여 Consul 클라이언트/캐싱/폴백 로직을 일원화한다.
3. Jenkins 파이프라인에서 `init-consul-kv.sh` 및 배포 단계의 KV 동기화 스텝을 호출, 서비스 기동 시 최신 값을 보장한다.
4. 민감 정보는 `secrets` 네임스페이스에서만 조회하고, 애플리케이션 로그에는 마스킹된 형태로만 노출한다.

### 2.1 키스페이스/키 규약(명확화)

- 키 프리픽스: 환경 구분 포함
  - 구성: `config/<service>/<env>/configs/<key>`
  - 시크릿: `secrets/<service>/<env>/<key>`
- 예시(API Gateway, dev)
  - `config/api-gateway/dev/configs/rate_limit_per_minute = 100`
  - `config/api-gateway/dev/configs/rate_limit_redis_url = "redis://redis:6379/0"`
  - `secrets/api-gateway/dev/jwt_secret_key = "***"`
- 타입 규칙
  - 스칼라: 문자열로 저장, 로더에서 타입 캐스팅(int/bool/float)
  - 리스트/맵: JSON 문자열로 저장 후 로더가 `List/Dict`로 역직렬화
  - 미지정/누락: 폴백 정책(2.2) 적용

### 2.2 최소 환경 변수와 .env 정책(구체화)

- 허용 환경변수(최소):
  - `CONSUL_HTTP_ADDR`(예: `https://consul.local:8501`)
  - `CONSUL_HTTP_TOKEN`(런타임 토큰)
  - `CONSUL_HTTP_SSL_VERIFY`(`true|false`, 기본 true)
  - `CONSUL_KV_PREFIX`(옵션, 기본 빈 값)
  - `ENVIRONMENT`(`development|staging|production`)
- 파일 정책:
  - `.env.consul`: 위 5개 항목만 허용(민감 애플리케이션 시크릿 금지)
  - 레거시 `.env`는 제거 대상으로 분류하고, 개발/테스트에서 필요한 비민감 설정만 유지

## 3. 단계별 구현 로드맵

### Phase A: 기반 인프라 및 SDK 준비 (1주)

1. Consul 접속 SDK
   - `shared/consul_client.py` 신규: 주소/토큰/TLS/네임스페이스, 재시도/백오프, 타임아웃, 간단 캐시 제공
   - `shared/config_loader.py` 신규: Consul→Pydantic Settings 바인딩 팩토리, 타입 변환(JSON→List/Dict), 부분 실패 시 폴백
2. 로컬 개발 지원(실자산 경로 지정)
   - 개발용 Consul Compose: `config/compose/consul.dev.yml`
   - Make 타겟: `make consul-dev-up`, `make consul-dev-down`
   - `.env.example` 정리: Consul 접속 정보만 남기고 민감값 제거, `.env.consul.example` 제공
3. 테스트 유틸
   - pytest fixture: 로컬 Consul 에이전트 또는 Mock 클라이언트
   - 공통 로더 단위테스트용 fake KV 데이터셋 제공

### Phase B: 서비스별 설정 리팩터 (2~3주)

- 공통 원칙
  1) `BaseSettings` + `SettingsConfigDict`로 통일, 필드 타입 명시, 민감 기본값 제거
  2) `load_settings(service_name)`를 통해 초기화, Consul 우선 로드
  3) 비밀은 `SecretStr` 또는 lazy getter 사용, 로그 마스킹 필수
  4) `/health` 응답에 `config_sync_timestamp` 포함(부록 B 참고)
- 변경 순서(권장): API Gateway → Collector → Analysis → Alert → ABSA → OSINT*
- 서비스별 보강 사항
  - API Gateway: RateLimit/Redis를 `configs`로, JWT 키를 `secrets`로 이전
  - Collector: `qa_domain_whitelist` 등 리스트형은 JSON 배열로 저장→로더 역직렬화
  - Analysis: 하드코딩된 `SECRET_KEY` 제거→`secrets/analysis/<env>/secret_key`
  - Alert: SMTP/Slack/Twilio 자격증명은 모두 `secrets`로, 템플릿 콘텐츠는 Git 유지
  - ABSA: 클래스→`BaseSettings` 전환, Consul 연동, 모델 파라미터는 `configs`
  - OSINT 계열: `OsintSettingsMixin`(shared)로 공통 필드/검증/로딩 절차 통합

### Phase C: 파이프라인/운영 통합 (2주)

1. Jenkins Shared Library: `consul.withCredentials {}` 및 공통 스텝
2. 배포 스텝:
   - `scripts/init-consul-kv.sh --env=$ENV --service=$SERVICE`(dry-run→apply)
   - 배포 완료 시 `config/<service>/<env>/configs/deployment_id` 갱신
3. 롤백: 이전 KV 스냅샷 복구/검증 스텝
4. 관측성: 설정 버전/동기화 타임스탬프를 매트릭으로 노출

## 4. 서비스별 상세 작업 항목(보완)

- `/health` 스키마 표준화(부록 B): 최소 필드 `status, service, config_sync_timestamp, environment`
- 로그 마스킹 정책: 키 이름에 `SECRET|TOKEN|PASSWORD` 포함시 값 마스킹 처리
- 예외/부족 데이터 처리: 필수 키 누락 시 사용자 친화적 메시지와 가이드 링크 반환

## 5. Consul KV Seed & 마이그레이션 전략(보강)

1. Seed 경로: `infra/consul/seeds/<env>/<service>.hcl`
2. 변환 스크립트(I/O 정의)
   - 도구: `scripts/env_to_consul_hcl.py`
   - 입력: 기존 `.env`(K=V) 또는 YAML(JSON) 설정 파일
   - 출력: HCL 파일(키스페이스 규약 적용), 검증 리포트(JSON)
   - 샘플 실행: `python scripts/env_to_consul_hcl.py --service api-gateway --env dev --in .env --out infra/consul/seeds/dev/api-gateway.hcl`
3. 체크리스트(확장)
   - 민감 키는 `secrets`로 이동했는가
   - Jenkins Credential Store ↔ Consul secrets 정합성(이름, 스코프)
   - 리스트/맵(JSON) 직렬화/역직렬화 OK
   - 서비스 재기동 시 Consul 값 적용 확인(`/health.config_sync_timestamp` 갱신)

## 6. 테스트 및 검증 계획(구체화)

1. 단위 테스트
   - `ConfigLoader`에 대한 타입 캐스팅, JSON 역직렬화, 폴백 순서 검증
   - 재시도/백오프 동작, 부분 실패(일부 키 누락) 처리 시나리오
2. 통합 테스트
   - 사전조건: `docker compose -f config/compose/consul.dev.yml up -d`
   - KV seed 주입 후 서비스 기동→`/health`에서 `config_sync_timestamp` 확인
   - 기존 스크립트(`tests/test_integration_enhanced.py`) 확장: Consul 연결/설정 버전 검증 케이스 추가
3. 파이프라인 검증
   - Jenkins stage에서 `init-consul-kv.sh` dry-run → main 파이프라인 적용
   - 실패 시 롤백 스크립트 및 알림 채널 검증
4. 장애/롤백 시나리오
   - 토큰 만료/네트워크 분리 시 폴백 동작, 재시도 backoff, 캐시 유효성 확인

## 7. 리스크 및 대응(보안 기준 포함)

| 리스크                        | 영향             | 대응                                               |
| ----------------------------- | ---------------- | -------------------------------------------------- |
| Consul 장애 시 설정 로드 실패 | 서비스 기동 실패 | 초기 부트 캐시/폴백, 재시도 Backoff                |
| 민감 데이터 Git 유출          | 치명적           | secrets Git 금지, seed placeholder, Vault 검토     |
| Jenkins 토큰 누출             | 높음             | 마스킹, 단기 수명 토큰, 접근 로그/회전 주기        |
| TLS 미검증                    | 중간             | `CONSUL_HTTP_SSL_VERIFY=true` 기본, 사설 CA 배포 |
| 개발자 학습 곡선              | 중간             | 가이드/워크샵, Consul UI 활용                      |

## 8. 일정 및 마일스톤 제안

| 주차 | 주요 산출물                                                         |
| ---- | ------------------------------------------------------------------- |
| W1   | Shared Consul SDK,`config/compose/consul.dev.yml`, Seed 구조 초안 |
| W2   | API Gateway/Collector 리팩터, Seed 머지                             |
| W3   | Analysis/Alert/ABSA 리팩터, 테스트 보강                             |
| W4   | OSINT 계열 리팩터, Jenkins 파이프라인 통합                          |
| W5   | 종합 통합 테스트, 문서/교육 자료 완료                               |

## 9. 후속 작업

1. Terraform/Helm으로 Consul ACL/정책 IaC
2. Vault 연동 PoC(Consul secrets → Vault KV)
3. MkDocs 자동화(P5)에서 Consul 구조 기반 환경 문서 생성

---

## 부록 A. 공통 로더 인터페이스 명세(초안)

- 함수: `load_settings(service: str, env: Optional[str] = None, *, require: Optional[list[str]] = None) -> BaseSettings`
- 내부 동작
  1) 환경 해석: `env` 인자→`ENVIRONMENT`→기본 `development`
  2) 로드 순서(폴백): Consul(KV 우선) → 프로세스 env → `.env.consul` → 안전 기본값
  3) 타입 변환: `int|bool|float` 캐스팅, JSON 문자열→`List/Dict`
  4) 캐시: 프로세스 내 TTL 캐시(기본 60초), 강제 리프레시 옵션
  5) 재시도: 지수 백오프(예: 0.5s, 1s, 2s... 최대 5회)
  6) 마스킹: 로그 출력 시 `*SECRET*|*TOKEN*|*PASSWORD*` 키는 값 마스킹
- 에러 처리
  - `require` 키 목록이 누락되면 예외 발생과 함께 누락 키/가이드 메시지 제공
  - Consul 접속 실패 시 폴백 경로로 지속, 최종 실패 시 명시적 예외

## 부록 B. 헬스 응답 스키마(초안)

- 경로: `/health`
- 응답(JSON)

```
{
  "status": "ok|degraded|fail",
  "service": "<service-name>",
  "environment": "development|staging|production",
  "config_sync_timestamp": "2025-11-02T12:34:56Z",
  "dependencies": {"postgres": "ok|fail", "redis": "ok|fail"}
}
```

- 노출 금지: 시크릿 값/토큰 직접 노출 금지
