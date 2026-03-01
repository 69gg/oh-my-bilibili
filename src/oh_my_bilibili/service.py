"""Public high-level service functions."""

from __future__ import annotations

from pathlib import Path

from oh_my_bilibili.api_client import BilibiliApiClient
from oh_my_bilibili.downloader import download_video
from oh_my_bilibili.errors import InvalidVideoIdentifierError
from oh_my_bilibili.models import DownloadResult, VideoInfo
from oh_my_bilibili.parser import normalize_to_bvid


def _resolve_bvid(video: str) -> str:
    bvid = normalize_to_bvid(video)
    if not bvid:
        raise InvalidVideoIdentifierError(f"Cannot parse BV/AV/URL from: {video}")
    return bvid


def get_video_info(video: str, *, cookie: str = "", timeout: float = 30.0) -> VideoInfo:
    """Get video info from BV/AV/URL."""
    bvid = _resolve_bvid(video)
    with BilibiliApiClient(cookie=cookie, timeout=timeout) as api_client:
        return api_client.get_video_info(bvid)


def download(
    video: str,
    *,
    save_path: str | Path,
    cookie: str = "",
    prefer_quality: int = 80,
    timeout: float = 30.0,
    overwrite: bool = True,
) -> DownloadResult:
    """Download video to save_path (directory or file path)."""
    bvid = _resolve_bvid(video)
    with BilibiliApiClient(cookie=cookie, timeout=timeout) as api_client:
        return download_video(
            api_client,
            bvid=bvid,
            save_path=save_path,
            prefer_quality=prefer_quality,
            overwrite=overwrite,
        )


def fetch(
    video: str,
    *,
    save_path: str | Path | None = None,
    cookie: str = "",
    prefer_quality: int = 80,
    timeout: float = 30.0,
    overwrite: bool = True,
) -> VideoInfo | DownloadResult:
    """Fetch video info, or download when save_path is provided."""
    if save_path is None:
        return get_video_info(video, cookie=cookie, timeout=timeout)
    return download(
        video,
        save_path=save_path,
        cookie=cookie,
        prefer_quality=prefer_quality,
        timeout=timeout,
        overwrite=overwrite,
    )
