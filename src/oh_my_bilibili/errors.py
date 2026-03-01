"""Custom exceptions used by the package."""

from __future__ import annotations


class BilibiliError(Exception):
    """Base exception for package errors."""


class InvalidVideoIdentifierError(BilibiliError):
    """Raised when BV/AV/URL cannot be parsed."""


class ApiResponseError(BilibiliError):
    """Raised when Bilibili API returns invalid or failed response."""


class DownloadError(BilibiliError):
    """Raised when stream download or merge process fails."""


class FFmpegError(DownloadError):
    """Raised when ffmpeg merge fails."""


class FFmpegNotFoundError(FFmpegError):
    """Raised when ffmpeg executable cannot be found."""
