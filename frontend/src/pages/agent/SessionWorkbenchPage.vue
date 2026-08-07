<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import {
  agentGetTicket,
  agentSendMessage,
  claimTicket,
  connectTicketSocket,
  getQueueBoard,
  resolveTicket,
  ticketStatusMap,
  type TicketDetail,
  type TicketItem,
  type TicketMessage,
  type TicketStatus,
} from '@/services/ticketService'

const OPEN_STATUSES: TicketStatus[] = ['waiting', 'active', 'need_info', 'need_expert']

const route = useRoute()
const router = useRouter()

const list = ref<TicketItem[]>([])
const detail = ref<TicketDetail | null>(null)
const inputText = ref('')
const loading = ref(false)
const error = ref('')
const sending = ref(false)
const resolving = ref(false)
let ticketWs: WebSocket | null = null
let queueWs: WebSocket | null = null

const activeId = computed(() => (route.params.id as string) || '')

/** 用详情状态覆盖列表项，避免结案后左侧仍显示「处理中」 */
const displayList = computed(() => {
  return list.value.map((item) => {
    if (detail.value && item.id === detail.value.id) {
      return { ...item, status: detail.value.status }
    }
    return item
  })
})

function statusLabel(status: TicketStatus) {
  return ticketStatusMap[status]?.label || status
}

function statusTag(status: TicketStatus) {
  return ticketStatusMap[status]?.tag || 'tag-muted'
}

async function loadList() {
  try {
    const board = await getQueueBoard()
    list.value = (board.items || []).filter((i) => OPEN_STATUSES.includes(i.status))
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载队列失败'
  }
}

function patchListStatus(id: string, status: TicketStatus) {
  list.value = list.value
    .map((i) => (i.id === id ? { ...i, status } : i))
    .filter((i) => OPEN_STATUSES.includes(i.status))
}

