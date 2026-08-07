# 启动说明 · 太平洋金科·智能行政咨询助手

## 环境要求

| 项 | 要求 |
|----|------|
| Python | **3.11+**（本机已用 `/opt/homebrew/bin/python3.13` 创建项目根目录 `.venv`） |
| Node.js | 18+（前端 Vite） |
| 数据库 | 默认 SQLite（`backend/.env` 中 `DATABASE_URL`） |
| 向量索引 | 本地文件（可选 FAISS；无则 numpy） |
| PyCore | 通过 `PYTHONPATH=..` 引用仓库上级/同级 `pycore`，**勿 pip 安装** |

## 依赖安装（由你执行）

```bash
# 后端虚拟环境（本机已建好时可跳过）
cd "/Users/wangxinyu/Downloads/开发规范包_V2"
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt   # 含 loguru、httpx、python-pptx

# 前端
cd frontend
npm install
```

## 配置

- 后端配置文件：`backend/.env`（应用内通过 Settings 读取，**不要**在代码里用 `os.getenv`）
- 前端：`frontend/.env` 或环境变量  
  - `VITE_API_BASE_URL=/api`（开发时走 Vite 代理）  
  - `VITE_USE_MOCK=false`（接真后端）

### 百炼 LLM（可选，推荐）

在 [百炼控制台](https://bailian.console.aliyun.com/) 创建 API Key，写入 `backend/.env`：

```env
LLM_API_KEY=sk-你的密钥
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_GENERATE=qwen-plus
LLM_MODEL_INTENT=qwen-turbo
LLM_MODEL_EMBEDDING=text-embedding-v3
```

未填 Key 时对话仍可用（知识模板降级）。修改 `.env` 后需**重启后端**。  
健康检查：`http://localhost:8010/api/health` → `data.llm.configured` 应为 `true`。

## 启动命令（重要）

> **请在你自己的 Cursor 终端里启动**（点终端 `+` 开两个窗口）。  
> 不要依赖对话里 Agent 后台拉起的进程——那些任务会被系统中断，所以你会觉得「老是挂」。

**终端 1 — 后端（8010，避开旧的 8000）**

```bash
cd "/Users/wangxinyu/Downloads/开发规范包_V2"
bash scripts/dev-backend.sh
```

或手动：

```bash
cd "/Users/wangxinyu/Downloads/开发规范包_V2"
source .venv/bin/activate
cd backend
PYTHONPATH=.. python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8010
```

**终端 2 — 前端（5173）**

```bash
cd "/Users/wangxinyu/Downloads/开发规范包_V2"
bash scripts/dev-frontend.sh
```

浏览器打开：`http://localhost:5173`（前端经 Vite 把 `/api` 代理到 `8010`）

健康检查：`http://localhost:8010/api/health`

## 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `emp` | `123456` | 员工 |
| `agent` | `123456` | 坐席 |
| `admin` | `123456` | 运营管理员 |

## 功能入口速查

| 角色 | 路径示例 |
|------|----------|
| 员工 | 工作台对话、服务目录、我的任务、转人工工单、材料中心、消息、设置 |
| 坐席 | 坐席队列、会话工作台、任务审批、SLA 看板、质检与回访 |
| 运营 | 知识管理、意图/SLA、洞察（指标+Bad Case）、权限审计 |

## 新增 API（B8–B10）

| 前缀 | 说明 |
|------|------|
| `/api/materials` | 材料上传 / 列表 / 重试解析 / 关联任务 |
| `/api/qa/*` | 质检记录与回访任务（agent/admin） |
| `/api/notifications` | 站内消息聚合与已读 |
| `/api/users/me/preferences` | 个人偏好 |
| `/api/content` | 改写 / 报告草稿 / 权限内数据导出 |

材料文件目录：`backend/data/uploads/materials/`（随 `UPLOAD_DIR`）。

## 说明

- 首次启动会自动建表并写入演示种子（用户、知识、服务目录、Skill、意图/SLA/Bad Case、质检回访）。
- 写操作（知识发布、Skill 确认、转人工、任务审批、运营配置变更）会写入审计日志，可在运营端「权限与安全审计」查看。
- 材料解析为 **简易抽文本 / 图片元数据**，非真 OCR。
- 员工顶栏「待办」→ `/tasks`，「未读」→ `/messages`；坐席结案后队列/工作台列表即时刷新。
- 交付状态：B0–B10 已完成，详见 `.output/plan.md`。
