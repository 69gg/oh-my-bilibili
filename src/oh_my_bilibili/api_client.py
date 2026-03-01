"""HTTP API client with WBI fallback strategy."""

from __future__ import annotations

from typing import Any

import httpx

from oh_my_bilibili.errors import ApiResponseError
from oh_my_bilibili.models import VideoInfo
from oh_my_bilibili.wbi import build_signed_params, parse_cookie_string

_BILIBILI_API_VIEW = "https://api.bilibili.com/x/web-interface/view"
_BILIBILI_API_VIEW_WBI = "https://api.bilibili.com/x/web-interface/wbi/view"
_BILIBILI_API_PLAYURL = "https://api.bilibili.com/x/player/playurl"
_BILIBILI_API_PLAYURL_WBI = "https://api.bilibili.com/x/player/wbi/playurl"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com",
}


def _api_message(data: dict[str, Any]) -> str:
    return str(data.get("message") or data.get("msg") or "unknown error")


class BilibiliApiClient:
    """Thin sync API client over Bilibili endpoints."""

    def __init__(self, *, cookie: str = "", timeout: float = 30.0) -> None:
        cookies = parse_cookie_string(cookie)
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            cookies=cookies,
            timeout=timeout,
            follow_redirects=True,
        )

    @property
    def http_client(self) -> httpx.Client:
        return self._client

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BilibiliApiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _request_json(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self._client.get(endpoint, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ApiResponseError("API response is not a JSON object")
        return payload

    def request_with_wbi_fallback(
        self,
        *,
        endpoint: str,
        params: dict[str, Any],
        signed_endpoint: str | None = None,
    ) -> dict[str, Any]:
        """Three-step strategy: plain -> signed -> refresh key + signed."""
        wbi_endpoint = signed_endpoint or endpoint
        payload = self._request_json(endpoint, params)
        if int(payload.get("code", -1)) == 0:
            return payload

        try:
            signed_params = build_signed_params(self._client, params)
        except Exception:
            return payload

        signed_payload = self._request_json(wbi_endpoint, signed_params)
        if int(signed_payload.get("code", -1)) == 0:
            return signed_payload

        try:
            refreshed_params = build_signed_params(
                self._client,
                params,
                force_refresh=True,
            )
        except Exception:
            return signed_payload

        if refreshed_params == signed_params:
            return signed_payload
        return self._request_json(wbi_endpoint, refreshed_params)

    def get_video_info(self, bvid: str) -> VideoInfo:
        payload = self.request_with_wbi_fallback(
            endpoint=_BILIBILI_API_VIEW,
            signed_endpoint=_BILIBILI_API_VIEW_WBI,
            params={"bvid": bvid},
        )
        if int(payload.get("code", -1)) != 0:
            raise ApiResponseError(f"Failed to fetch video info: {_api_message(payload)}")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ApiResponseError("Missing data in video info response")

        pages = data.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ApiResponseError("Missing page information in video info response")

        page0 = pages[0]
        if not isinstance(page0, dict) or "cid" not in page0:
            raise ApiResponseError("Missing cid in page information")

        owner = data.get("owner")
        owner_name = ""
        if isinstance(owner, dict):
            owner_name = str(owner.get("name", ""))

        return VideoInfo(
            bvid=bvid,
            title=str(data.get("title", "")),
            duration=int(data.get("duration", 0)),
            cover_url=str(data.get("pic", "")),
            up_name=owner_name,
            desc=str(data.get("desc", "")),
            cid=int(page0["cid"]),
        )

    def get_playurl(self, bvid: str, cid: int) -> dict[str, Any]:
        payload = self.request_with_wbi_fallback(
            endpoint=_BILIBILI_API_PLAYURL,
            signed_endpoint=_BILIBILI_API_PLAYURL_WBI,
            params={
                "bvid": bvid,
                "cid": cid,
                "fnval": 16,
                "fourk": 1,
            },
        )
        if int(payload.get("code", -1)) != 0:
            raise ApiResponseError(f"Failed to fetch playurl: {_api_message(payload)}")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise ApiResponseError("Missing data in playurl response")
        return data
