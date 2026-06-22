# Visual Agent (MOYAG) 项目全景文档

> 最后更新：2026-06-12  
> 角色：Andrew Wang（王佳楠），沐源甲科技 · 双子智擎

---

## 1. 项目背景

| 项目 | 详情 |
|------|------|
| **名称** | Visual Agent（代号 MOYAG） |
| **公司** | 沐源甲科技 |
| **访问地址** | http://47.237.203.217/ |
| **部署平台** | 阿里云 ECS（8C/16G，100G SSD，5Mbps） |
| **核心功能** | 上传产品资料（PDF/PPT/Word/文字描述）→ AI 自动提取卖点 → 生成六类视觉素材 |
| **当前状态** | P0-P2 全部完成（33/33 设计功能），进入 P3+ 双引擎阶段 |

**六类生成素材：**
- 主图方案 + Prompt
- 白底图
- 场景图（1-3 个使用场景）
- 卖点图（3-5 个模块）
- 视频脚本（15+30 秒分镜）
- 广告素材方案

**用户流程：**
```
文档上传/文字输入 → 结构化解析(BriefReviewPanel) → 追问补全 → 创意策略预览(StrategyPanel) → 六类素材并行生成 → Canvas 编辑 → 多平台导出
```

---

## 2. 代码库结构

### 2.1 总体目录

```
/opt/visual-agent/
├── app/backend/           # Python 后端 (FastAPI)
│   ├── app/
│   │   ├── agents/        # Agent 编排器（orchestrator）
│   │   ├── api/           # 路由层（17 个路由文件）
│   │   ├── db/            # SQLAlchemy CRUD
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic 模式
│   │   └── services/      # 业务逻辑（37 个服务）
│   ├── tests/             # 294 个测试
│   │   ├── unit/          # 单元测试
│   │   └── integration/   # 集成测试（含真实 LLM 调用）
│   └── main.py            # FastAPI 入口
├── frontend/              # React 前端
│   ├── src/
│   │   ├── api/           # API 客户端 (axios)
│   │   ├── components/    # UI 组件（23 个）
│   │   ├── pages/         # 页面组件
│   │   └── types/         # TypeScript 类型
│   └── dist/              # 构建产物（Nginx 静态托管）
├── .env                   # 环境变量（17 行，含 API Keys）
└── backups/               # 原始设计文档
```

### 2.2 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12.3 | 运行时 |
| FastAPI | 0.136.3 | Web 框架 |
| Uvicorn | 0.48.0 | ASGI 服务器 |
| SQLAlchemy | 2.0.50 | ORM |
| Pydantic | 2.13.4 | 数据校验 |
| DeepSeek | v4-pro | 主力 LLM |
| OpenAI SDK | 2.40.0 | 统一 LLM 调用接口 |
| pytest | 9.0.3 | 测试框架 |
| Alembic | 1.18.4 | 数据库迁移 |
| Redis | 8.0.0 | 缓存 / 异步任务状态 |
| python-docx | 1.2.0 | Word 导出 |
| openpyxl | 3.1.5 | Excel 处理 |
| PyPDF2 | 3.0.1 | PDF 解析 |
| rembg | 2.0.75 | 背景移除 |
| Pillow | 12.2.0 | 图片处理 |

### 2.3 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.2.6 | UI 框架 |
| TypeScript | 6.0.2 | 类型系统 |
| Vite | 8.0.12 | 构建工具 |
| Tailwind CSS | 3.4.19 | 样式 |
| React Router | 7.17.0 | 路由 |
| TanStack Query | 5.101.0 | 数据获取 |
| Axios | 1.17.0 | HTTP 客户端 |

