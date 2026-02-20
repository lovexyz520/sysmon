"""HTTP 網站檢測工具"""

from __future__ import annotations

import time
from typing import Any

import httpx
from html.parser import HTMLParser


DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

STATUS_DESCRIPTIONS = {
    200: "OK", 201: "Created", 204: "No Content",
    301: "Moved Permanently", 302: "Found", 304: "Not Modified",
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
    404: "Not Found", 405: "Method Not Allowed", 429: "Too Many Requests",
    500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable",
    504: "Gateway Timeout",
}


class _TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def _extract_title(html: str) -> str:
    parser = _TitleParser()
    try:
        parser.feed(html[:10000])
    except Exception:
        pass
    return parser.title.strip()


def check_website(url: str, user_agent: str = DEFAULT_UA, timeout: int = 15) -> dict[str, Any]:
    """
    檢測網站 HTTP 資訊：狀態碼、標頭、重定向鏈、回應時間、頁面標題
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    redirect_chain: list[dict[str, Any]] = []
    headers = {"User-Agent": user_agent}

    try:
        start = time.perf_counter()
        with httpx.Client(
            headers=headers,
            follow_redirects=True,
            timeout=timeout,
            verify=False,
        ) as client:
            resp = client.get(url)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # 重定向鏈
        for r in resp.history:
            redirect_chain.append({
                "url": str(r.url),
                "status_code": r.status_code,
                "status_text": STATUS_DESCRIPTIONS.get(r.status_code, ""),
            })

        # 最終回應
        final_status = resp.status_code
        response_headers = dict(resp.headers)
        content_type = resp.headers.get("content-type", "")
        title = ""
        if "text/html" in content_type:
            title = _extract_title(resp.text)

        return {
            "url": str(resp.url),
            "original_url": url,
            "status_code": final_status,
            "status_text": STATUS_DESCRIPTIONS.get(final_status, ""),
            "response_time_ms": round(elapsed_ms, 2),
            "headers": response_headers,
            "redirect_chain": redirect_chain,
            "title": title,
            "content_type": content_type,
            "content_length": len(resp.content),
            "server": resp.headers.get("server", ""),
        }
    except httpx.ConnectError as e:
        return {"url": url, "error": f"連線失敗：{e}"}
    except httpx.TimeoutException:
        return {"url": url, "error": "連線超時"}
    except Exception as e:
        return {"url": url, "error": str(e)}
