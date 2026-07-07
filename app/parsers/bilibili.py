"""
B站视频解析模块
"""

import re
import requests
from config import BILIBILI_API_URL

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 20


def parse_bilibili_video(url):
    bv_id = ""
    m = re.search(r'(BV[a-zA-Z0-9]+)', url)
    if m:
        bv_id = m.group(1)
    if not bv_id:
        m = re.search(r'b23\.tv/([a-zA-Z0-9]+)', url)
        if m:
            try:
                r = requests.head(url, allow_redirects=True, timeout=10, headers={"User-Agent": UA})
                m2 = re.search(r'(BV[a-zA-Z0-9]+)', r.url)
                if m2:
                    bv_id = m2.group(1)
            except:
                pass

    if not bv_id:
        return {"error": "无法提取BV号"}

    try:
        r = requests.get(f"{BILIBILI_API_URL}/api/bilibili/web/fetch_one_video?bv_id={bv_id}",
                         headers={"User-Agent": UA}, timeout=TIMEOUT)
        data = r.json()
    except Exception as e:
        return {"error": f"B站API请求失败: {e}"}

    detail = data.get("data", {})
    if not detail:
        return {"error": "未获取到视频数据"}

    stat = detail.get("stat", {})
    owner = detail.get("owner", {})

    return {
        "title": detail.get("title", ""),
        "description": detail.get("desc", "")[:500],
        "author": {
            "name": owner.get("name", ""),
            "mid": owner.get("mid", 0),
            "avatar": owner.get("face", ""),
        },
        "stats": {
            "view": stat.get("view", 0),
            "like": stat.get("like", 0),
            "coin": stat.get("coin", 0),
            "favorite": stat.get("favorite", 0),
            "danmaku": stat.get("danmaku", 0),
            "reply": stat.get("reply", 0),
        },
        "cover": detail.get("pic", ""),
        "duration": detail.get("duration", 0),
        "bv_id": bv_id,
    }
