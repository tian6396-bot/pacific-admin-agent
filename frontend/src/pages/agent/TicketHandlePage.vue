<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import MockBadge from '@/components/MockBadge.vue'

const showExpert = ref(false)

interface TicketDetail {
  id: string
  subject: string
  status: 'open' | 'processing' | 'resolved' | 'closed'
  employee: string
  dept: string
  channel: string
  agent: string
  createdAt: string
  description: string
  timeline: { time: string; action: string; operator: string }[]
}

const route = useRoute()

const ticket: TicketDetail = {
  id: 'TK-1001',
  subject: '差旅标准咨询转人工',
  status: 'processing',
  employee: '张明',
  dept: '研发中心',
  channel: '智能对话',
  agent: '李坐席',
  createdAt: '2026-03-05 14:20',
  description: '员工出差机票 1580 元超出经济舱标准 1200 元，需发起超标审批。AI 已识别意图并建议转人工核实。',
  timeline: [
    { time: '14:20', action: '员工发起咨询，AI 应答', operator: '系统' },
    { time: '14:21', action: '低置信转人工，创建工单', operator: '系统' },
    { time: '14:22', action: '坐席李接入会话', operator: '李坐席' },
    { time: '14:25', action: '核实差旅标准，生成审批单', operator: '李坐席' },
  ],
}

const ticketId = computed(() => (route.params.id as string) || ticket.id)

const statusMap = {
  open: { label: '待接入', tag: 'tag-danger' },
  processing: { label: '处理中', tag: 'tag-primary' },
  resolved: { label: '已解决', tag: 'tag-success' },
  closed: { label: '已关闭', tag: 'tag-muted' },
} as const
</script>

<template>
  <div class="page">
    <PageHeader title="工单处理" description="查看详情并执行处理操作" icon="◆">
      <template #badge><MockBadge /></template>
    </PageHeader>

    <div class="layout">
      <div class="card detail-card">
        <div class="detail-head">
          <div>
            <h2>{{ ticket.subject }}</h2>
            <span class="mono sub-id">{{ ticketId }}</span>
          </div>
          <span class="tag" :class="statusMap[ticket.status].tag">
            {{ statusMap[ticket.status].label }}
          </span>
        </div>

        <div class="meta-grid">
          <div><span class="label">员工</span>{{ ticket.employee }}</div>
          <div><span class="label">部门</span>{{ ticket.dept }}</div>
          <div><span class="label">来源</span>{{ ticket.channel }}</div>
          <div><span class="label">当前坐席</span>{{ ticket.agent }}</div>
          <div><span class="label">创建时间</span>{{ ticket.createdAt }}</div>
        </div>

        <div class="field">
          <span class="label">问题描述</span>
          <p class="desc">{{ ticket.description }}</p>
        </div>

        <div class="actions">
          <button type="button" class="btn btn-primary">提交审批</button>
          <button type="button" class="btn btn-ghost">转派坐席</button>
          <button type="button" class="btn btn-ghost" @click="showExpert = true">转专家协同</button>
          <button type="button" class="btn btn-ghost">添加备注</button>
          <button type="button" class="btn btn-primary">标记已解决</button>
          <button type="button" class="btn btn-danger">关闭工单</button>
        </div>
      </div>

      <div class="card timeline-card">
        <h3>处理时间线</h3>
        <ul class="timeline">
          <li v-for="(item, i) in ticket.timeline" :key="i">
            <span class="time">{{ item.time }}</span>
            <span class="action">{{ item.action }}</span>
            <span class="operator">{{ item.operator }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div v-if="showExpert" class="drawer-mask" @click.self="showExpert = false">
      <aside class="drawer card">
        <div class="drawer-head">
          <h3>专家协同 <MockBadge /></h3>
          <button type="button" class="btn btn-ghost" @click="showExpert = false">关闭</button>
        </div>
        <p class="drawer-desc">选择专家域并留言（原独立协同页已并入抽屉）</p>
        <label class="label">专家域</label>
        <select class="input">
          <option>财务</option>
          <option>HR</option>
          <option>行政</option>
          <option>IT</option>
        </select>
        <label class="label">留言</label>
        <textarea class="input" rows="4" placeholder="说明需复核的风险点…" />
        <button type="button" class="btn btn-primary" @click="showExpert = false">提交转派</button>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
}

.detail-card {
  padding: 24px;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.detail-head h2 {
  margin: 0 0 4px;
  font-size: 18px;
}

.sub-id {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
  font-size: 13px;
}

.meta-grid .label {
  display: block;
  margin-bottom: 2px;
}

.desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.timeline-card {
  padding: 20px;
}

.timeline-card h3 {
  margin: 0 0 16px;
  font-size: 14px;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline li {
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

.timeline li:last-child {
  border-bottom: none;
}

.time {
  display: inline-block;
  width: 48px;
  color: var(--color-text-secondary);
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
}

.action {
  margin-right: 8px;
}

.operator {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.drawer-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  justify-content: flex-end;
  z-index: 40;
}

.drawer {
  width: min(400px, 100%);
  height: 100%;
  border-radius: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-head h3 {
  margin: 0;
  font-size: 16px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.drawer-desc {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.drawer .label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.drawer textarea.input {
  resize: vertical;
  min-height: 96px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
