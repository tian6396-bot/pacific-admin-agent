# 开发计划 — 太平洋金科·智能行政咨询助手

> 依据：`.output/PRD.md`、`.output/prototype-final.md`、`.output/ui-design-spec.md`（2026-08-06 定稿）  
> 节奏：前端 Mock 全页（按定稿大改）→ 用户验收 → 后端逐功能

---

## 一、前端开发（定稿大改 · V2）

> 旧 27 页实现已验收过一轮；本轮按 **25 页 + Agent 优先** 重构。完成后需用户**二次验收**。

### 基础设施
- [x] 项目初始化（Vue 3 + TypeScript + Pinia + Router + 设计变量）
- [x] 三端布局 + 鉴权 + axios + MockBadge
- [x] ECharts 封装（P12/P15/P24）
- [x] 路由/菜单对齐 25 页 IA（去掉办理记录独立页、协同独立页；合并洞察）
- [x] 员工顶栏对齐定稿（全部服务不进顶栏并列）

### 页面清单（定稿编号）

#### P01 登录
- 功能：账号密码；按角色跳转 P02/P12/P17
- Mock：emp / agent / admin
- 跳转：→ `/workbench` | `/agent/queue` | `/ops/knowledge`
- [x] 已有；仅校验跳转文案
- [x] 二次验收勾选

#### P02 Agent 首页
- 功能：左会话/P0/全部服务；中问候+大输入+建议问法；顶栏待办摘要
- Mock：建议问法 4 条；最近会话；P0 四项
- 跳转：发问→P03；全部服务→P04；P0→P03/P05
- [x] 开发完成

#### P03 智能对话
- 功能：三栏；来源引用；确认卡片；转人工；全部服务入口
- Mock：差旅问答 + 请假确认卡
- 跳转：←P02；→P06/P08/P09
- [x] 开发完成（按定稿增强）

#### P04 全部服务
- 功能：域列表 + 紧凑事项表（非门户卡片墙）
- Mock：8 域；P0/P1 事项
- 跳转：→P05 或回 P02
- [x] 开发完成

#### P05–P11 员工其余页
- P05 申请确认 / P06 任务（含历史 Tab）/ P07 详情 / P08 工单 / P09 材料 / P10 消息 / P11 设置
- [x] 骨架已有
- [x] P06 并入历史 Tab；去掉独立 `/records` 导航
- [x] 二次验收勾选

#### P12–P16 坐席
- 去掉顶栏「协同专家」；专家协同进 P14 抽屉
- [x] 各页骨架已有
- [x] 菜单与 P14 抽屉对齐定稿
- [x] 二次验收勾选

#### P17–P25 运营
- P18 知识解析详情（新增）
- P21 Skill（原 Workflow 改名）
- P24 运营洞察（合并 Bad Case + 指标）
- P19–P23、P25 菜单文案对齐
- [x] P18 / P24 开发完成
- [x] 其余页菜单与文案对齐
- [x] 二次验收勾选

### 前端验收
- [x] 用户启动二次验收通过（定稿大改）

---

## 二、后端开发

> 前端二次验收：已确认通过（2026-08-07）  
> 环境：用户确认采用建议默认（Python=`python3`，venv=`.venv`，JWT_SECRET=`change-me-dev`，LLM 先空）

### Python 环境
- **Python 指令**：`/opt/homebrew/bin/python3.13`（系统 `python3` 为 3.9，实际用 3.13 建 venv）
- **虚拟环境名称**：`.venv`（项目根目录）
- [x] 用户已确认 Python 指令
- [x] 用户已创建虚拟环境并完成依赖安装（见下方 B0 测试引导）

### 配置项（写入 `backend/.env`，B0 落盘）
| 配置项 | 确认值 |
|--------|--------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/app.db` |
| `HOST` | `0.0.0.0` |
| `PORT` | `8000` |
| `DEBUG` | `true` |
| `CORS_ORIGINS` | `["http://localhost:5173"]` |
| `JWT_SECRET` | `change-me-dev` |
| `JWT_EXPIRE_MINUTES` | `1440` |
| `UPLOAD_DIR` | `./data/uploads` |
| `VECTOR_INDEX_DIR` | `./data/faiss` |
| `QA_SIMILARITY_THRESHOLD` | `0.8` |
| `SHORT_MEMORY_TURNS` | `3` |
| `INTENT_CONFIDENCE_THRESHOLD` | `0.7` |
| `LLM_API_KEY` / `LLM_BASE_URL` / 模型名 | 空（后续功能再补） |
| `SEED_DEMO_USERS` | `true` |

### 功能依赖图
```
B0 基础设施（可启动 /health）
 └─ B1 登录鉴权 + 基础 RBAC
      ├─ B2 知识入库与发布
      ├─ B3 智能对话主链 + WebSocket
      ├─ B4 服务目录与申请 → 任务
      ├─ B5 转人工 / 坐席队列与工作台
      ├─ B6 Skill / 工具调用
      └─ B7 运营配置与看板 / 审计
           ├─ B8 材料中心（简易解析）
           ├─ B9 质检与回访
           └─ 轻量：消息 / 设置 / SLA 看板