async function loadDetail(id: string) {
  if (!id) return
  loading.value = true
  error.value = ''
  try {
    detail.value = await agentGetTicket(id)
    if (detail.value && !OPEN_STATUSES.includes(detail.value.status)) {
      patchListStatus(detail.value.id, detail.value.status)
    }
    openTicketWs(id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function openTicketWs(id: string) {
  ticketWs?.close()
  ticketWs = connectTicketSocket(`ticket:${id}`, {
    onEvent: (data) => {
      if (data.type === 'message' && data.message) {
        const msg = data.message as TicketMessage
        if (!detail.value?.messages.find((m) => m.id === msg.id)) {
          detail.value?.messages.push(msg)
        }
      }
      if (data.type === 'ticket' && data.ticket) {
        const t = data.ticket as TicketDetail
        detail.value = t
        patchListStatus(t.id, t.status)
      }
    },
  })
}

function openQueueWs() {
  queueWs?.close()
  queueWs = connectTicketSocket('agent:queue', {
    onEvent: (data) => {
      if (data.type === 'queue') {
        void loadList()
      }
    },
  })
}

async function selectTicket(id: string) {
  router.push(`/agent/sessions/${id}`)
}

async function goNextOrClear(excludeId: string) {
  const next = list.value.find((i) => i.id !== excludeId)
  if (next) {
    await router.replace(`/agent/sessions/${next.id}`)
  } else {
    detail.value = detail.value?.id === excludeId ? detail.value : null
    await router.replace('/agent/sessions')
  }
}

async function claimIfNeeded() {
  if (!detail.value || detail.value.status !== 'waiting') return
  detail.value = await claimTicket(detail.value.id)
  patchListStatus(detail.value.id, detail.value.status)
  await loadList()
}

async function send() {
  const text = inputText.value.trim()
  if (!text || !detail.value) return
  sending.value = true
  try {
    if (detail.value.status === 'waiting') {
      await claimIfNeeded()
    }
    if (!detail.value || !OPEN_STATUSES.includes(detail.value.status)) {
      throw new Error('工单已结束，无法发送')
    }
    const msg = await agentSendMessage(detail.value.id, text)
    if (!detail.value.messages.find((m) => m.id === msg.id)) {
      detail.value.messages.push(msg)
    }
    inputText.value = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '发送失败'
  } finally {
    sending.value = false
  }
}

const canResolve = computed(() => {
  const s = detail.value?.status
  return !!s && OPEN_STATUSES.includes(s)
})

async function onResolve() {
  if (!detail.value || resolving.value) return
  const ticketId = detail.value.id
  resolving.value = true
  error.value = ''
  try {
    if (detail.value.status === 'waiting') {
      await claimIfNeeded()
    }
    const resolved = await resolveTicket(ticketId, '坐席工作台完成此单')
    detail.value = resolved
    patchListStatus(ticketId, 'resolved')
    await loadList()
    await goNextOrClear(ticketId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '完成此单失败'
    await loadList()
  } finally {
    resolving.value = false
  }
}

function fmtTime(iso: string) {
  return iso ? new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''
}

function slaText() {
  if (!detail.value) return '—'
  if (['resolved', 'closed'].includes(detail.value.status)) return '已结束'
  return detail.value.sla_overdue ? '已超时' : '进行中'
}

watch(
  () => route.params.id,
  (id) => {
    if (id) void loadDetail(String(id))
    else detail.value = null
  },
)

onMounted(async () => {
  openQueueWs()
  await loadList()
  if (activeId.value) {
    await loadDetail(activeId.value)
  } else if (list.value.length) {
    await router.replace(`/agent/sessions/${list.value[0].id}`)
  }
})

onUnmounted(() => {
  ticketWs?.close()
  queueWs?.close()
})
</script>

<template>
  <div class="page page-workbench">
    <PageHeader title="会话工作台" description="三栏布局 · 会话列表 / 对话区 / 交接摘要" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>

    <div class="workbench">
      <aside class="panel panel-left card">
        <div class="panel-head">会话列表</div>
        <div class="panel-body">
          <button
            v-for="s in displayList"
            :key="s.id"
            type="button"
            class="session-item"
            :class="{ active: s.id === activeId }"
            @click="selectTicket(s.id)"
          >
            <div class="session-top">
              <span class="session-name">{{ s.employee_name }}</span>
              <span class="tag" :class="statusTag(s.status)">
                {{ statusLabel(s.status) }}
              </span>
            </div>
            <div class="session-topic">{{ s.subject }}</div>
            <div class="session-preview">等待 {{ s.wait_minutes }} 分钟</div>
          </button>
          <p v-if="!displayList.length" class="muted">暂无在办/排队工单</p>
        </div>
      </aside>

      <section class="panel panel-mid card">
        <div class="panel-head mid-head">
          <div>
            <strong>{{ detail?.employee_name || '未选择' }}</strong>
            <span class="sub">{{ detail?.subject }}</span>
          </div>
          <div class="mid-actions">
            <button
              v-if="detail?.status === 'waiting'"
              class="btn btn-primary btn-sm"
              type="button"
              @click="claimIfNeeded"
            >
              接管
            </button>
            <button
              v-if="canResolve"
              class="btn btn-primary btn-sm"
              type="button"
              :disabled="resolving"
              @click="onResolve"
            >
              完成此单
            </button>
          </div>
        </div>
        <div class="panel-body messages">
          <p v-if="loading" class="muted">加载中…</p>
          <div
            v-for="m in detail?.messages || []"
            :key="m.id"
            class="msg"
            :class="m.role"
          >
            <div class="bubble">
              <div class="meta">{{ m.sender_name }} · {{ fmtTime(m.created_at) }}</div>
              <p>{{ m.content }}</p>
            </div>
          </div>
        </div>
        <div class="composer">
          <input
            v-model="inputText"
            class="input composer-input"
            placeholder="回复员工…"
            :disabled="!detail || detail.status === 'resolved' || detail.status === 'closed'"
            @keyup.enter="send"
          />
          <button
            class="btn btn-primary composer-send"
            type="button"
            :disabled="sending || !detail || detail.status === 'resolved' || detail.status === 'closed'"
            @click="send"
          >
            发送
          </button>
          <button
            v-if="canResolve"
            class="btn btn-ghost composer-done"
            type="button"
            :disabled="resolving"
            @click="onResolve"
          >
            完成此单
          </button>
        </div>
      </section>

      <aside class="panel panel-right card">
        <div class="panel-head">交接包</div>
        <div class="panel-body handoff">
          <template v-if="detail">
            <p><strong>意图</strong> {{ detail.handoff.intent || '—' }}</p>
            <p><strong>置信</strong> {{ detail.handoff.confidence }}</p>
            <p><strong>摘要</strong></p>
            <pre>{{ detail.handoff.summary || '—' }}</pre>
            <p><strong>证据</strong></p>
            <ul>
              <li v-for="(e, i) in detail.handoff.evidence" :key="i">{{ e }}</li>
              <li v-if="!detail.handoff.evidence?.length">暂无</li>
            </ul>
            <p class="muted">工单 {{ detail.id.slice(0, 8) }} ·
              <span class="tag" :class="statusTag(detail.status)">{{ statusLabel(detail.status) }}</span>
              · SLA
              <span :class="{ danger: detail.sla_overdue && canResolve }">
                {{ slaText() }}
              </span>
            </p>
          </template>
          <p v-else class="muted">选择左侧会话查看交接包</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.err {
  color: #cf1322;
  margin-bottom: 8px;
}
.workbench {
  display: grid;
  grid-template-columns: 260px 1fr 280px;
  gap: 10px;
  height: calc(100vh - var(--header-h) - 80px);
  min-height: 420px;
}
.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.panel-head {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
  font-size: 13px;
}
.mid-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.sub {
  display: block;
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-secondary);
}
.mid-actions {
  display: flex;
  gap: 6px;
}
.panel-body {
  flex: 1;
  overflow: auto;
  padding: 10px;
}
.session-item {
  width: 100%;
  text-align: left;
  border: none;
  background: var(--color-bg);
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 6px;
  cursor: pointer;
}
.session-item.active {
  background: var(--color-primary-soft);
}
.session-top {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}
.session-topic {
  font-size: 12px;
  margin-top: 2px;
}
.session-preview {
  font-size: 11px;
  color: var(--color-text-secondary);
}
.messages {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.msg {
  display: flex;
}
.msg.employee {
  justify-content: flex-start;
}
.msg.agent {
  justify-content: flex-end;
}
.msg.system,
.msg.ai {
  justify-content: center;
}
.bubble {
  max-width: 80%;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
}
.msg.agent .bubble {
  background: var(--color-primary-soft);
  border-color: transparent;
}
.msg.system .bubble,
.msg.ai .bubble {
  background: #fafafa;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.meta {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}
.bubble p {
  margin: 0;
  white-space: pre-wrap;
}
.composer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid var(--color-border);
}
.composer-input {
  flex: 1;
  min-width: 0;
}
.composer-send,
.composer-done {
  flex: 0 0 auto;
  white-space: nowrap;
  writing-mode: horizontal-tb;
  min-width: 72px;
}
.handoff p {
  margin: 0 0 8px;
  font-size: 12px;
}
.handoff pre {
  white-space: pre-wrap;
  font-size: 12px;
  background: var(--color-bg);
  padding: 8px;
  border-radius: 6px;
  margin: 0 0 10px;
}
.handoff ul {
  margin: 0 0 10px;
  padding-left: 18px;
  font-size: 12px;
}
.muted {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.danger {
  color: var(--color-danger);
  font-weight: 600;
}
.btn-sm {
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
}
.btn-ghost {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: 6px;
  cursor: pointer;
}
@media (max-width: 1100px) {
  .workbench {
    grid-template-columns: 1fr;
    height: auto;
  }
}
</style>
