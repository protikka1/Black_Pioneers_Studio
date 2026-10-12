from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from threading import Lock, RLock
from typing import Callable
from uuid import uuid4

from .models import RenderJob


RenderTask = Callable[[Callable[[float], None]], Path]


class RenderJobManager:
    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = Lock()
        self._workspace_lock = RLock()
        self._jobs: dict[str, RenderJob] = {}
        self._futures: dict[str, Future[None]] = {}
        self._request_keys: dict[str, str] = {}
        self._job_request_keys: dict[str, str] = {}

    @contextmanager
    def prepare_workspace(self):
        """Keep cleanup out while uploads are being prepared and queued."""
        with self._workspace_lock:
            yield

    def has_active_jobs(self) -> bool:
        with self._lock:
            return any(job.status in {"queued", "running"} for job in self._jobs.values())

    def clean_workspace_if_idle(self, cleanup: Callable[[], None]) -> bool:
        with self._workspace_lock:
            if self.has_active_jobs():
                return False
            cleanup()
            return True

    def create_job(self, pioneer_id: int) -> RenderJob:
        job = RenderJob(
            job_id=uuid4().hex,
            pioneer_id=pioneer_id,
            status="queued",
            progress=0.0,
            output_path=None,
            error_message=None,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def run_render_job(
        self,
        pioneer_id: int,
        task: RenderTask,
        *,
        request_key: str | None = None,
    ) -> RenderJob:
        with self._workspace_lock:
            if request_key:
                with self._lock:
                    existing_job_id = self._request_keys.get(request_key)
                    if existing_job_id:
                        existing_job = self._jobs.get(existing_job_id)
                        if existing_job and existing_job.status in {"queued", "running", "completed"}:
                            return existing_job

            job = self.create_job(pioneer_id=pioneer_id)
            if request_key:
                with self._lock:
                    self._request_keys[request_key] = job.job_id
                    self._job_request_keys[job.job_id] = request_key

            future = self._executor.submit(self._run_job, job.job_id, task)
            with self._lock:
                self._futures[job.job_id] = future
            return job

    def _run_job(self, job_id: str, task: RenderTask) -> None:
        self.update_job(job_id, status="running", progress=0.05, error_message=None, output_path=None)

        def report_progress(value: float) -> None:
            clamped = max(0.0, min(1.0, value))
            self.update_job(job_id, progress=clamped)

        try:
            output_path = task(report_progress)
            self.update_job(
                job_id,
                status="completed",
                progress=1.0,
                output_path=output_path,
                error_message=None,
            )
        except Exception as exc:
            self.update_job(
                job_id,
                status="failed",
                progress=1.0,
                output_path=None,
                error_message=str(exc),
            )
            self._clear_request_key(job_id)

    def get_job(self, job_id: str) -> RenderJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        progress: float | None = None,
        output_path: Path | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs[job_id]
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if output_path is not None or status == "failed":
                job.output_path = output_path
            if error_message is not None or status == "completed":
                job.error_message = error_message

    def _clear_request_key(self, job_id: str) -> None:
        with self._lock:
            request_key = self._job_request_keys.pop(job_id, None)
            if request_key is None:
                return
            current_job_id = self._request_keys.get(request_key)
            if current_job_id == job_id:
                self._request_keys.pop(request_key, None)