```

### 功能清单（按依赖顺序）
| 序号 | 描述 | 对应入口 | 状态 |
|------|------|----------|------|
| B0 | 后端可启动，健康检查可访问 | `/api/health` | 用户已确认通过 |
| B1 | 登录 + RBAC | 登录页 | 已完成（用户确认） |
| B2 | 知识发布与检索 | P17/P18/P03 | 已完成（用户确认继续） |
| B3 | 对话主链 + WS | P02/P03 | 已完成（用户确认继续） |
| B4 | 服务申请→任务 | P04/P05/P06 | 已完成（用户确认继续） |
| B5 | 转人工/坐席 | P03/P12/P13 | 已完成（用户确认继续） |
| B6 | Skill/工具/确认闸 | P03/P21/P22 | 已完成（用户确认继续） |
| B7 | 运营配置与洞察审计 | P19–P25 | 已完成（用户确认继续） |
| B8 | 材料中心（上传+简易解析） | P09 | 已完成（用户确认继续） |
| B9 | 质检与回访 | P16 | 已完成（用户确认继续） |
| B10 | 消息/设置/SLA 看板去 Mock | P10/P11/P15 | 已完成（用户确认继续） |
| B11 | 百炼 LLM 接入（生成回答） | P03 | 已交付，待填 Key 验收 |
| B12 | 内容产出：改写/报告/数据导出 | P03/P06/P07/P13/P24 | 已完成（用户确认继续） |
| B13 | 报告简易 PPTX 导出 | 内容产出 | 已交付，待用户测试 |

---

### B0：基础设施（依赖：无）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 让后端服务能在本机跑起来：配置可读、日志可用、数据库可初始化、浏览器/接口能访问 `/health`，为后续登录等功能打底。

#### 预计涉及文件
- 新建：`backend/requirements.txt`
- 新建：`backend/.env`、`backend/.env.example`
- 新建：`backend/src/core/config.py`（AppSettings）
- 新建：`backend/src/db/session.py`（异步引擎 / 会话 / init_db）
- 新建：`backend/src/db/models.py`（最小占位，可先空或仅 Base）
- 新建：`backend/src/api/routes/health.py`
- 新建：`backend/src/main.py`（PyCore APIServer 入口）
- 新建：`backend/data/`（运行时目录，gitignore 数据文件）
- 如需：根目录 `.gitignore` 补充 `backend/.env`、`.venv`、`backend/data/`

#### 分层实现思路
- [x] **层 1：配置与依赖清单**
  - 目标：用 `BaseSettings` 固化已确认的配置项；列出 pip 依赖（FastAPI/uvicorn/SQLAlchemy/aiosqlite 等）。`pycore` 不 pip 安装，靠 `PYTHONPATH=..`。
  - 产出：`requirements.txt`、`.env` / `.env.example`、`src/core/config.py`。

- [x] **层 2：ORM / 数据库会话底座**
  - 目标：异步引擎连上 SQLite，启动时能建表（即便暂无业务表也要跑通 init）。
  - 产出：`src/db/session.py`、`src/db/models.py`（Base）。

- [x] **层 3：Repository**
  - 目标：本功能暂不需要业务 Repository。
  - 产出：无。

- [x] **层 4：Service**
  - 目标：本功能暂不需要业务 Service；健康检查可直接在路由返回状态与关键配置摘要（不含密钥）。
  - 产出：无独立 Service 文件。

- [x] **层 5：API 路由 + 应用入口**
  - 目标：挂上 `/api/health`（与前端 `VITE_API_BASE_URL=/api` 约定一致）；PyCore 另有根路径 `/health`。
  - 产出：`src/api/routes/health.py`、`src/main.py`。

- [x] **层 6：前端联调**
  - 目标：B0 不改前端页面；浏览器/curl 直连健康检查即可。登录联调留给 B1。
  - 产出：CORS 指向 `5173`；端口 `8000`。

#### 用户测试思路
- 测试入口：`http://localhost:8000/api/health`（或 `/health`）
- 触发方式：按下方测试引导创建 `.venv`、安装依赖、启动 uvicorn
- 成功表现：`data.status` 为 `ok`（或根路径 `status=healthy`），日志无报错
- 排查重点：是否忘记 `PYTHONPATH=..`、是否在 `backend/` 目录启动、`.env` 是否存在

