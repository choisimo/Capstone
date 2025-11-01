# Deployment Command & Environment Inventory (Task 101)

## 1. Current Deployment Entry Points

- **Makefile** – Production helpers wrap `docker compose` for build and deploy via `prod-build` and `prod-deploy`, rebuilding images without cache and recreating services in detached mode.@/home/nodove/workspace/Capstone/Makefile#146-153
- **production-start script** – `scripts/production-start.sh` orchestrates a full compose-based bring-up: checks Docker prerequisites, prepares directories, builds images, starts infrastructure services, waits for readiness, launches microservices/front-end, and performs health checks.@/home/nodove/workspace/Capstone/scripts/production-start.sh#19-133
- **Runbooks** – Linux deployment guide highlights `.env` preparation (`PLATFORM_PROFILE=linux-server`) and running `docker compose --profile linux-server up -d`, providing the operational baseline currently followed by the team.@/home/nodove/workspace/Capstone/DOCUMENTS/DEVELOPMENT/linux-deployment-runbook.md#15-21

## 2. Manual Deployment Flow (As Practiced Today)

1. **SSH to target host** and ensure Docker/Docker Compose availability (validated in `production-start.sh`).@/home/nodove/workspace/Capstone/scripts/production-start.sh#29-42
2. **Prepare environment variables** by copying `.env.example` (or per-service templates) and filling secrets before execution.@/home/nodove/workspace/Capstone/scripts/production-start.sh#19-27 @/home/nodove/workspace/Capstone/.env.example#1-49
3. **Compose-based bring-up** using either manual `docker compose --profile linux-server up -d` or automated helper scripts/Make targets depending on environment.@/home/nodove/workspace/Capstone/DOCUMENTS/DEVELOPMENT/linux-deployment-runbook.md#18-21 @/home/nodove/workspace/Capstone/Makefile#146-153
4. **Post-deploy verification** via health checks/log review (`production-start.sh` triggers checks and prints service endpoints).@/home/nodove/workspace/Capstone/scripts/production-start.sh#103-133
5. **Nginx/Ancillary setup** manually applied per runbook (reverse proxy/TLS steps) when required.@/home/nodove/workspace/Capstone/DOCUMENTS/DEVELOPMENT/linux-deployment-runbook.md#19-21

## 3. Configuration & Secrets Landscape

- Root `.env.example` captures shared infrastructure variables (Postgres, Mongo, JWT, Grafana, CORS) used by compose definitions; identical keys must be provided for production/staging deployments.@/home/nodove/workspace/Capstone/.env.example#22-49
- Service directories also ship `.env.example` templates (API Gateway, Collector, ABSA, Alert, OSINT, Frontend, etc.), indicating per-service overrides that must be consolidated into the new centralized secrets workflow.
- Current automation relies on local files—no GitHub Actions secret consumption yet, so CI/CD-driven deployments need a secure injection strategy (Task 102+103 scope).

## 4. Operational Prerequisites & Assumptions

- Target host must expose Docker + Compose CLIs and possess sufficient privileges for system operations such as `ln` and `systemctl` (implied by helper scripts).@/home/nodove/workspace/Capstone/scripts/production-start.sh#29-98
- Deployment actor requires SSH access and ability to modify `.env`, Compose files, and web server configuration (reverse proxy/TLS per runbook).@/home/nodove/workspace/Capstone/DOCUMENTS/DEVELOPMENT/linux-deployment-runbook.md#15-21
- Monitoring/health tooling invoked by scripts assumes availability of supporting utilities (curl, pytest stacks, etc.).@/home/nodove/workspace/Capstone/scripts/production-start.sh#103-133

## 5. Identified Gaps & Next Steps (Input to Task 102+)

- **Central script missing** – No repository-wide `deploy.sh`; existing flow is split between Make targets, manual compose commands, and `production-start.sh`, motivating the new unified script.
- **Secrets sprawl** – Environment values live in multiple `.env` templates; migrating to GitHub Secrets + runtime injection (HEREDOC/base64) will eliminate plaintext handling on CI nodes.
- **State tracking/manual steps** – Runbooks capture order of operations but do not automate git sync, secrets rotation, or rollback hooks; these become explicit requirements for the forthcoming `deploy.sh` implementation and CI integration.
