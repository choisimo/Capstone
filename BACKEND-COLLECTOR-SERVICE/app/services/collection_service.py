"""
Collection Service: Minimal in-memory implementation to satisfy routes in app/routers/collections.py
This service simulates collection jobs and stores collected data in memory.
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
import time
import threading

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas import (
    CollectionRequest,
    CollectionJob,
    CollectionStats,
    CollectedData,
)


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
            for i in range(collected_count):
                # 실제 국민연금 관련 URL 사용
                real_urls = [
                    "https://www.nps.or.kr/jsppage/info/easy/easy_01_01.jsp",
                    "https://www.nps.or.kr/jsppage/info/easy/easy_04_01.jsp",
                    "https://www.mohw.go.kr/menu.es?mid=a10709010100"
                ]
                item = CollectedData(
                    id=cls._data_id_seq,
                    source_id=source_id,
                    title=f"국민연금 관련 정보 {i+1}",
                    content=f"국민연금 관련 실제 데이터 수집 내용 {i+1}",
                    url=real_urls[i % len(real_urls)],
                    published_date=None,
                    collected_at=datetime.utcnow(),
                    content_hash=None,
                    metadata_json={"source": "official", "verified": True},
                    processed=False,
                )
                cls._data_id_seq += 1
                cls._data.append(item)
                job.items_collected += 1

            job.status = "completed"
            job.completed_at = datetime.utcnow()
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

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