- [x] **用户测试通过（本人执行后勾选）**

---

### B1：登录鉴权 + 基础 RBAC（依赖 B0）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 用户能用账号密码登录，拿到 JWT；后端能根据角色做基础鉴权；前端登录页可关掉 Mock，接到真实接口，并按角色跳到员工/坐席/运营首页。

#### 预计涉及文件
- 新建：`backend/src/models/auth.py`（LoginRequest / TokenResponse / UserPublic）
- 新建：`backend/src/repositories/user.py`
- 新建：`backend/src/services/auth_service.py`（登录、密码校验、发 JWT、种子用户）
- 新建：`backend/src/api/deps.py`（解析 Bearer Token、当前用户、角色校验）
- 新建：`backend/src/api/routes/auth.py`（`POST /api/auth/login`、`GET /api/auth/me`）
- 修改：`backend/src/db/models.py`（User 表）
- 修改：`backend/src/main.py`（注册 auth 路由；启动时按需 seed）
- 修改：`backend/requirements.txt`（`bcrypt`、`PyJWT`）
- 修改：`frontend/src/services/authService.ts`（解析统一响应；`VITE_USE_MOCK=false` 时可走真接口）
- 如需：`frontend/.env` / `.env.example` 增加 `VITE_API_BASE_URL`、`VITE_USE_MOCK`

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — `src/models/auth.py`
- [x] **层 2：ORM 表结构** — `User` 表
- [x] **层 3：Repository** — `UserRepository`
- [x] **层 4：Service** — bcrypt + JWT + 种子用户
- [x] **层 5：API 路由 + 依赖** — `/api/auth/login`、`/api/auth/me`
- [x] **层 6：前端联调** — `authService` 解包 `data`；默认 `VITE_USE_MOCK=false`

#### 用户测试思路
- 测试入口：前端登录页；或 `POST /api/auth/login`
- 触发方式：用 `emp/123456`、`agent/123456`、`admin/123456` 登录
- 成功表现：返回 token 与用户信息；前端按角色分别进入工作台 / 队列看板 / 知识管理；带 token 访问 `/api/auth/me` 成功
- 排查重点：是否重装依赖（bcrypt/PyJWT）、旧 SQLite 无 users 表时重启会建表、前端 Mock 是否关掉

- [x] **用户测试通过（本人执行后勾选）**

---

### B2：知识发布与检索（依赖 B1）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 运营能在后台管理 FAQ/文档：上传或新建 → 解析出 Chunk → 校对 → 走「草稿→待审→已发布→已下线」；**只有已发布且在有效期内**的知识能被检索到；为后续对话 RAG（B3）留下可调用的检索接口。本地用 SQLite 存元数据 + FAISS（或等价本地向量文件）建索引；若 LLM Embedding 未配置，用可降级的本地向量/关键词混合方案，保证联调可验。

#### 预计涉及文件
- 新建：`backend/src/models/knowledge.py`（知识条目、Chunk、状态流转、检索请求/响应）
- 新建：`backend/src/repositories/knowledge.py`
- 新建：`backend/src/services/knowledge_service.py`（生命周期与权限校验）
- 新建：`backend/src/services/knowledge_pipeline.py`（上传解析、切分、置信度标记）
- 新建：`backend/src/services/vector_index.py`（本地 FAISS/文件索引的写入与检索）
- 新建：`backend/src/api/routes/knowledge.py`
- 新建：`frontend/src/services/knowledgeService.ts`
- 修改：`backend/src/db/models.py`（KnowledgeDocument / KnowledgeChunk 等表）
- 修改：`backend/src/main.py`（注册知识路由）
- 修改：`backend/requirements.txt`（PDF 解析、向量依赖，如 `pypdf`、`numpy`、`faiss-cpu` 等，以实现时选型为准）
- 修改：`frontend/src/pages/ops/KnowledgePage.vue`、`KnowledgeParsePage.vue`（去掉 Mock，接真接口）
- 如需：`backend/.env.example` 补充向量目录说明（已有 `VECTOR_INDEX_DIR` / `UPLOAD_DIR`）

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — `src/models/knowledge.py`
- [x] **层 2：ORM 表结构** — `KnowledgeDocument` / `KnowledgeChunk`
- [x] **层 3：Repository** — `repositories/knowledge.py`
- [x] **层 4：Service** — 生命周期 + 解析管线 + 本地向量索引（无 LLM 用哈希向量；可选 FAISS）
- [x] **层 5：API 路由** — `/api/knowledge/*`（admin 写，登录用户可读/检索）
- [x] **层 6：前端联调** — P17/P18 接真接口，列表页含试检索

