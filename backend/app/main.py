from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4
import os
import shutil
import threading

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

try:
    import imageio_ffmpeg
except Exception:  # pragma: no cover
    imageio_ffmpeg = None


app = FastAPI(
    title="Universal Video Downloader API",
    version="0.1.0",
    description="MVP backend for video download service powered by yt-dlp.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FORMAT = "bv*+ba/b"
MERGE_OUTPUT_FORMAT = "mp4"
TASK_STORE: dict[str, dict[str, Any]] = {}
TASK_LOCK = threading.Lock()
LEGACY_BAD_FORMATS = {
    "best[ext=mp4]/best",
    "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
}


class VideoInfoRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)


class DownloadVideoRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)
    format_id: Optional[str] = Field(default=None, max_length=200)


class BatchDownloadRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=50)
    format_id: Optional[str] = Field(default=None, max_length=200)




def _resolve_ffmpeg_location() -> Optional[str]:
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    if imageio_ffmpeg is not None:
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_path and Path(ffmpeg_path).exists():
                return ffmpeg_path
        except Exception:
            return None

    return None


def _with_ffmpeg_location(options: dict[str, Any]) -> dict[str, Any]:
    ffmpeg_location = _resolve_ffmpeg_location()
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    return options
def _base_ydl_opts() -> dict[str, Any]:
    return _with_ffmpeg_location({
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    })


def _format_filesize(num: Optional[int]) -> Optional[int]:
    if not num:
        return None
    return int(num)


def _extract_stats(info: dict[str, Any]) -> dict[str, Optional[int]]:
    return {
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "favorite_count": info.get("favorite_count"),
        "comment_count": info.get("comment_count"),
        "danmaku_count": info.get("danmaku_count"),
        "repost_count": info.get("repost_count"),
    }


