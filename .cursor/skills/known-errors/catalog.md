# 已知错误条目明细

> 来源：本项目开发/联调对话沉淀（2026-08）。按 ID 查阅；修复新问题请追加到文末。

---

## E-ENV-VENV — 虚拟环境未创建或路径错误

**症状**
- `source .venv/bin/activate`：No such file or directory
- `uvicorn: command not found`

**根因**
- 项目尚未创建 `.venv`
- 误以为 venv 在 `backend/` 下；规范是**项目根目录** `.venv`

**正确处置**
```bash
cd /Users/wangxinyu/Downloads/开发规范包_V2
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
PYTHONPATH=.. python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**预防**
- 启动说明写清：venv 在仓库根；在 `backend` 内激活用 `source ../.venv/bin/activate`
- 依赖安装由用户执行，且提醒勿中途 Ctrl+C

---

## E-ENV-REFUSED — 连接被拒绝 / 页面打不开

**症状**
- 浏览器 `ERR_CONNECTION_REFUSED`
- Cursor 内置浏览器 Connection Failed

**根因**
- 前端 5173 或后端 8000/8010 未监听（从未启动或已退出）

**正确处置**
1. `lsof -iTCP:5173 -sTCP:LISTEN` / `lsof -iTCP:8000 -sTCP:LISTEN`（或 8010）
2. 按 `.output/startup.md` 或 `scripts/dev-backend.sh` / `scripts/dev-frontend.sh` 分终端启动
3. 先验 `http://127.0.0.1:<port>/api/health` 再开登录页
4. 内置浏览器偶发连不上时，改用 Safari/Chrome 打开同一 URL

**预防**
- 不要假设「昨天开过今天还在」；每次验收先 health check

---

## E-ENV-CMD — 多条命令粘成一行

**症状**
- `Error: Invalid value for '--port': '8000~cd' is not a valid integer`
- 在 `backend` 目录执行 `npm run dev` → 找不到 `package.json`

**根因**
- 用户把后端启动命令与 `cd frontend` / `npm run dev` 粘贴成同一行
- 前后端挤在同一终端连续硬跑

**正确处置**
- 终端 1 只跑后端一行命令，看到 `Uvicorn running` 后不要再往该窗敲命令
- 终端 2（点 `+`）再 `cd frontend` → `npm run dev`，一次一条

**预防**
- 给用户命令时分块、标明「终端 1 / 终端 2」；强调「一次只贴一条」

---

## E-ENV-DEPS — 缺依赖导致热重载/启动失败

**症状**
- 后端曾能启动，改代码 reload 后登录卡住或接口无响应
- 日志：`ModuleNotFoundError: httpx` / `loguru` 等
- `pip install` 被中途 Ctrl+C，包未装完

**根因**
- `requirements.txt` 有依赖但未装入当前 `.venv`
- 顶层 import 重型依赖（如 httpx）导致**整应用**起不来，连登录也挂

**正确处置**
```bash
# 停掉卡住的 uvicorn
pkill -f "uvicorn src.main:app"
cd <repo> && source .venv/bin/activate
pip install -r backend/requirements.txt   # 等跑完，勿中断
# 再启动后端
```
- 代码侧：LLM 客户端对 `httpx` **延迟导入**，未安装时仍允许登录等非 LLM 接口启动

**预防**
- 新增依赖必须写入 `requirements.txt` 并明确告知用户安装
- 可选依赖不要在模块 import 时硬失败拖垮启动

---

## E-ENV-ZOMBIE — 端口被僵死进程占用

**症状**
- `Address already in use`
- `lsof` 显示端口在听，但 `/api/health` 超时或无响应

**根因**
- reload 失败后旧 worker 仍占端口
- 多次启动叠加

**正确处置**
```bash
pkill -f "uvicorn src.main:app"
# 或 lsof -tiTCP:8000 | xargs kill
# 确认端口空闲后再启动
```

**预防**
- 换端口前先确认是「僵死」还是「对话后台被杀」（见 E-ENV-AGENT-KILL）

---

## E-ENV-AGENT-KILL — 对话里后台代启服务被清掉

**症状**
- 「为啥老是中断」
- Agent 刚说后端已起来，过一会又挂

**根因**
- 在 Cursor Agent 对话中用后台 Shell 代启的长期进程会被会话清理杀掉
- **不是端口本身坏了**