#### 用户测试思路
- 测试入口：`admin/123456` → `/ops/knowledge`；解析页 `/ops/knowledge/:id/parse`
- 触发方式：新建 FAQ → 查看解析 → 提交/发布 → 顶部试检索 → 下线后再检索
- 成功表现：状态流转正确；已发布可召回，下线后不可召回；解析页可见 Chunk
- 排查重点：是否安装 `numpy`/`pypdf`、是否 `admin` 登录、旧库需重启以建新表

- [x] **用户测试通过（本人执行后勾选）**

---

### B3：智能对话主链 + WebSocket（依赖 B1、B2）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 员工能在 Agent 首页发问并进入对话页，看到真实会话列表与消息流；后端按主流程做「知识直答 / 检索问答 / 澄清」并带来源引用；支持 WebSocket 推送回复进度（如 thinking / 最终消息）。本阶段**不实现**完整 Skill 写操作、转人工入队、Planner（留给 B4–B6），但要留出路由占位与「转人工」入口提示。

#### 预计涉及文件
- 新建：`backend/src/models/chat.py`（会话、消息、发问请求、路由结果、引用）
- 新建：`backend/src/repositories/chat.py`
- 新建：`backend/src/services/chat_service.py`（会话 CRUD + 主链编排）
- 新建：`backend/src/services/intent_router.py`（意图/路由：规则 + 可选 LLM，可降级）
- 新建：`backend/src/services/answer_generator.py`（基于检索结果生成带引用回复；无 LLM 时模板降级）
- 新建：`backend/src/api/routes/chat.py`（REST）
- 新建：`backend/src/api/routes/chat_ws.py`（WebSocket，JWT 鉴权）
- 新建：`frontend/src/services/chatService.ts`
- 修改：`backend/src/db/models.py`（ChatSession / ChatMessage）
- 修改：`backend/src/main.py`（注册路由 / WS）
- 修改：`frontend/src/pages/WorkbenchPage.vue`、`ChatPage.vue`（接真接口，去掉硬编码 Mock 会话）
- 如需：复用 B2 `KnowledgeService.search`；配置项沿用 `QA_SIMILARITY_THRESHOLD`、`SHORT_MEMORY_TURNS`、`INTENT_CONFIDENCE_THRESHOLD`

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — `src/models/chat.py`
- [x] **层 2：ORM 表结构** — `ChatSession` / `ChatMessage`
- [x] **层 3：Repository** — `repositories/chat.py`
- [x] **层 4：Service** — 主链编排 + 意图路由 + 模板生成 + WS 推送
- [x] **层 5：API 路由 + WebSocket** — `/api/chat/*`、`/api/chat/ws`
- [x] **层 6：前端联调** — P02/P03 接真接口

#### 用户测试思路
- 测试入口：`emp/123456` → `/workbench` 发问或点建议问法 → `/chat`
- 触发方式：问「深圳酒店住宿标准」「年假还剩几天」；再问「嗯」看澄清；点转人工看占位
- 成功表现：会话列表/消息持久化；回复带来源；右侧证据区有引用；刷新历史仍在
- 排查重点：后端是否已启动且 B2 种子知识在、token 是否有效、WS URL 是否随 API 基址切换

- [x] **用户测试通过（本人执行后勾选）**

---

### B4：服务目录与申请 → 任务（依赖 B1）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 员工能在「全部服务」浏览可办服务（含 P0：报销/请假/IT 报修/会议室），填写申请表并提交后生成**真实任务**；在「我的任务」按进行中/待审批/历史/Planner 查看，并能打开任务详情看进度时间线。本阶段提交即建任务并走简易状态流转（含审批人视角的待审批），**不实现**真实外部工具写回与完整 Skill 状态机（留给 B6）。

