"""
抖音 SSR 数据提取器
直接从抖音分享页 HTML 提取视频元数据，无需外部 API

用法:
    from douyin_ssr import extract
    data = extract("https://www.douyin.com/video/7659433645735693609")
    # 或从 HTML 字符串
    data = extract_from_html(html_content)
"""

import re
import json
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
)

# ── 公共接口 ──────────────────────────

def extract(video_url: str, cookies: dict = None) -> dict:
    """从视频链接提取元数据（优先 SSR，备选 API）"""
    video_id = _extract_video_id(video_url)
    if not video_id:
        return {"success": False, "error": "无法提取 video_id"}

    # 抓取分享页
    import requests
    share_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
    try:
        resp = requests.get(share_url, headers={"User-Agent": UA_MOBILE}, timeout=10, allow_redirects=True)
        resp.raise_for_status()
        data = extract_from_html(resp.text, video_id)
        if data:
            return {"success": True, "data": data, "source": "ssr"}
    except Exception as e:
        pass

    # 备选：直接请求 douyin.com
    try:
        resp = requests.get(
            f"https://www.douyin.com/video/{video_id}",
            headers={"User-Agent": UA_MOBILE},
            timeout=10, allow_redirects=True
        )
        data = extract_from_html(resp.text, video_id)
        if data:
            return {"success": True, "data": data, "source": "ssr"}
    except Exception as e:
        pass

    return {"success": False, "error": "无法解析视频数据"}


def extract_from_html(html: str, video_id: Optional[str] = None) -> Optional[dict]:
    """从 HTML 中提取视频元数据"""
    # 方法1: 从 SSR_DATA 提取（iesdouyin 分享页）
    data = _extract_from_ssr(html)
    if data:
        return data

    # 方法2: 直接正则匹配 item_list
    data = _extract_item_list(html)
    if data:
        return data

    return None


# ── 私有实现 ──────────────────────────

def _extract_video_id(url: str) -> Optional[str]:
    """从 URL 提取 video_id"""
    m = re.search(r'(?:douyin\.com/video/|video/(\d+))', url)
    if m:
        return m.group(1) or m.group(2) if m.lastindex else None

    # 重定向获取
    try:
        import requests
        resp = requests.head(url, headers={"User-Agent": UA_MOBILE}, timeout=8, allow_redirects=True)
        m = re.search(r'video/(\d+)', resp.url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _extract_from_ssr(html: str) -> Optional[dict]:
    """从 window._SSR_DATA 提取"""
    idx = html.find('"item_list"')
    if idx < 0:
        return None

    # 往后找最近的完整 JSON 数组
    start = html.index('[', idx)
    depth, end = 0, start
    for i in range(start, min(start + 50000, len(html))):
        if html[i] == '[': depth += 1
        elif html[i] == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    raw = html[start:end]
    return _parse_first_item(raw)


def _extract_item_list(html: str) -> Optional[dict]:
    """通过正则提取各项字段"""
    fields = {
        'desc': r'"desc":"((?:[^"\\]|\\.)*)"',
        'nickname': r'"nickname":"((?:[^"\\]|\\.)*)"',
        'signature': r'"signature":"((?:[^"\\]|\\.)*)"',
        'aweme_id': r'"aweme_id":"(\d+)"',
        'duration': r'"duration":(\d+)',
        'create_time': r'"create_time":(\d+)',
        'digg_count': r'"digg_count":(\d+)',
        'comment_count': r'"comment_count":(\d+)',
        'share_count': r'"share_count":(\d+)',
    }

    info = {}
    for key, pat in fields.items():
        m = re.search(pat, html)
        if m:
            info[key] = m.group(1)

    if 'aweme_id' not in info:
        return None

    return _format_item(info)


def _parse_first_item(raw: str) -> Optional[dict]:
    """解析 item_list 第一项"""
    try:
        # 处理 unicode 转义
        raw = raw.replace('\\u002F', '/')
        items = json.loads(raw)
        if items and isinstance(items, list):
            return _format_item(items[0])
    except json.JSONDecodeError:
        pass

    # 正则兜底
    return _extract_item_list(raw)


def _format_item(item: dict) -> dict:
    """标准化输出"""
    author = item.get('author', {})
    if not isinstance(author, dict):
        author = {}

    stats = item.get('statistics', {})
    if not isinstance(stats, dict):
        stats = {}

    # 时间
    ct = item.get('create_time', 0)
    ct = int(ct) if ct else 0
    create_dt = datetime.fromtimestamp(ct).strftime('%Y-%m-%d %H:%M') if ct else ''

    # 时长：取合理的值（< 10000 为秒，否则可能是毫秒或错误数据）
    dur_candidates = [
        item.get('duration', 0),
        item.get('video', {}).get('duration', 0),
        item.get('music', {}).get('duration', 0),
    ]
    dur = 0
    for d in dur_candidates:
        d = int(d) if d else 0
        if 1 < d < 10000:  # 秒级别
            dur = d
            break
    if dur == 0:
        # 可能是毫秒，挑最小的合理值
        for d in dur_candidates:
            d = int(d) if d else 0
            if 1000 < d < 1000000:
                dur = d // 1000
                break

    return {
        "aweme_id": str(item.get('aweme_id', '')),
        "desc": item.get('desc', '').strip(),
        "duration": dur,
        "create_time": create_dt,
        "author": {
            "nickname": author.get('nickname', item.get('nickname', '')),
            "signature": author.get('signature', item.get('signature', '')),
            "short_id": author.get('short_id', ''),
            "aweme_count": author.get('aweme_count', 0),
        },
        "statistics": {
            "digg_count": int(stats.get('digg_count', item.get('digg_count', 0))),
            "comment_count": int(stats.get('comment_count', item.get('comment_count', 0))),
            "share_count": int(stats.get('share_count', item.get('share_count', 0))),
        },
    }


# ── CLI ──────────────────────────────

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if not url:
        print("用法: python3 douyin_ssr.py <视频链接>")
        sys.exit(1)

    result = extract(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
