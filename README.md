# OmniParse 🔍

> **统一内容解析服务** — 自动识别链接类型，走对应解析通道

自动识别并解析 **抖音、微信公众号、B站、闲鱼** 等平台的内容链接，输出结构化数据。

## 🎯 定位

> **纯解析工具，永不要求登录。就像浏览器一样——甩个链接过来，我打开看，能拿多少给你多少。**

与运营工具的区别：
| | OmniParse（解析器） | 运营平台（platforms/） |
|:--|:------------------:|:--------------------:|
| 登录 | ❌ 永不要求 | ✅ 需要扫码登录 |
| 谁用 | 任何人 | 内部运营 |
| 场景 | 别人分享链接「快看这个」 | 搜索、管理、回复、数据分析 |
| 数据 | 页面公开可见的内容 | 完整数据 + 操作能力 |

## ✨ 特性

- 🎯 **自动识别** — 丢一个链接进来，自动判断是什么平台
- 📹 **抖音视频** — 标题/文案/作者/互动数据/无水印视频直链
- 📰 **公众号文章** — 兼容标准图文 & 图文模式，全文提取
- 🎬 **B站视频** — 标题/UP主/播放/点赞/硬币数据
- 🏪 **闲鱼商品** — 商品标题/价格/描述/图片
- 🐳 **Docker 部署** — 一键运行，API 调用

## 🚀 快速开始

```bash
# 启动服务（首次会自动生成配置模板）
docker run -d --name omni-parse -p 【你的端口】:8000 omni-parse
```

> ⚠️ **首次启动会自动生成配置模板，填写必要配置后重启才能使用。**

## 配置说明

首次启动后，进入容器或挂载目录编辑 `config.yaml`：

```yaml
# 【必填】抖音解析 API 地址
parser_api_url: "http://【你的解析服务地址】:【端口】"

# 【可选】服务端口
port: 8000
```

编辑后重启容器即可。

## 📖 API 用法

```bash
# 解析链接（自动识别平台）
curl "http://【你的地址】/api/parse?url=https://mp.weixin.qq.com/s/xxx"

# 只看平台识别
curl "http://【你的地址】/api/identify?url=https://v.douyin.com/xxx"

# 完整内容
curl "http://【你的地址】/api/parse?url=https://...&verbose=true"
```

## 🔧 本地开发

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## ⚙️ 配置

支持通过环境变量配置：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `PORT` | 服务端口 | `8000` |
| `PARSER_API_URL` | 内容解析服务 API 地址 | （必填，用户自定义） |
| `XIANYU_API_URL` | 闲鱼外部解析 API（可选） | 空 |

## 📦 项目结构

```
omni-parse/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py              # API 入口 + 路由器
│   └── parsers/
│       ├── douyin.py         # 抖音解析器
│       ├── wechat.py         # 公众号解析器
│       ├── bilibili.py       # B站解析器
│       └── xianyu.py         # 闲鱼解析器
└── github-publish.py         # GitHub 发布工具
```

## 🗺️ 路线图

- [x] 抖音视频解析
- [x] 公众号文章解析（多格式兼容）
- [x] B站视频解析
- [ ] 闲鱼商品完整解析（Playwright 增强）
- [ ] 抖音账号作品列表
- [ ] 图片内容分析
- [ ] 更多平台支持

## 📄 License

MIT
