import asyncio
import json
import uvicorn
from fastapi import FastAPI, Response
from app.config import settings
from app.routers import tasks
from app.routers import dashboard
from shared.eureka_client import create_manager_from_settings
import httpx
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
try:
    import redis.asyncio as aioredis
    from redis.exceptions import ResponseError
except Exception:
    aioredis = None
    ResponseError = Exception
try:
    import asyncpg
except Exception:
    asyncpg = None

app = FastAPI(
    title="OSINT Task Orchestrator Service",
    description="Orchestrates OSINT tasks with priority-based queue management and worker coordination",
    version="1.0.0"
)

eureka_manager = create_manager_from_settings(
    enabled=settings.EUREKA_ENABLED,
    service_urls=settings.EUREKA_SERVICE_URLS,
    app_name=settings.EUREKA_APP_NAME,
    instance_port=settings.PORT,
    instance_host=settings.EUREKA_INSTANCE_HOST,
    instance_ip=settings.EUREKA_INSTANCE_IP,
    metadata=settings.EUREKA_METADATA,
)

app.include_router(tasks.router)
app.include_router(dashboard.router)

STREAM_NAME = "orchestrator:events"
GROUP_NAME = "orchestrator-consumers"
CONSUMER_NAME = "orchestrator-main"

EVENT_COUNTER = Counter("orchestrator_events_total", "Total events consumed", ["event_type"])
TASKS_COMPLETED = Counter("orchestrator_tasks_completed_total", "Total tasks completed")
TASKS_FAILED = Counter("orchestrator_tasks_failed_total", "Total tasks failed")
WORKERS_REGISTERED = Counter("orchestrator_workers_registered_total", "Total workers registered")

async def _ensure_group(client):
    try:
        await client.xgroup_create(name=STREAM_NAME, groupname=GROUP_NAME, id="$", mkstream=True)
    except ResponseError as e:
        # Group already exists
        if "BUSYGROUP" in str(e):
            return
        # Stream might be missing; ensure mkstream handled, else ignore
        if "NOGROUP" in str(e) or "NO such key" in str(e):
            return
        raise

async def _init_audit():
    if not settings.DATABASE_URL or not asyncpg:
        return None
    pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orchestrator_audit_logs (
              id BIGSERIAL PRIMARY KEY,
              event_type TEXT NOT NULL,
              stream_id TEXT,
              occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              payload JSONB
            );
            """
        )
    return pool

async def _write_audit(pool, event_type: str, entry_id: str, timestamp_str: str, payload: dict):
    if not pool:
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO orchestrator_audit_logs(event_type, stream_id, occurred_at, payload) VALUES($1, $2, COALESCE(to_timestamp(NULLIF($3,'') , 'YYYY-MM-DD""T""HH24:MI:SS.MS""Z""'), NOW()), $4)",
                event_type,
                entry_id,
                timestamp_str or "",
                json.dumps(payload),
            )
    except Exception:
        # 감사 로그 기록 실패는 서비스 동작에 영향 주지 않음
        pass

async def _consume_events():
    if not settings.REDIS_URL or not aioredis:
        # Redis 미설정 또는 의존성 없음: 소비자 비활성화
        return
    client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await _ensure_group(client)
    audit_pool = await _init_audit()
    http_timeout = httpx.Timeout(10.0)
    http_client = httpx.AsyncClient(timeout=http_timeout)
    try:
        while True:
            try:
                messages = await client.xreadgroup(
                    groupname=GROUP_NAME,
                    consumername=CONSUMER_NAME,
                    streams={STREAM_NAME: ">"},
                    count=50,
                    block=5000,
                )
            except Exception:
                # 일시적 오류 발생 시 짧게 대기 후 재시도
                await asyncio.sleep(1.0)
                continue

            if not messages:
                continue

            for stream, entries in messages:
                for entry_id, fields in entries:
                    try:
                        payload = fields.get("payload")
                        event_type = fields.get("event_type", "unknown")
                        ts = fields.get("timestamp")
                        data = json.loads(payload) if payload else {}
                        # 메트릭
                        EVENT_COUNTER.labels(event_type=event_type).inc()
                        if event_type == "task.updated":
                            new_status = str(data.get("new_status", "")).lower()
                            if new_status == "failed":
                                TASKS_FAILED.inc()
                            if new_status == "completed":
                                TASKS_COMPLETED.inc()
                        elif event_type == "worker.registered":
                            WORKERS_REGISTERED.inc()

                        # 감사 로그 기록
                        await _write_audit(audit_pool, event_type, entry_id, ts or "", data)

                        # 이벤트 라우팅: 알림 생성 (조건부)
                        should_alert = False
                        alert_severity = "high"
                        alert_title = None
                        alert_message = None
                        source_data_id = None

                        # 1) task_failed: task.updated + new_status == failed
                        if event_type == "task.updated" and str(data.get("new_status", "")).lower() == "failed":
                            should_alert = True
                            alert_severity = "high"
                            alert_title = "작업 실패 감지"
                            source_data_id = data.get("task_id")
                            err = data.get("error_message") or "작업 실패"
                            alert_message = f"Task {source_data_id} failed: {err}"

                        # 2) critical_error 이벤트
                        if event_type == "critical_error":
                            should_alert = True
                            alert_severity = "critical"
                            alert_title = data.get("title") or "치명적 오류 발생"
                            source_data_id = data.get("task_id") or data.get("worker_id")
                            alert_message = data.get("message") or json.dumps(data, ensure_ascii=False)

                        if should_alert:
                            rule_id = None
                            try:
                                rule_id_env = getattr(settings, "SYSTEM_ALERT_RULE_ID", None)
                            except Exception:
                                rule_id_env = None
                            if rule_id_env:
                                rule_id = int(rule_id_env)
                            # rule_id 없는 경우, Alert Service와의 계약상 생성 불가할 수 있어 건너뜀
                            if rule_id:
                                try:
                                    alert_url_base = getattr(settings, "ALERT_SERVICE_URL", None) or "http://alert-service:8004"
                                    alert_url = f"{alert_url_base.rstrip('/')}/alerts"
                                    body = {
                                        "rule_id": rule_id,
                                        "severity": alert_severity,
                                        "title": alert_title,
                                        "message": alert_message,
                                        "source_service": "osint-orchestrator",
                                        "source_data_id": source_data_id,
                                        "triggered_data": data,
                                    }
                                    resp = await http_client.post(alert_url, json=body)
                                    if resp.status_code >= 300:
                                        print(f"Alert create failed: status={resp.status_code} body={resp.text}")
                                except Exception as e:
                                    print(f"Alert create error: {e}")

                        # 로그
                        print(f"Event consumed: type={event_type} id={entry_id} ts={ts}")
                    except Exception as e:
                        print(f"Event consume error id={entry_id}: {e}")
                    finally:
                        try:
                            await client.xack(STREAM_NAME, GROUP_NAME, entry_id)
                        except Exception:
                            # ack 실패는 다음 루프에서 pending 처리 가능
                            pass
    finally:
        try:
            await client.aclose()
        except Exception:
            pass
        try:
            await http_client.aclose()
        except Exception:
            pass
        if audit_pool:
            try:
                await audit_pool.close()
            except Exception:
                pass

@app.on_event("startup")
async def on_startup():
    # 백그라운드 소비자 태스크 시작
    app.state.consumer_task = asyncio.create_task(_consume_events())
    await eureka_manager.register()


@app.on_event("shutdown")
async def on_shutdown():
    # 백그라운드 소비자 태스크 정리
    task = getattr(app.state, "consumer_task", None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
    await eureka_manager.deregister()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "osint-task-orchestrator"}

@app.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)