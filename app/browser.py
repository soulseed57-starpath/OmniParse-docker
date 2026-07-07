"""
浏览器渲染模块
使用 Playwright 渲染 JavaScript 页面，提取内容
"""

import os
import time
import logging
from urllib.parse import urlparse

logger = logging.getLogger("omniparse.browser")

# Playwright 仅在需要时导入
_playwright_available = False
try:
    from playwright.sync_api import sync_playwright
    _playwright_available = True
except ImportError:
    pass


def fetch_page(url, wait_seconds=3, timeout_ms=15000):
    """
    使用无头浏览器获取 JS 渲染后的页面内容
    返回页面文本内容（去标签）
    """
    if not _playwright_available:
        return {"error": "Playwright 未安装，无法渲染 JavaScript 页面"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                time.sleep(wait_seconds)  # 额外等待 JS 渲染
                content = page.content()
                title = page.title()
                return {"title": title, "html": content, "url": page.url}
            except Exception as e:
                return {"error": f"页面加载失败: {str(e)}"}
            finally:
                browser.close()
    except Exception as e:
        return {"error": f"浏览器启动失败: {str(e)}"}


def extract_meta_info(html, fields=None):
    """从 HTML 中提取 meta 信息"""
    import re
    result = {}

    if fields is None:
        fields = ["title", "description", "price", "image"]

    m = re.search(r'<title>(.*?)</title>', html)
    if m and "title" in fields:
        result["title"] = _clean(m.group(1))

    m = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
    if m and "title" in fields and "title" not in result:
        result["title"] = _clean(m.group(1))

    m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
    if m and "description" in fields:
        result["description"] = _clean(m.group(1))[:500]

    m = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
    if m and "image" in fields:
        result["image"] = m.group(1)

    m = re.search(r'"price"[:\s]+"([\d.]+)"', html)
    if m and "price" in fields:
        result["price"] = m.group(1)

    if not result.get("price"):
        m = re.search(r'"price"[:\s]+([\d.]+)', html)
        if m and "price" in fields:
            result["price"] = m.group(1)

    return result


def _clean(text):
    import re
    return re.sub(r'\s+', ' ', text).strip()