#### 预计涉及文件
- 新建：`backend/src/models/service.py`、`backend/src/models/task.py`（或合并为 `catalog_task.py`）
- 新建：`backend/src/repositories/service.py`、`backend/src/repositories/task.py`
- 新建：`backend/src/services/catalog_service.py`（服务目录种子与查询）
- 新建：`backend/src/services/task_service.py`（申请建单、列表、详情、审批通过/驳回、简易时间线）
- 新建：`backend/src/api/routes/services.py`、`backend/src/api/routes/tasks.py`
- 新建：`frontend/src/services/catalogService.ts`、`frontend/src/services/taskService.ts`
- 修改：`backend/src/db/models.py`（ServiceItem / Task / TaskEvent）
- 修改：`backend/src/main.py`
- 修改：`frontend/src/pages/ServiceHallPage.vue`、`ServiceApplyPage.vue`、`TasksPage.vue`、`TaskDetailPage.vue`

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — `src/models/catalog.py`
- [x] **层 2：ORM 表结构** — ServiceCatalog / Task / TaskEvent
- [x] **层 3：Repository** — `repositories/catalog.py`
- [x] **层 4：Service** — 目录种子 + 申请建单 + 审批/材料时间线
- [x] **层 5：API 路由** — `/api/services`、`/api/tasks`
- [x] **层 6：前端联调** — P04–P07；坐席端 `/agent/tasks` 待审批

#### 用户测试思路
- 测试入口：`emp` → `/services` 提交申请 → `/tasks`；`agent` → `/agent/tasks?tab=approve` 审批
- 触发方式：报销/请假等表单提交；坐席通过或驳回；申请人可点补充材料
- 成功表现：任务出现在进行中；详情有时间线；审批后进历史
- 排查重点：重启后端以建新表与目录种子；审批须用 agent 账号

- [x] **用户测试通过（本人执行后勾选）**

---

### B5：转人工 / 坐席队列与工作台（依赖 B1、B3）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 员工在对话中发起转人工后，系统创建**工单 + 排队会话**，组装交接包（摘要/意图/证据等）；坐席在队列看板看到排队项与基础 KPI，可**接管**进入会话工作台，与员工通过 WebSocket 互发消息；员工在「我的工单」看到进度。本阶段实现可演示闭环；SLA 精确计时与专家协同抽屉可做简化（超时高亮 + 占位），完整班次排班留给后续。

#### 预计涉及文件
- 新建：`backend/src/models/ticket.py`（工单、队列项、交接包、坐席消息）
- 新建：`backend/src/repositories/ticket.py`
- 新建：`backend/src/services/handoff_service.py`（转人工入队、交接包、接管、结案）
- 新建：`backend/src/api/routes/tickets.py`
- 新建：`backend/src/api/routes/agent_queue.py`（或与 tickets 合并）
- 如需扩展：`backend/src/api/routes/chat_ws.py` / `ws_hub.py`（坐席↔员工房间）
- 新建：`frontend/src/services/ticketService.ts`
- 修改：`backend/src/db/models.py`（Ticket / QueueSession / HandoffMessage 等）
- 修改：`backend/src/services/chat_service.py`（human_review 真正入队，不再仅占位）
- 修改：`backend/src/main.py`
- 修改：`frontend/src/pages/ChatPage.vue`、`TicketsPage.vue`、`agent/QueueBoardPage.vue`、`agent/SessionWorkbenchPage.vue`
- 如需：`TicketHandlePage.vue` 轻量接真工单详情

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — `src/models/ticket.py`
- [x] **层 2：ORM 表结构** — Ticket / TicketMessage
- [x] **层 3：Repository** — `repositories/ticket.py`
- [x] **层 4：Service** — HandoffService（入队/交接包/接管/消息/结案）
- [x] **层 5：API + WS** — `/api/tickets/*`、`/api/agent/*`、房间 `ticket:{id}` / `agent:queue`
- [x] **层 6：前端联调** — Chat 转人工、P08、P12、P13

#### 用户测试思路
- 测试入口：`emp` 对话转人工 → `/tickets`；`agent` → `/agent/queue` 接入 → 工作台回复并结案
- 触发方式：对话点「转人工」或发送「转人工」；坐席接入后互发消息
- 成功表现：队列出现工单与交接包；SLA 超时高亮；员工工单状态变为已解决
- 排查重点：重启后端建 tickets 表；坐席须用 agent 账号

- [x] **用户测试通过（本人执行后勾选）**

---

