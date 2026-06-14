from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl

from app.services.task_manager import TaskManager
from app.services.video_downloader import VideoDownloader
from app.services.ytdlp_downloader import YtdlpVideoDownloader


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class FormatResponse(BaseModel):
    format_id: str
    label: str
    ext: str
    is_audio_only: bool = False


class AnalyzeResponse(BaseModel):
    title: str
    thumbnail: str
    duration: int
    formats: List[FormatResponse]
    default_format_id: str


class DownloadRequest(BaseModel):
    url: HttpUrl
    format_id: Optional[str] = None


class DownloadResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    status: str
    progress: float
    error: Optional[str] = None
    filename: Optional[str] = None


def _attachment_disposition(filename: str) -> str:
    safe_name = Path(filename).name
    suffix = Path(safe_name).suffix or ".bin"
    ascii_name = safe_name.encode("ascii", "ignore").decode() or f"download{suffix}"
    encoded_name = quote(safe_name)
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded_name}'


def create_app(
    download_dir: Optional[Path] = None,
    downloader: Optional[VideoDownloader] = None,
    task_manager: Optional[TaskManager] = None,
    cleanup_ttl_seconds: float = 1800.0,
) -> FastAPI:
    app = FastAPI(title="SnapVid API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.downloader = downloader if downloader is not None else YtdlpVideoDownloader()
    app.state.download_dir = download_dir or Path("downloads")
    app.state.task_manager = task_manager or TaskManager(
        cleanup_ttl_seconds=cleanup_ttl_seconds
    )

    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    def analyze_video(body: AnalyzeRequest):
        if app.state.downloader is None:
            raise HTTPException(status_code=503, detail="Downloader not configured")

        url = str(body.url)
        try:
            info = app.state.downloader.analyze(url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid video URL: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to analyze video: {exc}") from exc

        return AnalyzeResponse(
            title=info.title,
            thumbnail=info.thumbnail,
            duration=info.duration,
            formats=[FormatResponse(**asdict(fmt)) for fmt in info.formats],
            default_format_id=info.default_format_id,
        )

    @app.post("/api/download", response_model=DownloadResponse)
    def start_download(body: DownloadRequest, background_tasks: BackgroundTasks):
        if app.state.downloader is None:
            raise HTTPException(status_code=503, detail="Downloader not configured")

        url = str(body.url)
        task = app.state.task_manager.create_task(url, body.format_id)
        background_tasks.add_task(
            app.state.task_manager.run_download,
            task.id,
            app.state.downloader,
            app.state.download_dir,
        )
        return DownloadResponse(task_id=task.id)

    @app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
    def get_task_status(task_id: str):
        task = app.state.task_manager.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskStatusResponse(
            status=task.status,
            progress=task.progress,
            error=task.error,
            filename=task.filename,
        )

    @app.get("/api/tasks/{task_id}/file")
    def download_task_file(task_id: str):
        try:
            file_path, filename = app.state.task_manager.get_downloadable_file(task_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Task not found") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        content = file_path.read_bytes()
        response = Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": _attachment_disposition(filename)},
        )
        app.state.task_manager.mark_file_delivered(task_id)
        return response

    return app
