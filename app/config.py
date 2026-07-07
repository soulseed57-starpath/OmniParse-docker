"""
配置管理 — 单一配置源，所有解析器从这里读取
"""

import os
from pathlib import Path

CONFIG_FILE = Path("/app/config.yaml")
TEMPLATE = """# OmniParse 配置文件
# 首次启动自动生成，用户按需填写

# 【必填】各平台 API 服务地址（各自独立配置）
# 部署了 Douyin_TikTok_Download_API 后填写对应地址
apis:
  douyin: ""
  bilibili: ""

# 【可选】服务端口（默认 8000）
port: 8000

# 【可选】浏览器 cookies — 不填使用公开解析，数据有限
# 配置后可用 Playwright 获取更完整的页面内容
cookies:
  douyin: ""
  taobao: ""
  xianyu: ""
"""

# ─── 各平台 API 地址（由 check_config 填充） ────────
DOUYIN_API_URL = ""
BILIBILI_API_URL = ""
PORT = "8000"
XIANYU_API_URL = ""

# Cookies 配置（各平台可选）
COOKIES = {"douyin": "", "taobao": "", "xianyu": ""}


def check_config():
    """检查配置，填充全局变量"""
    global DOUYIN_API_URL, BILIBILI_API_URL, PORT, XIANYU_API_URL, COOKIES

    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(TEMPLATE)
        print(f"\n⚠️  首次启动，已生成配置模板: {CONFIG_FILE}")
        print("   请填写必要配置后重启服务。\n")
        print(TEMPLATE)
        return False

    # 读取配置
    config = {}
    current_section = None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if line.startswith("#") or not line:
                continue
            if ":" not in line:
                continue
            indent = len(line) - len(line.lstrip())
            key, val = [x.strip() for x in line.split(":", 1)]
            if indent == 0 and val == "":
                current_section = key
                config[current_section] = {}
            elif indent > 0 and current_section:
                config[current_section][key] = val.strip('"').strip("'")
            else:
                config[key] = val.strip('"').strip("'")

    # 读取各平台 API 地址
    apis = config.get("apis", {})
    if isinstance(apis, dict):
        DOUYIN_API_URL = apis.get("douyin", "").rstrip("/")
        BILIBILI_API_URL = apis.get("bilibili", "").rstrip("/")

    if not DOUYIN_API_URL and not BILIBILI_API_URL:
        print(f"\n❌ 配置不完整，至少需要一个 API 地址")
        print(f"   请编辑: {CONFIG_FILE}")
        return False

    PORT = config.get("port", "8000")
    XIANYU_API_URL = config.get("xianyu_api_url", "")

    # 读取 cookies（可选）
    cookies_config = config.get("cookies", {})
    if cookies_config:
        for platform in ["douyin", "taobao", "xianyu"]:
            if cookies_config.get(platform):
                COOKIES[platform] = cookies_config[platform]

    print(f"  📡 Douyin API: {DOUYIN_API_URL or '未配置'}")
    print(f"  📡 Bilibili API: {BILIBILI_API_URL or '未配置'}")
    for k, v in COOKIES.items():
        if v:
            print(f"  🍪 {k}: 已配置 ({v[:20]}...)")
        else:
            print(f"  🍪 {k}: 未配置")

    os.environ["DOUYIN_API_URL"] = DOUYIN_API_URL
    os.environ["BILIBILI_API_URL"] = BILIBILI_API_URL
    os.environ["PORT"] = PORT
    if XIANYU_API_URL:
        os.environ["XIANYU_API_URL"] = XIANYU_API_URL

    return True