### B6：Skill / 工具调用 / 确认闸（依赖 B3、B4）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 对话识别到办理类意图后，进入 **Skill 状态机**（补槽 → 校验 → **确认卡片** → 调已登记工具 → 失败补偿）；用户确认前**禁止写操作**。运营可在 P21/P22 查看已发布 Skill 与工具契约（种子 P0：报销/请假/报修/会议室 + 转人工已由 B5 承接）。工具默认走 **Mock 网关**（可配置），成功后联动 B4 创建/更新任务。本阶段不要求真接外部 OA；完整 13 Skills / 36 工具以种子清单可浏览，运行时优先打通 P0。

#### 预计涉及文件
- 新建：`backend/src/models/skill.py`（Skill 定义、运行实例、确认请求、工具契约）
- 新建：`backend/src/repositories/skill.py`
- 新建：`backend/src/services/skill_service.py`（状态机 + ConfirmGate）
- 新建：`backend/src/services/tool_gateway.py`（Mock/HTTP 工具调用、超时/幂等键）
- 新建：`backend/src/api/routes/skills.py`、`backend/src/api/routes/tools.py`
- 新建：`frontend/src/services/skillService.ts`
- 修改：`backend/src/db/models.py`（SkillDef / ToolDef / SkillRun）
- 修改：`backend/src/services/chat_service.py` / `intent_router.py`（skill 路由真正启状态机并回传确认卡）
- 修改：`backend/src/main.py`
- 修改：`frontend/src/pages/ChatPage.vue`（确认卡片接真）、`ops/WorkflowsPage.vue`（Skill 列表）、工具页（若有 ToolsPage）
- 如需：确认后调用 `TaskService.apply` 建任务

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — `src/models/skill.py` + Chat `confirm_card`
- [x] **层 2：ORM 表结构** — SkillDef / ToolDef / SkillRun
- [x] **层 3：Repository** — `repositories/skill.py`
- [x] **层 4：Service** — Skill 状态机 + ConfirmGate + Mock ToolGateway
- [x] **层 5：API 路由** — `/api/skills`、`/api/tools`、确认/取消
- [x] **层 6：前端联调** — Chat 确认卡；P21/P22 真数据

#### 用户测试思路
- 测试入口：`emp` 对话「帮我请假 3 天」→ 确认卡 → 确认办理
- 触发方式：确认后跳任务；取消则无写操作；`admin` 看 `/ops/skills`、`/ops/tools`
- 成功表现：未确认不建任务；确认后 Mock 工具成功且任务可见
- 排查重点：重启后端种子 Skill/Tool；办理类问法勿带过强「制度问答」措辞以免走 RAG

- [x] **用户测试通过（本人执行后勾选）**

---

### B7：运营配置与洞察审计（依赖 B1–B6）

> 分层实现思路由 feature-plan skill 生成，用户确认后动工。

#### 功能目标
- 运营端能管理**意图/Prompt、队列 SLA 配置、Bad Case、核心指标看板、权限矩阵与审计日志**；配置发布后运行时只读已发布项（MVP 无灰度）。知识/Skill/工具/服务目录已在前序功能具备，本功能补齐 P20/P23/P24/P25（P19 可复用 B4 目录只读或轻量发布）。交付后输出 `.output/startup.md` 启动说明，作为后端阶段收尾。

#### 预计涉及文件
- 新建：`backend/src/models/ops.py`（Intent、SLA 配置、BadCase、AuditLog、指标摘要）
- 新建：`backend/src/repositories/ops.py`
- 新建：`backend/src/services/ops_service.py`（配置 CRUD/发布、Bad Case 闭环、指标聚合、写审计）
- 新建：`backend/src/api/routes/ops.py`
- 新建：`frontend/src/services/opsService.ts`
- 修改：`backend/src/db/models.py`（IntentDef / SlaConfig / BadCase / AuditLog）
- 修改：关键写路径（知识发布、任务审批、转人工、Skill 确认等）调用审计埋点（可集中 helper）
- 修改：`backend/src/main.py`（注册路由 + 种子）
- 修改：`frontend/src/pages/ops/IntentsPage.vue`、`QueuesPage.vue`、`InsightsPage.vue`（或 BadCases/Metrics）、`SecurityPage.vue`；如需 `CatalogPage.vue`
- 新建：`.output/startup.md`（环境、启动命令、演示账号、端口）

#### 分层实现思路
- [x] **层 1：Pydantic 模型**
  - 目标：约定意图条目、SLA 参数、Bad Case（7 类 + 状态）、审计记录、看板指标字段，对齐 P20/P23/P24/P25。
  - 产出：请求/响应模型。
  - 说明：配置态统一 draft/published/offline。