**正确处置**
- 让用户在本机「终端」App 或 Cursor 终端面板常驻窗口跑 `scripts/dev-backend.sh` / `scripts/dev-frontend.sh`
- 可用看门狗脚本自动拉起；避免仅依赖对话后台

**预防**
- 禁止把「对话后台 uvicorn」当作稳定运行方式
- 文档写明：两个常驻窗口，不要关

---

## E-ENV-PORT-JUMP — Vite 端口漂移

**症状**
- 打开 `http://localhost:5173` 打不开，但「前端好像在跑」

**根因**
- 5173 被占时 Vite 自动改用 **5174**（或其它），用户仍访问 5173
- 后端也可能不在预期端口（曾临时改 8010）

**正确处置**
1. 看 Vite 终端里打印的 `Local: http://localhost:xxxx/`
2. 清掉多余 node/vite 进程，用固定端口重启（如 `--port 5173 --strictPort`）
3. 核对前端代理/`VITE_API_*` 与后端实际端口一致

**预防**
- 前端启动加 `strictPort`，占线时直接失败而不是偷偷换端口

---

## E-ENV-STALE-UI — 旧页面仍显示但交互失灵

**症状**
- 工作台还能看见，点「发送」完全无反应
- 截图看起来「页面在」，服务其实已挂

**根因**
- 浏览器保留了上次的 SPA 壳；新导航/API 需要活着的 Vite/后端

**正确处置**
1. health check + 重启前后端
2. 浏览器强制刷新（Cmd+Shift+R）
3. 前端对发送失败给出明确红字/「跳转中…」，避免静默无反馈

**预防**
- UI 关键路径必须有 loading / error 态，禁止「点了没任何提示」

---

## E-MOCK-FALSE — 后端未开被误报成密码错误

**症状**
- 登录页提示「账号或密码错误」
- 用户坚称密码是 `123456`
- 页面上可能还有 `[Mock]` 标记

**根因**
- `VITE_USE_MOCK=false`，请求打向后端失败，前端把网络/错误统一映射成「账号或密码错误」
- **`[Mock]` 只是组件角标，≠ 当前走了 Mock 登录**

**正确处置**
- 方式 A：启动后端后真登录
- 方式 B：临时 `VITE_USE_MOCK=true` 后重启前端（仅验收页面）

**预防**
- 登录失败文案区分：网络错误 vs 凭证错误
- 联调说明写清 Mock 开关含义

---

## E-MOCK-MIX — Mock 登录 + 真 API → 401 踢回

**症状**
- 能「登录成功」进工作台，立刻又回登录页
- 或表现为「登录不上」

**根因**
- `VITE_USE_MOCK=true` 写入假 token
- 对话/会话等接口已打真实后端 → 401 → 拦截器清登录态并跳转

**正确处置**
1. 联调时设 `VITE_USE_MOCK=false` 并保证后端在跑
2. 清 Local Storage 的 `token` / `user`（或无痕窗口）后重登
3. 全量去 Mock 后禁止再混用假 token

**预防**
- Mock 开关应全局一致：要么整站 Mock，要么整站真接口
- axios 401 处理前可区分「从未登录」与「token 无效」以便提示

---

## E-FE-DYN — 动态 import 模块失败

**症状**
```
Failed to fetch dynamically imported module:
http://localhost:5173/src/layouts/EmployeeLayout.vue
```

**根因**
- 文件通常存在；是 **Vite 已被 kill**（如 `zsh: killed npm run dev`），浏览器仍按 5173 拉模块

**正确处置**
```bash
cd frontend && npm run dev
```
刷新浏览器后再登录

**预防**
- 停前端前告知用户；杀进程后提醒必须重启再刷页

---

## E-CHAT-ORDER — 助手回复跑到用户消息上方

**症状**
- 「我说话，回复为什么在上方」

**根因**
- WebSocket 先推入助手消息；HTTP 返回后才插入用户消息 → 列表顺序反了

**正确处置（前端）**
- 发送时先乐观插入用户消息
- HTTP 返回后：去掉乐观节点 → **先 upsert 用户消息再 upsert 助手消息**
- 列表按 `created_at`（或稳定序号）排序，避免纯 push 顺序依赖网络时序

**预防**
- 凡「HTTP + WS 双通道」更新同一列表，必须定义权威顺序与去重 id

---

