"""
微信公众号文章解析模块
兼容多种文章格式：标准图文、图文模式等
"""

import re
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 20


def parse_wechat_article(url):
    if "mp.weixin.qq.com" not in url:
        return {"error": "不是有效的公众号文章链接"}

    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except:
        return {"error": "文章请求失败"}

    if r.status_code != 200:
        return {"error": f"请求失败: HTTP {r.status_code}"}

    html = r.text

    # 标题
    title = ""
    m = re.search(r'<title>(.*?)</title>', html)
    if m:
        title = m.group(1).replace('&#x0a;', '').strip()
    if not title:
        m = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
        if m:
            title = m.group(1)

    # 作者
    author = ""
    m = re.search(r'var\s+author_name\s*=\s*"([^"]+)"', html)
    if m:
        author = m.group(1)

    # 公众号
    account = ""
    m = re.search(r'var\s+user_name\s*=\s*"([^"]+)"', html)
    if m:
        account = m.group(1)

    # ── 正文提取：多种格式兼容 ──
    content = ""
    content_format = "unknown"

    # 格式1: 标准图文 (js_content)
    m = re.search(r'id="js_content"[^>]*>([\s\S]*?)</div>\s*<script', html)
    if m:
        text = _clean_html(m.group(1))
        if len(text) > 50:
            content = text
            content_format = "rich_text"

    # 格式2: js_article + rich_media_content
    if not content:
        m = re.search(r'id="js_article"[^>]*>([\s\S]*?)(?:</div>\s*){1,3}<script', html)
        if m:
            m2 = re.search(r'rich_media_content[^>]*>([\s\S]*?)</div>', m.group(1))
            if m2:
                text = _clean_html(m2.group(1))
                if len(text) > 50:
                    content = text
                    content_format = "rich_text"

    # 格式3: 图文模式 (description meta)
    if not content:
        m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
        if m:
            text = m.group(1).replace('&#x0a;', '\n').replace('&amp;nbsp;', '').strip()
            if text:
                content = text
                content_format = "image_album"

    # 格式4: og:description
    if not content:
        m = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"', html)
        if m:
            text = m.group(1).replace('&#x0a;', '\n').strip()
            if text:
                content = text
                content_format = "meta_only"

    # 封面图
    cover = ""
    m = re.search(r'var\s+msg_cdn_url\s*=\s*"([^"]+)"', html)
    if m:
        cover = m.group(1)
    if not cover:
        m = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if m:
            cover = m.group(1)

    # 发布时间
    create_time = ""
    m = re.search(r'var\s+create_time\s*=\s*"([^"]+)"', html)
    if m:
        create_time = m.group(1)

    # 提取图片（图文模式可能有图）
    images = re.findall(r'<img[^>]+src="([^"]+)"', html)
    images = [img for img in images if not img.startswith("data:")][:20]

    return {
        "title": title,
        "author": author,
        "account": account,
        "format": content_format,
        "cover": cover,
        "create_time": create_time,
        "content_text": content,
        "content_length": len(content),
        "images": images,
        "raw_url": url,
    }


def _clean_html(html):
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'&nbsp;|&#x0a;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
