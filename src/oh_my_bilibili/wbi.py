"""WBI signing utilities for Bilibili API."""

from __future__ import annotations

import hashlib
import threading
import time
from http.cookies import CookieError, SimpleCookie
from typing import Any
from urllib.parse import quote, urlencode, urlparse

import httpx

_BILIBILI_API_NAV = "https://api.bilibili.com/x/web-interface/nav"

_MIXIN_KEY_ENC_TAB: tuple[int, ...] = (
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
)

_WBI_CACHE_TTL_SECONDS = 3600
_cached_mixin_key: str | None = None
_cached_at: float = 0.0
_cache_lock = threading.Lock()


def parse_cookie_string(cookie: str = "") -> dict[str, str]:
    """Parse raw cookie string to requests-style cookie mapping."""
    raw = cookie.strip()
    if not raw:
        return {}

    if raw.lower().startswith("cookie:"):
        raw = raw[7:].strip()

    if "=" not in raw:
        return {"SESSDATA": raw}

    parsed: dict[str, str] = {}
    simple_cookie = SimpleCookie()
    try:
        simple_cookie.load(raw)
    except CookieError:
        simple_cookie = SimpleCookie()

    if simple_cookie:
        for key, morsel in simple_cookie.items():
            value = morsel.value.strip()
            if key and value:
                parsed[key] = value

    if parsed:
        return parsed

    for part in raw.split(";"):
        item = part.strip()
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            parsed[key] = value

    if parsed:
        return parsed

    return {"SESSDATA": raw}


def _extract_key_from_url(url: str) -> str:
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1]
    return name.split(".", 1)[0]


def _compute_mixin_key(img_key: str, sub_key: str) -> str:
    merged = img_key + sub_key
    if len(merged) < 64:
        raise ValueError(f"WBI key length too short: {len(merged)}")
    mixed = "".join(merged[i] for i in _MIXIN_KEY_ENC_TAB)
    return mixed[:32]


def _refresh_mixin_key(client: httpx.Client) -> str:
    response = client.get(_BILIBILI_API_NAV)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Invalid nav response format")

    code = int(payload.get("code", -1))
    if code not in (0, -101):
        message = payload.get("message", "unknown error")
        raise ValueError(f"Failed to get wbi key: {message} (code={code})")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Missing nav.data")
    wbi_img = data.get("wbi_img")
    if not isinstance(wbi_img, dict):
        raise ValueError("Missing nav.data.wbi_img")

    img_url = str(wbi_img.get("img_url", "")).strip()
    sub_url = str(wbi_img.get("sub_url", "")).strip()
    if not img_url or not sub_url:
        raise ValueError("Missing wbi img/sub url")

    img_key = _extract_key_from_url(img_url)
    sub_key = _extract_key_from_url(sub_url)
    return _compute_mixin_key(img_key, sub_key)


def get_mixin_key(client: httpx.Client, *, force_refresh: bool = False) -> str:
    """Get reusable cached mixin key."""
    global _cached_at, _cached_mixin_key

    now = time.time()
    if (
        not force_refresh
        and _cached_mixin_key
        and now - _cached_at < _WBI_CACHE_TTL_SECONDS
    ):
        return _cached_mixin_key

    with _cache_lock:
        now = time.time()
        if (
            not force_refresh
            and _cached_mixin_key
            and now - _cached_at < _WBI_CACHE_TTL_SECONDS
        ):
            return _cached_mixin_key

        _cached_mixin_key = _refresh_mixin_key(client)
        _cached_at = time.time()
        return _cached_mixin_key


def sign_params(
    params: dict[str, Any],
    mixin_key: str,
    *,
    timestamp: int | None = None,
) -> dict[str, str]:
    """Sign query params with WBI and return params including wts/w_rid."""
    normalized: dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            continue
        key_text = str(key).strip()
        if not key_text:
            continue
        value_text = str(value)
        for char in "!'()*":
            value_text = value_text.replace(char, "")
        normalized[key_text] = value_text

    normalized["wts"] = str(int(time.time()) if timestamp is None else timestamp)

    ordered = sorted(normalized.items(), key=lambda item: item[0])
    query = urlencode(ordered, safe="-_.~", quote_via=quote)
    normalized["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return normalized


def build_signed_params(
    client: httpx.Client,
    params: dict[str, Any],
    *,
    force_refresh: bool = False,
) -> dict[str, str]:
    """Build signed query params."""
    mixin_key = get_mixin_key(client, force_refresh=force_refresh)
    return sign_params(params, mixin_key)
