from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable, Optional, Protocol


@dataclass(frozen=True)
class VideoFormat:
    format_id: str
    label: str
    ext: str
    is_audio_only: bool = False


@dataclass(frozen=True)
class VideoInfo:
    url: str
    title: str
    thumbnail: str
    duration: int
    formats: list[VideoFormat]
    default_format_id: str


@dataclass
class DownloadResult:
    file_path: Path
    filename: str


ProgressCallback = Callable[[float], None]


class VideoDownloader(Protocol):
    def analyze(self, url: str) -> VideoInfo:
        ...

    def download(
        self,
        url: str,
        format_id: str | None,
        output_dir: Path,
        on_progress: ProgressCallback | None = None,
    ) -> DownloadResult:
        ...


@dataclass
class FakeVideoDownloader:
    videos: dict[str, VideoInfo] = field(default_factory=dict)
    download_files: dict[str, Path] = field(default_factory=dict)
    analyze_error: Optional[str] = None
    download_error: Optional[str] = None
    download_block: Optional[Event] = None

    def analyze(self, url: str) -> VideoInfo:
        if self.analyze_error:
            raise ValueError(self.analyze_error)
        if url not in self.videos:
            raise ValueError("Unsupported or invalid video URL")
        return self.videos[url]

    def download(
        self,
        url: str,
        format_id: str | None,
        output_dir: Path,
        on_progress: ProgressCallback | None = None,
    ) -> DownloadResult:
        if self.download_error:
            raise RuntimeError(self.download_error)
        if self.download_block is not None:
            self.download_block.wait(timeout=5)
        source = self.download_files.get(url)
        if source is None or not source.exists():
            raise RuntimeError("Download failed")

        if on_progress:
            on_progress(0.5)
            on_progress(1.0)

        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / source.name
        destination.write_bytes(source.read_bytes())
        return DownloadResult(file_path=destination, filename=source.name)


def sample_video_info(url: str = "https://example.com/video") -> VideoInfo:
    return VideoInfo(
        url=url,
        title="Sample Video",
        thumbnail="https://example.com/thumb.jpg",
        duration=120,
        formats=[
            VideoFormat("best", "最佳画质 (MP4)", "mp4"),
            VideoFormat("720", "720p (MP4)", "mp4"),
            VideoFormat("audio", "仅音频 (MP3)", "mp3", is_audio_only=True),
        ],
        default_format_id="best",
    )
