"""Public data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class VideoInfo:
    """Basic video metadata from Bilibili API."""

    bvid: str
    title: str
    duration: int
    cover_url: str
    up_name: str
    desc: str
    cid: int

    @property
    def url(self) -> str:
        """Canonical video URL."""
        return f"https://www.bilibili.com/video/{self.bvid}"


@dataclass(slots=True, frozen=True)
class DownloadResult:
    """Result after video file is downloaded."""

    path: Path
    size_bytes: int
    quality: int
    quality_label: str
    video_info: VideoInfo