### 2.4 后端核心路由

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/v1/projects` | GET/POST/DELETE | 项目管理 |
| `/api/v1/generate-async` | POST | 异步提交生成任务 |
| `/api/v1/generation/task/{id}` | GET | 轮询任务状态 |
| `/api/v1/strategy/preview` | POST | 策略预览（含追问） |
| `/api/v1/briefs/parse` | POST | 简报解析 |
| `/api/v1/brand/*` | CRUD | 品牌管理 |
| `/api/v1/assets/*` | CRUD | 素材管理 |
| `/api/v1/canvas/*` | - | 画布操作 |
| `/api/v1/copywriting/*` | - | 文案生成 |
| `/api/v1/layout/*` | - | 布局生成 |
| `/api/v1/auth/*` | - | 账号注册/登录/切换/存档 |
| `/health` | GET | 健康检查 |

### 2.5 Provider 架构

后端采用 Provider 注册表模式，支持运行时切换：

```
LLM:   DeepSeek v4-pro（主力）+ OpenAI-compatible providers
Image: Mige API GPT Image-2（主力，异步轮询）/ DALL-E 3 / Pollinations
Video: Mige API grok-video-3 / veo3.1（主力）/ Runway Gen-3 / Pika
```

核心文件：`app/services/llm_provider.py` — 抽象 Provider 基类，DeepSeek 通过 OpenAI SDK 兼容接口调用。

---

## 3. 架构设计

### 3.1 系统架构

```
Layer 1: Web Frontend
   ├── React + TypeScript + Vite
   ├── 项目入口、资料库、画布工作台
   └── 多端素材预览与编辑

Layer 2: API Backend
   ├── FastAPI 路由与业务服务
   ├── 项目、素材、品牌资产、生成任务管理
   └── 统一鉴权与数据隔离

Layer 3: Generation Providers
   ├── LLM / Image / Video Provider 注册表
   ├── 异步任务轮询与状态回填
   └── 可观测的生成进度记录

Layer 4: Storage & Deployment
   ├── PostgreSQL + 本地上传目录
   ├── Nginx + systemd 部署
   └── GitHub 代码托管与备份
```

### 3.2 TDD 工作管线

```
RED: 写失败测试，定义期望行为
  → GREEN: 实现最小代码使测试通过
  → REFACTOR: 在测试保护下整理实现

自检四步（每次改动后必执行）：
  ① npx tsc --noEmit（TypeScript 编译）
  ② npm run build（前端构建）
  ③ pytest tests/ -q（全量后端测试）
  ④ curl localhost:8000/health（服务健康）
```

### 3.3 异步生成流程

```
POST /generate-async → 立即返回 task_id + status=pending
  → 后台 6 路并行 DeepSeek 生成（2-3 分钟）
  → 前端每 3 秒轮询 GET /generation/task/{id}
  → status=complete → 跳转结果页
```

---

## 4. 当前瓶颈与未完成项

### 4.1 性能瓶颈

| 瓶颈 | 详情 | 影响 |
|------|------|------|
| **生成耗时** | 6 路并行 DeepSeek 调用需要 2-3 分钟 | 用户等待时间较长 |
| **ECS 资源** | 4C/4G，Python 3.12 + 前端构建同机 | 峰值时可能 OOM |
| **单机瓶颈** | 所有服务（FastAPI + Redis + Nginx）同机 | 无横向扩展能力 |
| **DeepSeek 限流** | API 有速率限制，重试机制增加延迟 | 高峰期可能排队 |

### 4.2 已知运维坑点

| 问题 | 表现 | 解决方案 |
|------|------|----------|
| **uvicorn 自动重载** | 编辑 .py 文件触发 reload → 多进程抢端口 → 服务崩溃循环 | `fuser -k 8000/tcp; systemctl restart visual-agent` |
| **compliance.py 依赖** | 该文件已改为 shim 但不可删除 | 保留空文件，勿删 |
| **API Key 脱敏** | Windows 本地无法直接提取 ECS 上的 API Key | 需用户手动在 ECS 上设置环境变量 |
| **Nginx 配置锁定** | 修改会被拦截 | 需用户手动执行 |
| **heredoc/sed 转义** | SSH 中含特殊字符的命令会失败 | 先本地写文件再 scp 上传 |
| **会话膨胀** | 超 200 条消息 / 100KB 工具输出后上下文膨胀 | 主动建议 /new 开新会话 |

### 4.3 未完全自动化项

| 项 | 状态 | 说明 |
|-----|------|------|
| GitHub SSH Key (ECS) | 已生成，待添加 | 需在 github.com/settings/keys 添加 `ECS Alibaba` |
| GitHub SSH Key (Windows) | 已生成，待添加 | 需添加 `Windows Binjiang` |
| ECS Git 推送 | 待验证 | GitHub Key 添加后可 push 到 krukteresa413-ops/visual-agent |
| GBrain Vault | 待初始化 | `~/.gbrain/vault/` 不存在 |

### 4.4 设计文档状态

设计文档：33/33 = 100%，P0a + P0b + P1 + P2 全部完成  
代码精简：42 → 37 services  
compliance.py：不可删除的 shim

---

## 5. SSH 连接与部署信息

### 5.1 ECS 服务器

| 项目 | 详情 |
|------|------|
| **IP** | 47.237.203.217 |
| **用户** | root |
| **认证** | SSH Key|
| **系统** | Ubuntu |
| **Python** | 3.12.3（系统）/ .venv（项目虚拟环境） |
| **前端服务** | Nginx（80 端口）→ `/opt/visual-agent/frontend/dist/` |
| **后端服务** | systemd（`visual-agent.service`）→ 127.0.0.1:8000 |
| **Redis** | 本地 6379 |
| **PostgreSQL** | 本地 |

### 5.2 连接命令

```bash
# SSH 连接
ssh root@47.237.203.217
ssh -o ConnectTimeout=30 root@47.237.203.217

# SCP 上传文件
scp -o ConnectTimeout=30 <local_file> root@47.237.203.217:<remote_path>
```

### 5.3 服务管理

```bash
# 重启后端（编辑代码后必须手动重启，不能依赖自动重载！）
ssh root@47.237.203.217 "fuser -k 8000/tcp; sleep 2; systemctl restart visual-agent"

# 重载 Nginx
ssh root@47.237.203.217 "nginx -s reload"

# 前端构建部署
ssh root@47.237.203.217 "cd /opt/visual-agent/frontend && npx tsc --noEmit && npm run build && nginx -s reload"

# 运行测试
ssh root@47.237.203.217 "cd /opt/visual-agent/app/backend && .venv/bin/python -m pytest tests/ -q"

# 健康检查
curl http://47.237.203.217/health
```

### 5.4 GitHub 仓库

| 仓库 | URL | 用途 |
|------|-----|------|
| **ECS 项目** | `git@github.com:krukteresa413-ops/visual-agent.git` | Visual Agent 代码托管 |
| **Windows 知识库** | `git@github.com:721AndrewWang/gbrain-vault.git` | GBrain Vault 备份 |

### 5.5 API Keys 位置

| Key | 环境变量 | 服务 |
|-----|----------|------|
| DeepSeek | `DEEPSEEK_API_KEY` | LLM 调用 |
| OpenAI | `OPENAI_API_KEY` | 备选 Provider |
| HappyHorse | `HAPPYHORSE_API_KEY` | 图片生成 |
| MigeAPI | `MIGEAPI_API_KEY` | 米格 API（图片/视频） |
| 阿里云 OSS | `ALIBABA_CLOUD_ACCESS_KEY_*` | 对象存储 |
| 阿里云 OSS | `OSS_BUCKET/REGION/ENDPOINT` | OSS 配置 |

> 注：API Key 受系统脱敏保护，Windows 本地无法提取，需用户在 ECS 上手动设置。

---

## 6. 备份策略

### 6.1 ECS Git 备份

```cron
# 每 3 小时全量快照
0 */3 * * * /root/scripts/git-full-backup.sh >> /var/log/git-backup.log 2>&1
```

备份脚本流程：
```bash
cd /opt/visual-agent
git add -A
git diff --cached --quiet || git commit -m "auto: hourly backup $(date -Iminutes)"
git push origin master
```

### 6.2 本地 GBrain Vault

```cron
# 每天 23:00
0 23 * * * cd "GBrain Vault" && git add -A && git commit && git push
```

### 6.3 桌面 SSH 密钥文件

`C:\Users\EDY\Desktop\GitHub_SSH_Key.md` — 包含两台机器的 SSH 公钥：
- `Windows Binjiang`：Windows 台式机
- `ECS Alibaba`：阿里云 ECS 服务器

---

## 7. 开发约定

1. **中文优先**：所有沟通和文档使用中文
2. **严格 TDD**：每行生产代码必须先有失败测试
3. **逐步推进**：每步确认后才进入下一步
4. **凝练沟通**：避免啰嗦
5. **菱形集群**：首页 45° 旋转 + 毛玻璃 + 十字排列，不可移除
6. **自检铁律**：每次代码改动后必须四步自检
7. **长会话警戒**：超 200 条消息或 100KB 工具输出时建议开启新上下文
