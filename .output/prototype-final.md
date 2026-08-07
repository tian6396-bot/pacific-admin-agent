# 原型定稿说明 — 太平洋金科·智能行政咨询助手

> 阶段 C | 定稿日期：2026-08-06  
> 对齐：`.output/Prototype.md`（B2 已确认）· `.output/PRD.md` · `.output/ui-design-spec.md`

---

## 1. 原型源文件

| 项 | 值 |
|----|-----|
| 工具 | Pencil MCP |
| 画布 | `.output/test.pen` |
| 画幅 | 1440×900 / 屏 |
| 风格 | Enterprise Light Ops Console · `#1677FF` |
| 状态 | P01–P25 已逐屏确认（含 Agent 优先纠偏） |

---

## 2. 界面与节点 ID（交付范围）

### 员工端

| 编号 | 界面 | 节点 ID | 路由建议 |
|------|------|---------|----------|
| P01 | 登录页 | `AijkC` | `/login` |
| P02 | Agent 首页 | `wfq8Y` | `/app` |
| P03 | 智能对话 | `zSvrN` | `/app/chat/:id?` |
| P04 | 全部服务 | `LDkN2` | `/app/services` |
| P05 | 服务申请确认 | `uZUQM` | `/app/services/:id/apply` |
| P06 | 我的任务 | `OYdrB` | `/app/tasks` |
| P07 | 任务详情 | `HKR0V` | `/app/tasks/:id` |
| P08 | 我的工单 | `MCmQZ` | `/app/tickets` |
| P09 | 材料中心 | `ubncs` | `/app/materials` |
| P10 | 消息中心 | `C2ATm6` | `/app/messages` |
| P11 | 个人设置 | `GI7Mw` | `/app/settings` |

### 坐席端

| 编号 | 界面 | 节点 ID | 路由建议 |
|------|------|---------|----------|
| P12 | 队列看板 | `hepma` | `/agent/queue` |
| P13 | 会话工作台 | `wM7L0` | `/agent/sessions/:id` |
| P14 | 工单处理 | `DyaWa` | `/agent/tickets/:id` |
| P15 | SLA 与班次看板 | `W2Jd5E` | `/agent/sla` |
| P16 | 质检与回访 | `Y30Sv` | `/agent/qa` |

### 运营端

| 编号 | 界面 | 节点 ID | 路由建议 |
|------|------|---------|----------|
| P17 | 知识管理 | `R8fCXk` | `/ops/knowledge` |
| P18 | 知识解析详情 | `peqf8` | `/ops/knowledge/:id/parse` |
| P19 | 服务目录 | `ui4SD` | `/ops/catalog` |
| P20 | 意图与 Prompt | `YKvRN` | `/ops/intents` |
| P21 | Skill 管理 | `y1OC6Z` | `/ops/skills` |
| P22 | 工具与模型 | `PDQUJ` | `/ops/tools` |
| P23 | 队列与 SLA 配置 | `p6weY` | `/ops/queues` |
| P24 | 运营洞察 | `W1zOT` | `/ops/insights` |
| P25 | 权限与审计 | `K0XBO` | `/ops/audit` |

**合计：25。** 画布中废弃/归档帧不在交付范围。

---

## 3. 交互定稿要点

1. **P02** 为员工默认落地：左列表 + 中央 Agent（问候/输入/建议问法）。  
2. **P03** 为对话中态：三栏；确认卡片在消息流；右侧画像/证据/进度。  
3. **P04** 为次要「全部服务」表格式目录；强调回 Agent。  
4. 坐席 **P14** 专家协同为抽屉，不独立整页。  
5. 运营 **P24** 合并 Bad Case 与指标。  
6. ECharts 强制页：**P12 / P15 / P24**（P02 不再强制图表）。  
7. Planner 完整编辑器（PPT/富文本）**不在本原型展开**（V1.1）。

---

## 4. 主跳转

```
登录(P01)
  ├─ 员工 → Agent首页(P02) → 对话(P03) / 全部服务(P04)→表单(P05)
  │         → 任务(P06)→详情(P07) / 工单(P08) / 材料(P09) / 消息(P10) / 设置(P11)
  ├─ 坐席 → 队列(P12) → 会话(P13) / 工单(P14) / SLA(P15) / 质检(P16)
  └─ 运营 → 知识(P17)→解析(P18) → 目录(P19) → 意图(P20) → Skill(P21)
            → 工具(P22) → 队列SLA(P23) → 洞察(P24) → 权限审计(P25)
```

---

## 5. 前端实现约束

- 技术栈：Vue 3 + TypeScript + Pinia + Router（不可替换）。  
- 按原型与 `ui-design-spec.md` 大改现有前端；Mock 先行，验收后再接后端。  
- 依赖安装与测试由用户执行；模型不代跑安装/测试。

---

## 6. 门禁

- [x] 与 B2 确认原型一致  
- [x] 节点 ID 与 `.output/Prototype.md` 对齐  
- [x] 可指导前端按屏开发
