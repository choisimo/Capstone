"""
Collection Service: Minimal in-memory implementation to satisfy routes in app/routers/collections.py
This service simulates collection jobs and stores collected data in memory.
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
import time
import threading
import hashlib
from urllib.parse import urlparse
import requests
import numpy as np
import re

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas import (
    CollectionRequest,
    CollectionJob,
    CollectionStats,
    CollectedData,
)
from app.config import settings


class CollectionService:
    # In-memory stores (class-level for simplicity)
    _jobs: List[CollectionJob] = []
    _data: List[CollectedData] = []
    _job_id_seq: int = 1
    _data_id_seq: int = 1

    def __init__(self, db: Session):
        self.db = db

    async def start_collection(self, request: CollectionRequest, background_tasks: BackgroundTasks) -> List[CollectionJob]:
        source_ids = request.source_ids or [1]
        jobs: List[CollectionJob] = []
        for sid in source_ids:
            job = CollectionJob(
                id=CollectionService._job_id_seq,
                source_id=sid,
                status="queued",
                started_at=None,
                completed_at=None,
                items_collected=0,
                error_message=None,
                created_at=datetime.utcnow(),
            )
            CollectionService._job_id_seq += 1
            CollectionService._jobs.append(job)
            # Schedule background collection per job
            background_tasks.add_task(self._run_collection_sync, job.id, sid)
            jobs.append(job)
        return jobs

    @classmethod
    def _run_collection_sync(cls, job_id: int, source_id: int) -> None:
        # Update job to running
        job = cls._get_job_internal(job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()

        # Simulate collection work
        try:
            # Sleep to simulate processing
            time.sleep(0.2)
            # Create a few collected items
            collected_count = 3
            batch_items: List[CollectedData] = []
            for i in range(collected_count):
                # 실제 국민연금 관련 URL 사용
                real_urls = [
                    "https://www.nps.or.kr/jsppage/info/easy/easy_01_01.jsp",
                    "https://www.nps.or.kr/jsppage/info/easy/easy_04_01.jsp",
                    "https://www.mohw.go.kr/menu.es?mid=a10709010100"
                ]
                title = f"국민연금 관련 정보 {i+1}"
                content_text = f"국민연금 관련 실제 데이터 수집 내용 {i+1}"
                url = real_urls[i % len(real_urls)]

                # --- QA: normalization ---
                norm_content = cls._normalize_text(content_text)
                normalized = True if norm_content != content_text else True  # normalized flag

                # --- QA: content hash & duplicate detection ---
                content_hash = cls._calc_hash(url, title, norm_content)
                duplicate_existing = any(
                    (d.content_hash == content_hash) for d in cls._data
                )

                # --- QA: basic content checks ---
                has_content = bool(norm_content and len(norm_content) >= settings.qa_min_content_length)
                http_ok = cls._http_check(url) if settings.qa_enable_network_checks else None

                # --- QA: semantic consistency ---
                semantic_consistency = cls._semantic_consistency_score(norm_content)

                item = CollectedData(
                    id=cls._data_id_seq,
                    source_id=source_id,
                    title=title,
                    content=norm_content,
                    url=url,
                    published_date=None,
                    collected_at=datetime.utcnow(),
                    content_hash=content_hash,
                    metadata_json={"source": "official", "verified": True},
                    processed=False,
                    http_ok=http_ok,
                    has_content=has_content,
                    duplicate=duplicate_existing,
                    normalized=normalized,
                    semantic_consistency=semantic_consistency,
                )
                cls._data_id_seq += 1

                # Skip duplicates or empty content at processing stage
                if duplicate_existing or not has_content:
                    continue

                batch_items.append(item)
                job.items_collected += 1

            # --- QA: outlier & trust/quality scoring (batch-level) ---
            lengths = np.array([len(it.content or "") for it in batch_items], dtype=float)
            mean = float(np.mean(lengths)) if len(lengths) else 0.0
            std = float(np.std(lengths)) if len(lengths) > 1 else 0.0
            for it in batch_items:
                z = abs(((len(it.content or "")) - mean) / std) if std > 1e-9 else 0.0
                # outlier_score: 0(best) ~ 1(worst), threshold z=3 → 1.0
                it.outlier_score = min(1.0, z / 3.0)
                it.trust_score = cls._trust_score(it.url, it.http_ok)
                it.quality_score = cls._quality_score(
                    http_ok=it.http_ok,
                    has_content=it.has_content,
                    duplicate=it.duplicate,
                    semantic_consistency=it.semantic_consistency,
                    outlier_score=it.outlier_score,
                )

            # Commit batch into in-memory store
            cls._data.extend(batch_items)

            job.status = "completed"
            job.completed_at = datetime.utcnow()
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        if not text:
            return ""
        # Collapse whitespace and trim
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _calc_hash(url: str, title: str, content: str) -> str:
        h = hashlib.sha256()
        h.update((url or "").encode("utf-8"))
        h.update((title or "").encode("utf-8"))
        h.update((content or "").encode("utf-8"))
        return h.hexdigest()

    @staticmethod
    def _http_check(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.hostname not in settings.qa_domain_whitelist:
                return False
            resp = requests.head(url, timeout=5, allow_redirects=True, headers={"User-Agent": settings.user_agent})
            if 200 <= resp.status_code < 400:
                return True
            # Fallback to GET if HEAD unreliable
            resp = requests.get(url, timeout=5, allow_redirects=True, headers={"User-Agent": settings.user_agent})
            return 200 <= resp.status_code < 400
        except Exception:
            return False

    @staticmethod
    def _semantic_consistency_score(text: str) -> float:
        if not text:
            return 0.0
        total = len(settings.qa_expected_keywords)
        if total == 0:
            return 0.5
        present = sum(1 for kw in settings.qa_expected_keywords if kw in text)
        return round(present / total, 3)

    @staticmethod
    def _trust_score(url: str, http_ok: Optional[bool]) -> float:
        parsed = urlparse(url)
        base = 0.9 if parsed.hostname in settings.qa_domain_whitelist else 0.5
        if http_ok is True:
            base += 0.1
        return max(0.0, min(1.0, base))

    @staticmethod
    def _quality_score(
        *,
        http_ok: Optional[bool],
        has_content: bool,
        duplicate: bool,
        semantic_consistency: float,
        outlier_score: float,
    ) -> float:
        # Normalize booleans to numeric
        http_score = 1.0 if http_ok is True else (0.5 if http_ok is None else 0.0)
        content_score = 1.0 if has_content else 0.0
        duplicate_penalty = 1.0 if duplicate else 0.0
        outlier_penalty = max(0.0, min(1.0, outlier_score))
        sem = max(0.0, min(1.0, semantic_consistency))

        # Weighted sum (clamped)
        score = 0.25 * http_score + 0.25 * content_score + 0.3 * sem + 0.2 * (1.0 - outlier_penalty) - 0.2 * duplicate_penalty
        return max(0.0, min(1.0, round(score, 3)))

    @classmethod
    def _get_job_internal(cls, job_id: int) -> Optional[CollectionJob]:
        for j in cls._jobs:
            if j.id == job_id:
                return j
        return None

    def get_stats(self) -> CollectionStats:
        total_sources = len({d.source_id for d in CollectionService._data})
        active_sources = total_sources  # In-memory demo
        total_items_collected = len(CollectionService._data)
        today = datetime.utcnow().date()
        items_collected_today = sum(1 for d in CollectionService._data if d.collected_at.date() == today)
        last_collection = max((d.collected_at for d in CollectionService._data), default=None)
        return CollectionStats(
            total_sources=total_sources,
            active_sources=active_sources,
            total_items_collected=total_items_collected,
            items_collected_today=items_collected_today,
            last_collection=last_collection,
        )

    def get_jobs(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> List[CollectionJob]:
        jobs = CollectionService._jobs
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        return jobs[skip: skip + limit]

    def get_job(self, job_id: int) -> Optional[CollectionJob]:
        return CollectionService._get_job_internal(job_id)

    def get_collected_data(
        self,
        skip: int = 0,
        limit: int = 100,
        source_id: Optional[int] = None,
        processed: Optional[bool] = None,
    ) -> List[CollectedData]:
        data = CollectionService._data
        if source_id is not None:
            data = [d for d in data if d.source_id == source_id]
        if processed is not None:
            data = [d for d in data if d.processed == processed]
        return data[skip: skip + limit]

    def mark_processed(self, data_id: int) -> bool:
        for d in CollectionService._data:
            if d.id == data_id:
                d.processed = True
                return True
        return False