## E-CHAT-GREET — 寒暄被规则拦截，误判百炼未通

**症状**
- 用户已配 Key，问「你好」仍是固定澄清文案
- 认为「没连上百炼」

**根因**
- 路由把过短/寒暄句直接打成 `clarify_reply`，**根本未调 LLM**
- 业务问句（如「差旅标准」）其实已经走模型

**正确处置**
- `llm_configured()` 为真时，寒暄/模糊句走 `conversational_reply`（调模型）
- 用「差旅标准」与「你好」分别验收：前者 RAG/生成，后者自然寒暄

**预防**
- 健康检查展示 `llm.configured`；产品文案区分「规则澄清」与「模型未配置」

---

## E-LLM-KEY — 未配置 API Key

**症状**
- `/api/health` 中 `llm.configured: false`
- 一律本地规则/模板回复

**根因**
- `backend/.env` 中 `LLM_API_KEY` 为空（BASE_URL/模型名可能已有）

**正确处置**
- 写入 Key 后重启后端；用 health + 一次真实 chat_completion 探测
- httpx 客户端：`trust_env=False`，配置只来自 AppSettings，不吃环境代理

**预防**
- `.env.example` 标明必填项；缺 Key 时接口/UI 明确提示而非静默降级到「像坏了」

---

## E-KB-HASH — 中文知识检索召回差

**症状**
- 问制度相关内容答非所问或空

**根因**
- 中文整词哈希向量几乎对不上
- 低分向量命中抢先，挡住关键词兜底

**正确处置**
- 检索链路：低分向量结果不得阻断关键词 fallback
- 校准种子知识与 chunk；必要时调阈值

**预防**
- 向量方案与中文分词/embedding 选型在架构蓝图中写清；本地哈希仅作降级需严格兜底

---

## E-TICKET-NAV — 转人工与坐席工单入口不一致

**症状**
- 员工转人工后不知道去哪看
- 坐席「工单」菜单仍是 Mock，真数据在「队列看板」

**根因**
- 去 Mock 不完整：导航/菜单未切到真实列表页

**正确处置**
- 转人工成功后引导至工单/会话对应页
- 坐席菜单与真数据源对齐（队列看板或真实工单列表）

**预防**
- 全量去 Mock 清单逐页勾选；禁止「半 Mock 半真」留入口

---

## E-API-COMMIT — 结案后列表状态不刷新（提交竞态）

**症状**
- 坐席点「完成此单」后，左侧列表仍显示 active
- 偶发：刷新才变对

**根因**
1. 前端结案后只 `loadList`，未同步本地状态、未听队列 WS
2. 后端 `get_db` **响应发出后才 commit**，前端立刻 GET 仍读到旧状态

**正确处置**
- 后端：业务成功路径在返回前 commit（或依赖能立即读到的会话边界）
- 前端：结案后本地更新 + 监听队列 WS + 再 pull

**预防**
- 写操作 API 的集成验收必须含「写完立即读」；注意 FastAPI Depends 会话生命周期

---

## E-WS-IMPORT — WebSocket 导入错误

**症状**
- 启动或调用 WS 相关路径时 ImportError / 模块未完成

**根因**
- 重构或去 Mock 时 WS 路由/客户端导入残留错误

**正确处置**
- 查后端 WS 路由注册与前端 `chatService`/队列 WS 的 import 路径，补齐后重启

**预防**
- 改导入后至少跑一遍 health + 登录 + 发一条消息的冒烟

---

## 附录：高频误判对照

| 用户说法 | 优先怀疑 |
|----------|----------|
| 账号或密码错误 | E-MOCK-FALSE / E-ENV-REFUSED / E-ENV-DEPS，不是密码 |
| 登录不上 / 又踢回登录 | E-MOCK-MIX / E-ENV-ZOMBIE |
| 打不开 / 又打不开了 | E-ENV-REFUSED / E-ENV-PORT-JUMP / E-ENV-AGENT-KILL |
| 发送没反应 | E-ENV-STALE-UI |
| 回复在上方 | E-CHAT-ORDER |
| 没连上百炼 | E-LLM-KEY / E-CHAT-GREET（先看 health） |
| 老是中断 | E-ENV-AGENT-KILL |

---

## 追加模板

```markdown
## E-XXX-YYY — 标题

**症状**
- …

**根因**
- …

**正确处置**
- …

**预防**
- …
```
