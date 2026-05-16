"""Bilibili connector for fetching recent UP videos with WBI signing."""
from __future__ import annotations

import hashlib
import os
import re
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urlencode, urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
    "Accept": "application/json,text/plain,*/*",
}


def _build_headers() -> dict:
    headers = dict(HEADERS)
    cookie = (os.getenv("BILIBILI_COOKIE") or "").strip()
    if cookie:
        headers["Cookie"] = cookie
    return headers

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32,
    15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19,
    29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61,
    26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63,
    57, 62, 11, 36, 20, 34, 44, 52,
]


class BilibiliFetchError(RuntimeError):
    pass


def extract_mid(input_text: str) -> str:
    text = (input_text or "").strip()
    if not text:
        raise BilibiliFetchError("B站输入为空，请提供 UID 或主页链接。")

    if re.fullmatch(r"\d+", text):
        return text

    m = re.search(r"space\.bilibili\.com\/(\d+)", text)
    if m:
        return m.group(1)

    raise BilibiliFetchError("无法从输入中提取 B站 UID(mid)，请提供纯 UID 或 space.bilibili.com 链接。")


def _safe_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return default


def _extract_key_from_url(url: str) -> str:
    if not url:
        return ""
    p = urlparse(url)
    name = p.path.rsplit("/", 1)[-1]
    if "." in name:
        name = name.split(".", 1)[0]
    return name


def _get_wbi_keys(session: requests.Session) -> Tuple[str, str]:
    nav_url = "https://api.bilibili.com/x/web-interface/nav"
    try:
        resp = session.get(nav_url, headers=_build_headers(), timeout=10)
    except Exception as e:
        raise BilibiliFetchError(f"请求 nav 接口失败: {e}") from e

    if resp.status_code != 200:
        raise BilibiliFetchError(
            f"请求 nav 接口失败: status_code={resp.status_code}, url={nav_url}, body={resp.text[:300]}"
        )

    try:
        payload = resp.json()
    except Exception as e:
        raise BilibiliFetchError(f"nav 接口响应非 JSON: {e}") from e

    wbi_img = ((payload.get("data") or {}).get("wbi_img")) or {}
    img_key = _extract_key_from_url(wbi_img.get("img_url", ""))
    sub_key = _extract_key_from_url(wbi_img.get("sub_url", ""))
    if not img_key or not sub_key:
        code = payload.get("code")
        message = payload.get("message")
        raise BilibiliFetchError(
            "nav 接口缺少 wbi_img.img_url 或 wbi_img.sub_url，无法生成 WBI 签名。"
            f" code={code}, message={message}"
        )
    return img_key, sub_key


def _get_mixin_key(img_key: str, sub_key: str) -> str:
    origin = img_key + sub_key
    mixed = "".join(origin[i] for i in MIXIN_KEY_ENC_TAB if i < len(origin))
    return mixed[:32]


def _sign_wbi_params(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = _get_mixin_key(img_key, sub_key)
    signed = deepcopy(params)
    signed["wts"] = int(time.time())

    filtered = {}
    for k in sorted(signed.keys()):
        v = str(signed[k])
        v = re.sub(r"[!'()*]", "", v)
        filtered[k] = v

    query = urlencode(filtered)
    filtered["w_rid"] = hashlib.md5((query + mixin_key).encode("utf-8")).hexdigest()
    return filtered


def _fetch_page(mid: str, pn: int, ps: int = 30, session: requests.Session | None = None) -> List[dict]:
    url = "https://api.bilibili.com/x/space/wbi/arc/search"
    base_params = {
        "mid": mid,
        "ps": ps,
        "pn": pn,
        "tid": 0,
        "keyword": "",
        "order": "pubdate",
        "platform": "web",
        "web_location": 1550101,
    }

    sess = session or requests.Session()
    try:
        img_key, sub_key = _get_wbi_keys(sess)
        signed_params = _sign_wbi_params(base_params, img_key, sub_key)
        resp = sess.get(url, params=signed_params, headers=_build_headers(), timeout=10)
    except BilibiliFetchError:
        raise
    except Exception as e:
        raise BilibiliFetchError(f"请求 B站接口失败: {e}") from e

    if resp.status_code != 200:
        if resp.status_code == 412:
            raise BilibiliFetchError(
                "B站数据拉取失败：接口返回 412，可能是 Cookie 失效、风控或请求频率过高。"
                f" status_code=412, url={resp.url}, body={resp.text[:300]}"
            )
        raise BilibiliFetchError(
            f"请求 B站接口失败: status_code={resp.status_code}, url={resp.url}, body={resp.text[:300]}"
        )

    try:
        payload = resp.json()
    except Exception as e:
        raise BilibiliFetchError(f"B站接口响应非 JSON: {e}, body={resp.text[:300]}") from e

    if payload.get("code") != 0:
        raise BilibiliFetchError(
            f"B站接口返回异常 code={payload.get('code')} message={payload.get('message')}"
        )

    return (((payload.get("data") or {}).get("list") or {}).get("vlist")) or []


def fetch_bilibili_up_videos(input_text: str, limit: int = 30) -> pd.DataFrame:
    mid = extract_mid(input_text)
    limit = max(1, min(limit, 30))

    session = requests.Session()
    vlist = _fetch_page(mid=mid, pn=1, ps=limit, session=session)
    if not vlist:
        raise BilibiliFetchError("未获取到公开视频，可能 UID 无效、该 UP 无公开视频或接口被限制。")

    rows = []
    for v in vlist[:limit]:
        stat = v.get("stat") or {}

        pub_ts = _safe_int(v.get("created"), 0)
        created_date = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d") if pub_ts else ""

        view_count = _safe_int(v.get("play"), 0) or _safe_int(stat.get("view"), 0)
        like_count = _safe_int(v.get("like"), 0) or _safe_int(stat.get("like"), 0)
        coin_count = _safe_int(v.get("coin"), 0) or _safe_int(stat.get("coin"), 0)
        favorite_count = _safe_int(v.get("favorites"), 0) or _safe_int(stat.get("favorite"), 0)
        comment_count = _safe_int(v.get("comment"), 0) or _safe_int(stat.get("reply"), 0)
        share_count = _safe_int(v.get("share"), 0) or _safe_int(stat.get("share"), 0)
        danmaku_count = _safe_int(v.get("video_review"), 0) or _safe_int(stat.get("danmaku"), 0)

        duration_raw = v.get("length") or v.get("duration") or 0
        author_mid = (
            _safe_int(v.get("mid"), 0)
            or _safe_int((v.get("author") or {}).get("mid"), 0)
            or _safe_int(mid, 0)
        )

        rows.append(
            {
                "bvid": v.get("bvid", ""),
                "aid": _safe_int(v.get("aid"), 0),
                "video_title": (v.get("title") or "").strip(),
                "pubdate": pub_ts,
                "created_date": created_date,
                "view_count": view_count,
                "like_count": like_count,
                "coin_count": coin_count,
                "favorite_count": favorite_count,
                "comment_count": comment_count,
                "share_count": share_count,
                "danmaku_count": danmaku_count,
                "duration": _parse_duration(duration_raw),
                "author_mid": author_mid,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        raise BilibiliFetchError("B站返回为空，无法继续分析。")
    return df


def _parse_duration(length_text) -> int:
    # format like mm:ss or hh:mm:ss, or int seconds
    if isinstance(length_text, (int, float)):
        return max(int(length_text), 0)
    parts = [int(p) for p in str(length_text).split(":") if p.isdigit()]
    if not parts:
        return 0
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0]
