# GCP 배포·운영 런북

## 1. 사전 준비
- 프로젝트: `org/pension-sentiment-{dev,stage,prod}`
- 네트워크: VPC, 서브넷, NAT, Cloud DNS, Cloud Armor 정책
- 보안: Secret Manager, KMS 키, IAM 롤 정의, Workload Identity

## 2. IaC(Terraform) 구성
- 모듈: network, gke, cloudrun, iam, gcs, bigquery, pubsub, secret, monitoring
- 파라미터: 리전, 노드풀, 오토스케일, 버킷 수명주기, BQ 파티션/클러스터, 라우팅 규칙
- 파이프라인: GitHub Actions → Terraform Cloud/`terraform apply` with WIF

## 3. CI/CD
- 빌드: Cloud Build 또는 GitHub Actions(Docker buildx, SBOM, cosign 서명)
- 배포: GKE(ArgoCD) 또는 Cloud Run(리비전 별 롤아웃), Canary 10→50→100
- 시크릿 주입: Secret Manager → CSI Driver(GKE) 또는 Runtime Env(Cloud Run)

## 4. 서비스 배포 순서
1) 인프라(IaC) 적용 → 네트워크/보안/관측성
2) 데이터 스토어: BQ 테이블/스키마, GCS 버킷, Pub/Sub 토픽
3) 런타임: GKE 클러스터/네임스페이스, ArgoCD, OTel Collector, Ingress
4) 백엔드: API Gateway/BFF, 분석 서비스 서빙(Deployment)
5) 파이프라인: Composer DAG 배포, 잡 스케줄
6) 프론트엔드: Next.js → Cloud Run + Cloud CDN/Load Balancer
7) 알림: Functions/Run 연결, Slack/Webhook 설정

## 5. 운영 체크리스트
- 관측성: 대시보드/경보 세트 활성화, 로그 샘플링 규칙
- 보안: WAF 룰, 서비스 계정 키 금지, CIS GKE 벤치마크 베이스라인
- 데이터 품질: GE 리포트 자동화, DLP 샘플 검사, 드리프트 경고

## 6. 재해 복구/백업
- GCS 버전관리, BQ 스냅샷, 구성 백업(ArgoCD GitOps), 비상 롤백 플레이북

## 7. 비용 최적화
- (GCP) Autoscaling/Autopilot, BQ BI Engine 예약, Cloud Run min instances=0, Vertex 엔드포인트 Autoscale, LLM 캐시/샘플링
- (Linux 서버) Compose 프로필로 선택적 기동, ClickHouse 머지트리 튜닝, Nginx 캐시 TTL, LLM 호출 샘플링/캐시

## 8. 보안 사고 대응
- IAM 변경 감지 알림, Cloud Armor 차단 룰 단계적 적용, 이상 트래픽 조사, 데이터 접근 감사

## 9. 릴리즈 기준
- 스테이지 환경 Lighthouse/시나리오 테스트 통과, 예산 경보/대시보드 적용 확인, 롤백 시나리오 리허설 완료