- [x] **层 2：ORM 表结构**
  - 目标：落库意图、SLA 配置、Bad Case、审计日志；指标可聚合表或实时统计。
  - 产出：对应表；启动种子若干意图与 SLA 默认值、示例 Bad Case。
  - 说明：审计只追加不改。

- [x] **层 3：Repository**
  - 目标：配置列表/发布、Bad Case 筛选更新、审计分页写入与查询。
  - 产出：运营仓储。
  - 说明：指标聚合可放 Service 读多表。

- [x] **层 4：Service**
  - 目标：意图发布/下线；SLA 读写；Bad Case 登记与标记已改进/忽略；从对话/任务/工单等聚合 KPI；提供 `audit()` 供其它服务调用。
  - 产出：`OpsService` / `EvalInsightService`（可合并）。
  - 说明：权限矩阵前端展示 + 后端角色校验已有，P25 以审计列表 + 角色说明为主。

- [x] **层 5：API 路由**
  - 目标：`/api/ops/*` 仅 admin；覆盖意图、SLA、Bad Case、指标、审计。
  - 产出：统一 `success_response`。
  - 说明：写操作记审计。

- [x] **层 6：前端联调 + 交付文档**
  - 目标：P20/P23/P24/P25 去 Mock；P19 可接目录只读 API；产出 `startup.md`。
  - 产出：opsService + 页面接线 + 启动文档。

#### 用户测试思路
- 测试入口：`admin` → 意图发布、SLA 修改、登记 Bad Case、查看洞察与审计
- 触发方式：再执行一次知识发布或 Skill 确认，审计应新增记录
- 成功表现：配置状态变化可见；Bad Case 可改状态；指标非全 0；审计可按人/动作筛选
- 排查重点：是否 admin、种子是否加载、写路径是否调用了 audit

- [x] **用户测试通过（本人执行后勾选）**

---

### B8：材料中心（依赖 B1、B4）

> 分层实现思路由 feature-plan skill 生成，用户确认全量计划后动工。

#### 功能目标
- 员工可上传材料、查看简易解析状态、关联任务并重试失败项（PDF 抽文本，非真 OCR）。

#### 预计涉及文件
- 新建：`backend/src/models/material.py`、`repositories/material.py`、`services/material_service.py`、`api/routes/materials.py`
- 新建：`frontend/src/services/materialService.ts`
- 修改：`backend/src/db/models.py`、`main.py`、`frontend/src/pages/MaterialsPage.vue`

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — MaterialPublic / 关联更新
- [x] **层 2：ORM** — materials 表
- [x] **层 3：Repository** — 列表/创建/更新
- [x] **层 4：Service** — 上传落盘 + 简易解析状态机
- [x] **层 5：API** — `/api/materials*`
- [x] **层 6：前端联调** — MaterialsPage 去 Mock

#### 用户测试思路
- `emp` 上传 PDF → success；失败可重试；可关联任务

- [x] **用户测试通过（本人执行后勾选）**

---

### B9：质检与回访（依赖 B1、B5）

> 分层实现思路由 feature-plan skill 生成，用户确认全量计划后动工。

#### 功能目标
- 坐席可查看/登记质检分项与总分，管理回访任务状态（pending/done/overdue）。

#### 预计涉及文件
- 新建：`backend/src/models/qa.py`、`repositories/qa.py`、`services/qa_service.py`、`api/routes/qa.py`
- 新建：`frontend/src/services/qaService.ts`
- 修改：`db/models.py`、`main.py`、`QaFollowupPage.vue`

#### 分层实现思路
- [x] **层 1–6** — 模型/ORM/仓储/服务/路由/前端去 Mock + 种子

#### 用户测试思路
- `agent` → 质检与回访 → 种子可见 → 回访标完成

- [x] **用户测试通过（本人执行后勾选）**

---

### B10：消息 / 设置 / SLA 看板（依赖 B1、B4、B5、B7、B8）

#### 功能目标
- P10 站内消息聚合；P11 偏好持久化；P15 SLA 真实聚合；登录去误导 MockBadge。

#### 分层实现思路
- [x] 通知表 + `/api/notifications`
- [x] 偏好表 + `/api/users/me/preferences`
- [x] `/api/agent/sla-board` + 前端接线
- [x] 顶栏「待办 / 未读」可点击跳转任务与消息

- [x] **用户测试通过（本人执行后勾选）**

---

## 三、交付收尾

