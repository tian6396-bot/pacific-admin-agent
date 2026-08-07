---
name: known-errors
description: >-
  本项目已沉淀的报错与踩坑手册。用户报错、登录失败、连接拒绝、发送无反应、
  消息顺序错乱、Mock/真接口混乱、依赖缺失、端口占用、服务中断、检索不准、
  结案后列表不刷新时优先查阅；修复新问题后须追加条目。
---

# 已知错误手册（太平洋金科·智能行政咨询助手）

## 何时使用

用户出现以下任一情况时**立即读取本 skill**，先对照目录再排查，避免重复踩坑：

- 报错 / 登录不上 / 又不行了 / 打不开 / 无反应 / 卡住
- `ERR_CONNECTION_REFUSED`、`Failed to fetch`、401、ModuleNotFound、端口异常
- Mock 与真后端行为不一致、聊天顺序反了、百炼「没连上」、结案后状态不更新

**开始时声明**：「我正在对照 known-errors skill 排查。」

---

## 排查顺序（强制）

按下面顺序快速分流，再查对应条目：

```
1. 服务是否在跑？
   curl -s http://127.0.0.1:8000/api/health 或 8010
   打开 http://localhost:5173/login
2. VITE_USE_MOCK 与后端是否一致？（见 E-MOCK-*）
3. 终端是否把多条命令粘成一行？（见 E-ENV-CMD）
4. .venv / 依赖是否齐全？（见 E-ENV-*）
5. 是否代码逻辑 / 竞态？（见 E-CHAT-* / E-API-*）
```

排查时优先看终端真实报错与 `lsof -iTCP:5173,8000,8010`，不要凭用户口头「登录失败」直接改密码逻辑。

---

## 错误目录速查

| ID | 用户表象 | 根因一类 |
|----|----------|----------|
| E-ENV-VENV | `activate` / `uvicorn` 找不到 | 未建根目录 `.venv` |
| E-ENV-REFUSED | Connection refused / 打不开页 | 前后端未启动或已挂 |
| E-ENV-CMD | `'8000~cd' is not a valid integer` | 多条命令粘成一行 |
| E-ENV-DEPS | 热重载后起不来 / 登录卡住 | 缺 `httpx`/`loguru` 等；pip 被 Ctrl+C |
| E-ENV-ZOMBIE | 端口在听但不响应 | 旧进程占端口、reload 失败 |
| E-ENV-AGENT-KILL | 「老是中断」 | Cursor 对话后台任务被清掉 |
| E-ENV-PORT-JUMP | 5173 打不开 | Vite 跳到 5174；用户仍开 5173 |
| E-ENV-STALE-UI | 页面在但发送无反应 | 浏览器旧页 + 服务已挂 |
| E-MOCK-FALSE | 提示「账号或密码错误」 | Mock=false 且后端未开 |
| E-MOCK-MIX | 登录后立刻踢回登录页 | Mock 假 token + 真 API → 401 |
| E-FE-DYN | Failed to fetch … Layout.vue | Vite 进程已停 |
| E-CHAT-ORDER | 回复出现在自己消息上方 | WS 先于 HTTP 插入消息 |
| E-CHAT-GREET | 「你好」像没连百炼 | 短句被规则拦成澄清模板 |
| E-LLM-KEY | llm.configured=false | `.env` 缺 `LLM_API_KEY` |
| E-KB-HASH | 制度问答召回差 | 中文哈希向量 + 低分挡住关键词兜底 |
| E-TICKET-NAV | 转人工后找不到工单 | 未引导到工单页；坐席菜单仍 Mock |
| E-API-COMMIT | 结案后列表仍 active | `get_db` 响应后才 commit 竞态 |
| E-WS-IMPORT | WebSocket 相关 ImportError | 导入路径/未完成修复 |

详细条目见 [catalog.md](catalog.md)。

---

## 处置原则

1. **先环境后代码**：多数「登录失败 / 打不开」是服务挂了或 Mock 不一致，不是密码错。
2. **前后端分终端、一次一条命令**；禁止把后端启动与 `cd frontend` 粘在一起。
3. **不要用对话后台长期代启服务**（会被 Cursor 清掉）。优先让用户在本机终端或 `scripts/dev-*.sh` / 看门狗保活。
4. **改 `.env` / Mock 后提醒重启或清 Local Storage 的 `token`/`user`**。
5. **httpx 客户端必须 `trust_env=False`**，不继承环境代理。
6. **最小改动**：对照条目修复，勿借机大重构。

---

## 修复后沉淀（强制）

每次修完**新**问题（目录里没有的）：

1. 在 [catalog.md](catalog.md) 追加一条，格式与现有条目一致。
2. 更新上方「错误目录速查」表。
3. 可选：写 `.output/bug_fix/YYYYMMDD-HHMMSS-简述.md`（与 bugfix skill 一致）。

条目至少包含：`症状` / `根因` / `正确处置` / `预防`。

---

## 与其它 skill 的关系

- **bugfix**：走完整分析→修复→报告流程时用；本 skill 提供「已知答案」加速定位。
- **feature-plan**：新功能开发前用；若开发中引入新坑，开发完成后写入本手册。
