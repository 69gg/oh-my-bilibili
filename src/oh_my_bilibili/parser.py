"""Video identifier parsing for BV/AV/URL/b23.tv."""

from __future__ import annotations

import re
from collections.abc import Iterable

import httpx

BV_PATTERN = re.compile(r"BV1[1-9A-HJ-NP-Za-km-z]{9}", re.IGNORECASE)
AV_PATTERN = re.compile(r"\bav(\d+)\b", re.IGNORECASE)
URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?bilibili\.com/video/"
    r"(BV1[1-9A-HJ-NP-Za-km-z]{9}|av\d+)",
    re.IGNORECASE,
)
SHORT_URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?b23\.tv/[A-Za-z0-9]+")

_AV2BV_TABLE = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
_AV2BV_S = [11, 10, 3, 8, 4, 6]
_AV2BV_XOR = 177451812
_AV2BV_ADD = 8728348608


def av_to_bv(avid: int) -> str:
    """Convert AV id to BV id."""
    encoded = (avid ^ _AV2BV_XOR) + _AV2BV_ADD
    bv = list("BV1  4 1 7  ")
    for index, pos in enumerate(_AV2BV_S):
        bv[pos] = _AV2BV_TABLE[encoded // 58**index % 58]
    return "".join(bv)


def _canonicalize_bvid(text: str) -> str:
    return "BV" + text[2:]


def resolve_short_url(
    short_url: str,
    *,
    client: httpx.Client | None = None,
    timeout: float = 10.0,
) -> str | None:
    """Resolve b23.tv short url to final url."""
    target = short_url if short_url.startswith("http") else f"https://{short_url}"

    if client is not None:
        return _resolve_short_url_with_client(client, target)

    with httpx.Client(follow_redirects=False, timeout=timeout) as temp_client:
        return _resolve_short_url_with_client(temp_client, target)


def _resolve_short_url_with_client(client: httpx.Client, short_url: str) -> str | None:
    try:
        head_resp = client.head(short_url, follow_redirects=False)
        location = head_resp.headers.get("Location") or head_resp.headers.get("location")
        if location:
            return str(location)
    except Exception:
        pass

    try:
        get_resp = client.get(short_url, follow_redirects=True)
        return str(get_resp.url)
    except Exception:
        return None


def normalize_to_bvid(
    identifier: str,
    *,
    client: httpx.Client | None = None,
) -> str | None:
    """Normalize BV/AV/URL/b23.tv identifier to BV id."""
    raw = identifier.strip()
    if not raw:
        return None

    match = BV_PATTERN.search(raw)
    if match:
        return _canonicalize_bvid(match.group(0))

    match = SHORT_URL_PATTERN.search(raw)
    if match:
        resolved = resolve_short_url(match.group(0), client=client)
        if not resolved:
            return None
        if resolved.strip() == raw:
            return None
        return normalize_to_bvid(resolved, client=client)

    match = URL_PATTERN.search(raw)
    if match:
        vid = match.group(1)
        if vid.lower().startswith("av"):
            return av_to_bv(int(vid[2:]))
        return _canonicalize_bvid(vid)

    match = AV_PATTERN.fullmatch(raw)
    if match:
        return av_to_bv(int(match.group(1)))

    return None


def extract_bilibili_ids(
    text: str,
    *,
    client: httpx.Client | None = None,
) -> list[str]:
    """Extract all unique BV ids from text."""
    seen: set[str] = set()
    result: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in seen:
            seen.add(value)
            result.append(value)

    for match in URL_PATTERN.finditer(text):
        add(normalize_to_bvid(match.group(0), client=client))
    for match in BV_PATTERN.finditer(text):
        add(normalize_to_bvid(match.group(0), client=client))
    for match in AV_PATTERN.finditer(text):
        add(normalize_to_bvid(match.group(0), client=client))
    for match in SHORT_URL_PATTERN.finditer(text):
        add(normalize_to_bvid(match.group(0), client=client))

    return result


def extract_bilibili_ids_from_iterable(
    lines: Iterable[str],
    *,
    client: httpx.Client | None = None,
) -> list[str]:
    """Extract all unique BV ids from multiple text fragments."""
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        for bvid in extract_bilibili_ids(line, client=client):
            if bvid not in seen:
                seen.add(bvid)
                result.append(bvid)
    return result