- [x] 后端 B0–B10 全部完成
- [x] 启动说明：`.output/startup.md`（环境、命令、演示账号、端口）
- [x] 前后端联调验收通过（2026-08-07：登录/对话检索/任务/转人工坐席/运营配置与审计）
- [x] B8–B10 去 Mock 收尾完成（用户确认继续）
- [x] 修复：坐席「完成此单」后左侧仍显示「处理中」（后端结案前 commit + 工作台列表乐观更新/队列 WS）
- [x] 交付阶段完成（2026-08-07）

---

### B11：百炼 LLM 接入（依赖 B3）

#### 功能目标
- 对话在检索到知识后，用阿里云百炼（OpenAI 兼容）生成自然回答；未配置 Key 或调用失败时回退模板，不阻断主流程。

#### 预计涉及文件
- 新建：`backend/src/services/llm_client.py`
- 修改：`answer_generator.py`、`chat_service.py`、`health.py`、`requirements.txt`、`.env` / `.env.example`、`startup.md`

#### 分层实现思路
- [x] **配置**：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL_GENERATE`（默认百炼兼容地址 + qwen-plus）
- [x] **客户端**：httpx 调 `/chat/completions`，`trust_env=False`
- [x] **编排**：`generate_answer` 优先 LLM，失败模板降级
- [x] **可观测**：`/api/health` 返回 `llm.configured`

#### 用户测试思路
1. 安装 `httpx`（见下方命令）并在 `.env` 填写 `LLM_API_KEY`
2. 重启后端 → `GET /api/health` 中 `llm.configured=true`
3. `emp` 提问差旅标准 → 回答应为模型润色文案（非纯模板拼接）

- [x] **用户测试通过（本人执行后勾选）**

---

### B12：内容产出 — 改写 / 报告 / 数据导出（依赖 B1、B3、B11）

> 依据：`.output/PRD.md` §2.1 能力矩阵（**不是全都有**，按角色授权）。  
> 分层实现思路由 feature-plan skill 生成，**用户确认后动工**。

#### 功能目标
- 员工/坐席/运营能按权限发起三类产出：文档改写、报告草稿、数据导出；结果可预览并下载；写入 Planner 类任务便于回溯。
- **不做**：完整 PPT 幻灯片编辑器、跨文档合并、用 Planner 办报销/请假等事务、导出薪资证件等敏感明文。

#### 预计涉及文件
- 新建：`backend/src/models/content.py`、`repositories/content.py`、`services/content_service.py`、`api/routes/content.py`
- 新建：`frontend/src/services/contentService.ts`；页面增强：`ChatPage` / `TaskDetailPage` / `SessionWorkbenchPage` / `InsightsPage`（按角色露出入口）
- 修改：`db/models.py`、`main.py`、权限校验与审计

#### 分层实现思路
- [x] **层 1：Pydantic 模型** — rewrite/report/export 请求响应与能力矩阵
- [x] **层 2：ORM** — `content_artifacts` 表
- [x] **层 3：Repository** — 按 owner 列表/读取
- [x] **层 4：Service** — 角色硬校验 + 百炼/模板 + CSV 导出
- [x] **层 5：API** — `/api/content/*`
- [x] **层 6：前端** — 三端「内容产出」页按角色露出数据集

#### 联调方式
- 后端：`scripts/dev-backend.sh`（默认 8010）
- 前端：`scripts/dev-frontend.sh`（5173，`/api` 代理）

#### 用户测试思路
1. `emp` → `/content`：改写一段通知；导出「我的任务」；不应看到审计日志选项。  
2. `agent` → `/agent/content`：改写回复稿；导出本人经办；尝试选运营数据集应无选项。  
3. `admin` → `/ops/content`：报告 + 导出 knowledge/bad_cases/audit_logs。  
4. 未配 LLM 时改写仍有模板结果。

- [x] **用户测试通过（本人执行后勾选）**

---

### B13：报告简易 PPTX 导出（依赖 B12）

#### 功能目标
- 生成报告时附带简易 `.pptx`（按 Markdown `##` 拆页）；预览区可下载 MD / PPTX。非完整幻灯片编辑器。

#### 涉及文件
- `backend/src/services/pptx_builder.py`、`content_service.py`、`api/routes/content.py`
- `frontend` ContentStudio 下载按钮；`requirements.txt` 增加 `python-pptx`

#### 用户测试思路
1. `pip install python-pptx` 后重启后端  
2. 内容产出 → 生成报告 → 出现「下载 PPTX」并能用 PowerPoint/WPS 打开  

- [ ] **用户测试通过（本人执行后勾选）**

