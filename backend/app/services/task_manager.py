from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from app.services.video_downloader import VideoDownloader


@dataclass
class TaskRecord:
    id: str
    url: str
    format_id: str | None
    status: str = "queued"
    progress: float = 0.0
    error: str | None = None
    filename: str | None = None
    file_path: Path | None = None
    created_at: float = field(default_factory=time.time)
    file_delivered: bool = False


class TaskManager:
    def __init__(self, cleanup_ttl_seconds: float = 1800.0) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = Lock()
        self.cleanup_ttl_seconds = cleanup_ttl_seconds

    def create_task(self, url: str, format_id: str | None) -> TaskRecord:
        task = TaskRecord(id=str(uuid.uuid4()), url=url, format_id=format_id)
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None:
                self._cleanup_if_expired(task)
            return task

    def get_downloadable_file(self, task_id: str) -> tuple[Path, str]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise FileNotFoundError("Task not found")
            self._cleanup_if_expired(task)
            if task.status != "completed" or task.file_path is None or not task.file_path.exists():
                raise RuntimeError("File not ready")
            return task.file_path, task.filename or task.file_path.name

    def mark_file_delivered(self, task_id: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            task.file_delivered = True
            self._delete_task_file(task)

    def _cleanup_if_expired(self, task: TaskRecord) -> None:
        if task.file_delivered:
            return
        if task.status != "completed" or task.file_path is None:
            return
        if time.time() - task.created_at >= self.cleanup_ttl_seconds:
            self._delete_task_file(task)

    def _delete_task_file(self, task: TaskRecord) -> None:
        if task.file_path and task.file_path.exists():
            task.file_path.unlink()
        task.file_path = None

    def run_download(
        self,
        task_id: str,
        downloader: VideoDownloader,
        download_dir: Path,
    ) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return

        task.status = "downloading"

        def on_progress(value: float) -> None:
            task.progress = value

        try:
            result = downloader.download(
                task.url,
                task.format_id,
                download_dir,
                on_progress=on_progress,
            )
            task.file_path = result.file_path
            task.filename = result.filename
            task.status = "completed"
            task.progress = 1.0
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
