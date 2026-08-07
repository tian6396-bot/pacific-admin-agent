# 太平洋金科·智能行政咨询助手（P-Assistant）

企业内部 Web 智能行政咨询助手：可信问答、服务办理、转人工坐席、运营治理。  
技术栈：**Vue 3 + TypeScript** / **Python FastAPI + PyCore**。

仓库：[https://github.com/tian6396-bot/pacific-admin-agent](https://github.com/tian6396-bot/pacific-admin-agent)

---

## 快速开始

### 1. 环境

- Python **3.11+**（推荐 3.13）
- Node.js **18+**
- 本仓库已包含 `pycore/`，启动时用 `PYTHONPATH=..`，**不要** `pip install pycore`

### 2. 安装依赖

```bash
# 后端
cd /path/to/本仓库
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 前端
cd frontend
npm install
```

### 3. 配置

```bash
cp backend/.env.example backend/.env
# 按需编辑 backend/.env（JWT、百炼 Key 等）

# 前端已有 frontend/.env.example；开发推荐：
# VITE_API_BASE_URL=/api
# VITE_USE_MOCK=false
```

可选：在 `backend/.env` 填写阿里云百炼 `LLM_API_KEY`，对话会用模型润色回答；不填则走知识模板降级。

### 4. 启动（开两个终端）

默认后端端口 **8010**（前端 Vite 已代理 `/api` → `8010`）。

```bash
# 终端 1 — 后端
bash scripts/dev-backend.sh

# 终端 2 — 前端
bash scripts/dev-frontend.sh
```

浏览器打开：http://localhost:5173  
健康检查：http://localhost:8010/api/health

更完整的说明见 [`.output/startup.md`](.output/startup.md)。

---

## 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `emp` | `123456` | 员工 |
| `agent` | `123456` | 坐席 |
| `admin` | `123456` | 运营管理员 |

---

## 目录结构

```
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
├── pycore/            # 框架（PYTHONPATH 引入）
├── scripts/           # 本地启动脚本
├── .output/           # PRD / 计划 / 启动说明
└── .cursor/           # Cursor 开发规范与 skills
```

---

## 说明

- **GitHub 只托管代码**，不会自动变成公网网址；他人需克隆后在本机启动。
- 密钥写在 `backend/.env`，该文件已在 `.gitignore` 中，请勿提交。
- 产品文档与验收清单：`.output/PRD.md`、`.output/plan.md`。
