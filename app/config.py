"""
配置管理 — 单一配置源，所有解析器从这里读取
"""

import os
from pathlib import Path

CONFIG_FILE = Path("/app/config.yaml")
TEMPLATE = """# OmniParse 配置文件
# 首次使用请填写以下配置，否则服务无法启动

# 【必填】内容解析服务 API 地址
# 部署 Douyin_TikTok_Download_API 后填写:
parser_api_url: ""

# 【可选】服务端口（默认 8000）
port: 8000

# 【可选】闲鱼外部解析 API（非必需）
xianyu_api_url: ""
"""

# ─── 解析器使用的配置（由 check_config 填充） ────────
PARSER_API_URL = ""
PORT = "8000"
XIANYU_API_URL = ""


def check_config():
    """检查配置，填充全局变量"""
    global PARSER_API_URL, PORT, XIANYU_API_URL

    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(TEMPLATE)
        print(f"\n⚠️  首次启动，已生成配置模板: {CONFIG_FILE}")
        print("   请填写必要配置后重启服务。\n")
        print(TEMPLATE)
        return False

    # 读取配置
    config = {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line or ":" not in line:
                continue
            key, val = line.split(":", 1)
            config[key.strip()] = val.strip().strip('"').strip("'")

    if not config.get("parser_api_url"):
        print(f"\n❌ 配置不完整，缺少 parser_api_url（内容解析服务地址）")
        print(f"   请编辑: {CONFIG_FILE}")
        return False

    # 填充全局变量（解析器从这里读）
    PARSER_API_URL = config["parser_api_url"].rstrip("/")
    PORT = config.get("port", "8000")
    XIANYU_API_URL = config.get("xianyu_api_url", "")

    # 同时设环境变量（兼容其他工具）
    os.environ["PARSER_API_URL"] = PARSER_API_URL
    os.environ["PORT"] = PORT
    if XIANYU_API_URL:
        os.environ["XIANYU_API_URL"] = XIANYU_API_URL

    return True
