"""oh-my-bilibili public API."""

from oh_my_bilibili.errors import (
    ApiResponseError,
    BilibiliError,
    DownloadError,
    FFmpegError,
    FFmpegNotFoundError,
    InvalidVideoIdentifierError,
)
from oh_my_bilibili.models import DownloadResult, VideoInfo
from oh_my_bilibili.service import download, fetch, get_video_info

__all__ = [
    "ApiResponseError",
    "BilibiliError",
    "DownloadError",
    "DownloadResult",
    "FFmpegError",
    "FFmpegNotFoundError",
    "InvalidVideoIdentifierError",
    "VideoInfo",
    "download",
    "fetch",
    "get_video_info",
]
