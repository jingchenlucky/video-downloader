from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

import yt_dlp

from app.services.video_downloader import (
    DownloadResult,
    ProgressCallback,
    VideoFormat,
    VideoInfo,
)


def _normalize_thumbnail(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[len("http://") :]
    return url


def _ffmpeg_location() -> Optional[str]:
    env_path = os.environ.get("FFMPEG_LOCATION")
    if env_path:
        return env_path

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    return shutil.which("ffmpeg")


def _is_bilibili_url(url: str) -> bool:
    lowered = url.lower()
    return "bilibili.com" in lowered or "b23.tv" in lowered


def _cookie_options() -> dict:
    options: dict = {}
    cookies_file = os.environ.get("YTDLP_COOKIES_FILE")
    if cookies_file:
        options["cookiefile"] = cookies_file

    cookies_browser = os.environ.get("YTDLP_COOKIES_FROM_BROWSER")
    if cookies_browser:
        options["cookiesfrombrowser"] = (cookies_browser,)

    return options


def _proxy_options() -> dict:
    """Build yt-dlp proxy options.

    yt-dlp inherits HTTP_PROXY/HTTPS_PROXY from the environment by default.
    Local proxy tools (Clash, Cursor sandbox, etc.) often break site access with
    403 on HTTPS CONNECT. Default to direct connections; opt in via env vars.
    """
    if os.environ.get("YTDLP_USE_ENV_PROXY", "").lower() in ("1", "true", "yes"):
        return {}

    proxy = os.environ.get("YTDLP_PROXY")
    if proxy is not None:
        return {"proxy": proxy}

    return {"proxy": ""}


class YtdlpVideoDownloader:
    def _options_for_url(self, url: str, **extra) -> dict:
        options = {
            "quiet": True,
            "no_warnings": True,
            **_proxy_options(),
            **_cookie_options(),
            **extra,
        }
        ffmpeg = _ffmpeg_location()
        if ffmpeg:
            options["ffmpeg_location"] = ffmpeg
        options.setdefault("merge_output_format", "mp4")
        if _is_bilibili_url(url):
            headers = dict(options.get("http_headers") or {})
            headers.setdefault("Origin", "https://www.bilibili.com")
            headers.setdefault("Referer", "https://www.bilibili.com")
            options["http_headers"] = headers
        return options

    def analyze(self, url: str) -> VideoInfo:
        options = self._options_for_url(url, skip_download=True)
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = self._build_formats(info)
        default_format_id = formats[0].format_id if formats else "best"

        return VideoInfo(
            url=url,
            title=info.get("title") or "Untitled",
            thumbnail=_normalize_thumbnail(info.get("thumbnail") or ""),
            duration=int(info.get("duration") or 0),
            formats=formats,
            default_format_id=default_format_id,
        )

    def download(
        self,
        url: str,
        format_id: Optional[str],
        output_dir: Path,
        on_progress: ProgressCallback | None = None,
    ) -> DownloadResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        selected = format_id or "best"

        def progress_hook(status: dict) -> None:
            if on_progress and status.get("status") == "downloading":
                total = status.get("total_bytes") or status.get("total_bytes_estimate")
                downloaded = status.get("downloaded_bytes") or 0
                if total:
                    on_progress(min(downloaded / total, 0.99))

        ydl_format = self._format_to_ytdlp(selected)
        options = self._options_for_url(
            url,
            outtmpl=str(output_dir / "%(title)s.%(ext)s"),
            progress_hooks=[progress_hook],
            format=ydl_format,
        )

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = Path(ydl.prepare_filename(info))

        if on_progress:
            on_progress(1.0)

        return DownloadResult(
            file_path=file_path,
            filename=file_path.name,
        )

    def _build_formats(self, info: dict) -> list[VideoFormat]:
        formats: list[VideoFormat] = [
            VideoFormat("best", "最佳画质 (MP4)", "mp4"),
            VideoFormat("720", "720p (MP4)", "mp4"),
            VideoFormat("audio", "仅音频 (MP3)", "mp3", is_audio_only=True),
        ]

        height = info.get("height")
        if height and height >= 1080:
            formats.insert(1, VideoFormat("1080", "1080p (MP4)", "mp4"))

        return formats

    def _format_to_ytdlp(self, format_id: str) -> str:
        mapping = {
            "best": "bestvideo+bestaudio/best",
            "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "audio": "bestaudio/best",
        }
        return mapping.get(format_id, "bestvideo+bestaudio/best")
