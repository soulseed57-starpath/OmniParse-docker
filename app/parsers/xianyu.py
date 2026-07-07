"""
闲鱼商品解析模块
通过公开的闲鱼页面解析获取商品信息
"""

import re
import os
import requests
from config import XIANYU_API_URL

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 15

# 可选的外部解析 API（通过环境变量配置，非必需）
XIANYU_API = os.environ.get("XIANYU_API_URL", "")


def extract_item_id(url):
    """从闲鱼链接提取商品ID"""
    m = re.search(r'goofish\.com/item/(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'id=(\d+)', url)
    if m:
        return m.group(1)
    return None


def parse_xianyu_item(url):
    """解析闲鱼商品"""
    item_id = extract_item_id(url)
    if not item_id:
        return {"error": "无法提取商品ID"}

    # 如果有配置外部 API 则尝试
    if XIANYU_API:
        try:
            r = requests.get(f"{XIANYU_API}/{item_id}",
                             headers={"User-Agent": UA}, timeout=TIMEOUT)
            if r.status_code == 200:
                result = r.json()
                if result.get('status') == '200' and result.get('data'):
                    return {
                        "item_id": item_id,
                        "detail": result['data'],
                        "source": "api",
                    }
        except Exception:
            pass

    # 直接从公开页面解析
    urls_to_try = [
        f"https://www.goofish.com/item/{item_id}",
        f"https://m.goofish.com/item?id={item_id}",
    ]
    for page_url in urls_to_try:
        try:
            r = requests.get(page_url, headers={"User-Agent": UA}, timeout=TIMEOUT)
            if r.status_code == 200:
                html = r.text
                title = ""
                m = re.search(r'<title>(.*?)</title>', html)
                if m:
                    title = m.group(1)
                price = ""
                m = re.search(r'["\']?price["\']?\s*[:=]\s*["\']?([\d.]+)', html)
                if m:
                    price = m.group(1)
                desc = ""
                m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
                if m:
                    desc = m.group(1)[:500]
                if title or desc:
                    return {
                        "item_id": item_id,
                        "title": title,
                        "price": price,
                        "description": desc,
                        "source": "web_page",
                    }
        except Exception:
            pass

    return {"error": "暂无法解析该闲鱼商品", "item_id": item_id}