def _extract_formats(info: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    seen_ids = set()

    for fmt in info.get("formats", []):
        format_id = fmt.get("format_id")
        if not format_id or format_id in seen_ids:
            continue

        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")

        if vcodec == "none" and acodec == "none":
            continue

        kind = "video+audio"
        if vcodec == "none":
            kind = "audio-only"
        elif acodec == "none":
            kind = "video-only"

        seen_ids.add(format_id)
        resolution = fmt.get("resolution") or (
            f"{fmt.get('width')}x{fmt.get('height')}"
            if fmt.get("width") and fmt.get("height")
            else "unknown"
        )
        items.append(
            {
                "format_id": format_id,
                "ext": fmt.get("ext"),
                "resolution": resolution,
                "fps": fmt.get("fps"),
                "vcodec": vcodec,
                "acodec": acodec,
                "kind": kind,
                "filesize": _format_filesize(
                    fmt.get("filesize") or fmt.get("filesize_approx")
                ),
                "format_note": fmt.get("format_note"),
            }
        )

    return items


def _detect_output_file(info: dict[str, Any], fallback: str) -> str:
    requested = info.get("requested_downloads") or []
    if requested:
        path = requested[0].get("filepath")
        if path:
            return str(path)
    return info.get("filepath") or info.get("_filename") or fallback


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_format_id(format_id: Optional[str]) -> str:
    if not format_id:
        return DEFAULT_FORMAT
    clean = format_id.strip()
    if clean in LEGACY_BAD_FORMATS:
        return DEFAULT_FORMAT
    return clean


def _iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def _list_filesystem_completed_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for file_path in DOWNLOAD_DIR.iterdir():
        if not file_path.is_file():
            continue
        stat = file_path.stat()
        created_at = _iso_from_timestamp(stat.st_mtime)
        tasks.append(
            {
                "task_id": f"file::{file_path.name}",
                "url": "local://downloads",
                "format_id": None,
                "status": "completed",
                "progress": 100.0,
                "downloaded_bytes": int(stat.st_size),
                "total_bytes": int(stat.st_size),
                "speed": None,
                "eta": None,
                "title": file_path.stem,
                "output_file": str(file_path.resolve()),
                "error": None,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
    return tasks


def _create_task(url: str, format_id: Optional[str]) -> dict[str, Any]:
    task_id = str(uuid4())
    task = {
        "task_id": task_id,
        "url": url,
        "format_id": _normalize_format_id(format_id),
        "status": "queued",
        "progress": 0.0,
        "downloaded_bytes": 0,
        "total_bytes": None,
        "speed": None,
        "eta": None,
        "title": None,
        "output_file": None,
        "error": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    with TASK_LOCK:
        TASK_STORE[task_id] = task
    return task


def _update_task(task_id: str, patch: dict[str, Any]) -> None:
    with TASK_LOCK:
        task = TASK_STORE.get(task_id)
        if not task:
            return
        task.update(patch)
        task["updated_at"] = _now_iso()


def _download_in_background(task_id: str) -> None:
    with TASK_LOCK:
        task = TASK_STORE.get(task_id)
        if not task:
            return
        url = task["url"]
        format_id = task["format_id"]

    _update_task(task_id, {"status": "downloading", "progress": 0.0, "error": None})

    def hook(data: dict[str, Any]) -> None:
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes") or 0
            progress = 0.0
            if total:
                progress = round((downloaded / total) * 100, 2)
            _update_task(
                task_id,
                {
                    "status": "downloading",
                    "progress": progress,
                    "downloaded_bytes": int(downloaded),
                    "total_bytes": int(total) if total else None,
                    "speed": data.get("speed"),
                    "eta": data.get("eta"),
                },
            )
        elif status == "finished":
            _update_task(task_id, {"progress": 100.0})

    requested_format = _normalize_format_id(format_id)
    download_opts = _with_ffmpeg_location({
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": requested_format,
        "merge_output_format": MERGE_OUTPUT_FORMAT,
        "outtmpl": str(DOWNLOAD_DIR / "%(title).120s [%(id)s].%(ext)s"),
        "progress_hooks": [hook],
    })

    try:
        with YoutubeDL(download_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]
            fallback = ydl.prepare_filename(info)
            output_file = _detect_output_file(info, fallback)
            _update_task(
                task_id,
                {
                    "status": "completed",
                    "progress": 100.0,
                    "title": info.get("title"),
                    "output_file": output_file,
                    "error": None,
                },
            )
    except DownloadError as error:
        if "Requested format is not available" in str(error):
            fallback_opts = _with_ffmpeg_location(
                {
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "format": DEFAULT_FORMAT,
                    "merge_output_format": MERGE_OUTPUT_FORMAT,
                    "outtmpl": str(DOWNLOAD_DIR / "%(title).120s [%(id)s].%(ext)s"),
                    "progress_hooks": [hook],
                }
            )
            try:
                with YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if "entries" in info and info["entries"]:
                        info = info["entries"][0]
                    fallback = ydl.prepare_filename(info)
                    output_file = _detect_output_file(info, fallback)
                    _update_task(
                        task_id,
                        {
                            "status": "completed",
                            "progress": 100.0,
                            "title": info.get("title"),
                            "output_file": output_file,
                            "error": None,
                        },
                    )
                    return
            except Exception:
                pass
        _update_task(task_id, {"status": "failed", "error": f"{error}"})
    except Exception as error:
        _update_task(task_id, {"status": "failed", "error": f"{error}"})


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/video/info")
def video_info(payload: VideoInfoRequest) -> dict[str, Any]:
    try:
        with YoutubeDL(_base_ydl_opts()) as ydl:
            info = ydl.extract_info(payload.url, download=False)
    except DownloadError as error:
        raise HTTPException(status_code=400, detail=f"无法解析该链接: {error}") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"解析失败: {error}") from error

    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    return {
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url"),
        "stats": _extract_stats(info),
        "formats": _extract_formats(info),
        "recommended_format": DEFAULT_FORMAT,
    }


@app.post("/api/video/download")
def download_video(payload: DownloadVideoRequest) -> dict[str, Any]:
    requested_format = _normalize_format_id(payload.format_id)
    download_opts = _with_ffmpeg_location({
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": requested_format,
        "merge_output_format": MERGE_OUTPUT_FORMAT,
        "outtmpl": str(DOWNLOAD_DIR / "%(title).120s [%(id)s].%(ext)s"),
    })

    try:
        with YoutubeDL(download_opts) as ydl:
            info = ydl.extract_info(payload.url, download=True)
            fallback = ydl.prepare_filename(info)
    except DownloadError as error:
        if "Requested format is not available" in str(error):
            retry_opts = _with_ffmpeg_location(
                {
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "format": DEFAULT_FORMAT,
                    "merge_output_format": MERGE_OUTPUT_FORMAT,
                    "outtmpl": str(DOWNLOAD_DIR / "%(title).120s [%(id)s].%(ext)s"),
                }
            )
            try:
                with YoutubeDL(retry_opts) as ydl:
                    info = ydl.extract_info(payload.url, download=True)
                    fallback = ydl.prepare_filename(info)
            except Exception:
                info = None
            if info is not None:
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                output_file = _detect_output_file(info, fallback)
                return {
                    "status": "completed",
                    "title": info.get("title"),
                    "output_file": output_file,
                }
        message = str(error)
        if "ffmpeg" in message.lower() and "not found" in message.lower():
            message = f"下载失败: {error}。当前环境缺少 ffmpeg，可通过设置 FFMPEG_PATH 或安装 ffmpeg 解决。"
        else:
            message = f"下载失败: {error}"
        raise HTTPException(status_code=400, detail=message) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"下载异常: {error}") from error

    if "entries" in info and info["entries"]:
        info = info["entries"][0]

    output_file = _detect_output_file(info, fallback)
    return {
        "status": "completed",
        "title": info.get("title"),
        "output_file": output_file,
    }


@app.post("/api/video/download/batch")
def batch_download(
    payload: BatchDownloadRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    task_ids = []
    for url in payload.urls:
        clean_url = url.strip()
        if not clean_url:
            continue
        task = _create_task(clean_url, payload.format_id)
        task_ids.append(task["task_id"])
        background_tasks.add_task(_download_in_background, task["task_id"])

    if not task_ids:
        raise HTTPException(status_code=400, detail="未提供有效链接")

    return {"status": "accepted", "task_ids": task_ids}


@app.get("/api/tasks")
def list_tasks(limit: int = 100) -> dict[str, Any]:
    safe_limit = max(1, min(limit, 300))
    with TASK_LOCK:
        tasks = list(TASK_STORE.values())

    tracked_files = set()
    for task in tasks:
        output_file = task.get("output_file")
        if not output_file:
            continue
        try:
            tracked_files.add(str(Path(output_file).resolve()))
        except Exception:
            tracked_files.add(str(output_file))

    for file_task in _list_filesystem_completed_tasks():
        output_file = file_task.get("output_file")
        if output_file in tracked_files:
            continue
        tasks.append(file_task)

    tasks.sort(key=lambda item: item["created_at"], reverse=True)
    return {"tasks": tasks[:safe_limit]}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    with TASK_LOCK:
        task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
