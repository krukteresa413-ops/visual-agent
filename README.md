# MOYAG — AI 视觉素材自动生成平台

> 🟢 **在线演示**: http://47.237.203.217/  
> 📦 **仓库**: github.com/krukteresa413-ops/visual-agent  
> 👤 **负责人**: WJN  
> 📅 **最后更新**: 2026-06-12

---

## 一、项目简介

MOYAG（沐源甲科技）是一个 AI 驱动的产品视觉素材自动生成平台。用户上传产品资料（PDF/PPT/Word 或文字描述），AI 自动提取卖点、制定创意策略，并生成**多类视觉素材(可补充)**：

| 类型 | 说明 |
|------|------|
| 🖼️ 主视觉 | 产品主图，支持多平台尺寸适配 |
| ⬜ 白底图 | 电商标准白底产品图 |
| 🎬 场景图 | 多场景产品展示图 |
| 💎 卖点图 | 核心卖点可视化卡片 |
| 📹 视频脚本 | 短视频/直播脚本 |
| 📢 广告素材 | 平台适配的广告物料 |

## 二、核心功能

- **文档解析** — 支持 PDF / PPT / DOCX / XLSX / TXT / CSV / 图片上传，AI 自动提取产品信息
- **结构化追问** — 缺失信息自动生成追问卡片，用户补充后继续
- **创意策略** — AI 先生成视觉方向策略，确认后再出图（"先出方向再出图"）
- **品牌记忆** — 自动学习品牌风格（颜色/字体/调性），跨项目复用
- **多平台适配** — 淘宝 / 小红书 / 抖音 / 拼多多 / 微信 / 美团 / Amazon / 阿里国际，自动调整尺寸和文案风格
- **合规检查** — 自动检测广告法禁用词、文化禁忌
- **AI 图片生成** — 接入 Mige API（GPT Image-2），异步生成+轮询
- **账号系统** — 邮箱/手机号注册登录，服务端 JWT 鉴权，多账号数据随后端项目同步

## 三、技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI (Python) | 3.12 |
| AI 引擎 | DeepSeek + OpenAI-compatible providers | — |
| 数据库 | PostgreSQL + SQLAlchemy | — |
| 前端框架 | React + TypeScript | — |
| 构建工具 | Vite | 8.x |
| CSS | Tailwind CSS | 3.x |
| 路由 | React Router | 6.x |
| 部署 | Nginx + systemd (阿里云 ECS) | — |
| 代码仓库 | GitHub (private) | — |

## 四、项目结构

```
/opt/visual-agent/
├── app/backend/                # Python 后端
│   ├── app/
│   │   ├── api/                # 17 个路由模块
│   │   ├── services/           # 37 个服务模块
│   │   ├── models/             # 数据库模型
│   │   ├── schemas/            # Pydantic 数据模型
│   │   ├── agents/             # 多 Agent 编排
│   │   └── prompts/            # Jinja2 模板
│   └── tests/                  # 294 个测试用例
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   ├── components/         # UI 组件（23 个）
│   │   └── types/              # TypeScript 类型
│   └── dist/                   # 构建产物
└── .env                        # 环境变量（API Keys）
```

## 五、当前进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0a | 核心闭环（DAG 编排、Canvas、品牌学习、淘宝导出） | ✅ 完成 |
| P0b | 多平台适配 + Mockup Agent | ✅ 完成 |
| P1 | 质量增强（视觉方向、字体检查、版本对比） | ✅ 完成 |
| P2 | 创意策略 + 资产推荐 + 导出打包 | ✅ 完成 |
| P3+ | 引擎调度、上下文记忆、竞品分析 | 📋 设计中 |



## 六、快速开始（开发者）

```bash
# 连接服务器
ssh root@47.237.203.217

# 后端
cd /opt/visual-agent/app/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 运行测试
pytest tests/ -q

# 前端构建
cd /opt/visual-agent/frontend
npm run build

# 重启服务
systemctl restart visual-agent
```

## 七、相关文档

| 文档 | 说明 |
|------|------|
| `docs/MOYAG_项目全景.md` | 8 章节项目全景（架构/部署/约定） |
| `docs/MOYAG_设计文档.md` | 6 阶段 33 功能完整设计 |
| `docs/API.md` | API 接口文档 |

## 八、联系方式

- **Agent相关**: WJN
- **服务器**: 阿里云 ECS（47.237.203.217，8C/16G/100G/5Mbps）
- **GitHub**: [krukteresa413-ops/visual-agent](https://github.com/krukteresa413-ops/visual-agent) (private)
