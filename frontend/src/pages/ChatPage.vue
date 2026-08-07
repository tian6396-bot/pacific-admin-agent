<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  citeLabel,
  connectChatSocket,
  createSession,
  formatMsgTime,
  formatSessionTime,
  getSession,
  listSessions,
  sendMessage as sendChatMessage,
  type ChatMessage,
  type ChatSession,
  type Citation,
} from '@/services/chatService'
import { createHandoff } from '@/services/ticketService'
import { cancelSkillRun, confirmSkillRun, type ConfirmCard } from '@/services/skillService'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const sessions = ref<ChatSession[]>([])
const messages = ref<ChatMessage[]>([])
const activeSession = ref<string>('')
const inputText = ref('')
const loading = ref(false)
const sending = ref(false)
const statusText = ref('')
const error = ref('')
const rightTab = ref<'profile' | 'evidence' | 'progress'>('evidence')
const confirmCard = ref<ConfirmCard | null>(null)
const confirming = ref(false)

let ws: WebSocket | null = null

/** 按时间排序；同秒时用户消息在助手之前，避免 WS 先到导致回复跑到上方 */
function sortMessages(list: ChatMessage[]): ChatMessage[] {
  const roleRank = (role: ChatMessage['role']) => (role === 'user' ? 0 : role === 'assistant' ? 1 : 2)
  return [...list].sort((a, b) => {
    const ta = new Date(a.created_at).getTime()
    const tb = new Date(b.created_at).getTime()
    if (ta !== tb) return ta - tb
    return roleRank(a.role) - roleRank(b.role)
  })
}

function upsertMessage(msg: ChatMessage) {
  const idx = messages.value.findIndex((m) => m.id === msg.id)
  if (idx >= 0) messages.value[idx] = msg
  else messages.value.push(msg)
  messages.value = sortMessages(messages.value)
}

const currentTitle = computed(() => {
  const s = sessions.value.find((x) => x.id === activeSession.value)
  return s?.title || '新对话'
})

const evidence = computed<Citation[]>(() => {
  const cites: Citation[] = []
  for (const m of messages.value) {
    if (m.role === 'assistant' && m.citations?.length) {
      for (const c of m.citations) {
        if (!cites.find((x) => x.document_id === c.document_id && x.text === c.text)) {
          cites.push(c)
        }
      }
    }
  }
  return cites.slice(-6)
})

const lastRoute = computed(() => {
  const last = [...messages.value].reverse().find((m) => m.role === 'assistant')
  return last?.route || '-'
})

function closeWs() {
  if (ws) {
    ws.close()
    ws = null
  }
}

function openWs(sessionId: string) {
  closeWs()
  ws = connectChatSocket(sessionId, {
    onStatus: (status) => {
      if (status === 'thinking') statusText.value = '思考中…'
      else if (status === 'done' || status === 'connected') statusText.value = ''
      else statusText.value = status
    },
    onMessage: (msg) => {
      upsertMessage(msg)
    },
  })
}

async function refreshSessions() {
  sessions.value = await listSessions()
}

async function loadSession(sessionId: string) {
  loading.value = true
  error.value = ''
  try {
    const detail = await getSession(sessionId)
    activeSession.value = detail.id
    messages.value = sortMessages(detail.messages || [])
    await refreshSessions()
    openWs(detail.id)
    await nextTick()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function ensureSessionAndMaybeSeed() {
  const sid = (route.query.sid as string) || ''
  const seed = sessionStorage.getItem('chat_seed')
  if (seed) sessionStorage.removeItem('chat_seed')

  if (sid) {
    await loadSession(sid)
    if (seed) await doSend(seed)
    return
  }

  if (seed) {
    const session = await createSession()
    activeSession.value = session.id
    router.replace({ path: '/chat', query: { sid: session.id } })
    await loadSession(session.id)
    await doSend(seed)
    return
  }

  const list = await listSessions()
  sessions.value = list
  if (list.length) {
    await loadSession(list[0].id)
    router.replace({ path: '/chat', query: { sid: list[0].id } })
  } else {
    const session = await createSession()
    router.replace({ path: '/chat', query: { sid: session.id } })
    await loadSession(session.id)
  }
}

async function doSend(text: string) {
  if (!text.trim() || sending.value) return
  sending.value = true
  error.value = ''
  statusText.value = '思考中…'
  const content = text.trim()
  const optimisticId = `local-${Date.now()}`
  upsertMessage({
    id: optimisticId,
    session_id: activeSession.value || '',
    role: 'user',
    content,
    citations: [],
    created_at: new Date().toISOString(),
  })
  try {
    const reply = await sendChatMessage(content, activeSession.value || undefined)
    activeSession.value = reply.session.id
    messages.value = messages.value.filter((m) => m.id !== optimisticId)
    // 先落用户消息再落助手，避免 WebSocket 先推助手导致「回复在上方」
    upsertMessage(reply.user_message)
    upsertMessage(reply.assistant_message)
    confirmCard.value = reply.confirm_card || reply.assistant_message.confirm_card || null
    await refreshSessions()
    if (route.query.sid !== reply.session.id) {
      router.replace({ path: '/chat', query: { sid: reply.session.id } })
    }
    openWs(reply.session.id)
  } catch (e) {
    messages.value = messages.value.filter((m) => m.id !== optimisticId)
    error.value = e instanceof Error ? e.message : '发送失败'
  } finally {
    sending.value = false
    statusText.value = ''
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  await doSend(text)
}

async function selectSession(id: string) {
  if (id === activeSession.value) return
  router.replace({ path: '/chat', query: { sid: id } })
  await loadSession(id)
}

async function newChat() {
  const session = await createSession()
  router.push({ path: '/chat', query: { sid: session.id } })
  await loadSession(session.id)
}

async function onConfirmSkill() {
  if (!confirmCard.value) return
  confirming.value = true
  error.value = ''
  try {
    const run = await confirmSkillRun(confirmCard.value.run_id)
    confirmCard.value = null
    messages.value.push({
      id: `local-${Date.now()}`,
      session_id: activeSession.value,
      role: 'assistant',
      content: run.task_id
        ? `已确认并执行（Mock 工具）。任务已创建：${run.task_id.slice(0, 8)}…`
        : `已确认并执行（Mock 工具）。状态：${run.status}`,
      citations: [],
      route: 'skill',
      created_at: new Date().toISOString(),
    })
    if (run.task_id) {
      setTimeout(() => router.push(`/tasks/${run.task_id}`), 600)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '确认失败'
  } finally {
    confirming.value = false
  }
}

async function onCancelSkill() {
  if (!confirmCard.value) return
  confirming.value = true
  try {
    await cancelSkillRun(confirmCard.value.run_id, '用户取消')
    confirmCard.value = null
    messages.value.push({
      id: `local-${Date.now()}`,
      session_id: activeSession.value,
      role: 'assistant',
      content: '已取消办理，未调用任何写工具。',
      citations: [],
      route: 'skill',
      created_at: new Date().toISOString(),
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '取消失败'
  } finally {
    confirming.value = false
  }
}

async function transfer() {
  sending.value = true
  error.value = ''
  try {
    if (!activeSession.value) {
      const session = await createSession()
      activeSession.value = session.id
      router.replace({ path: '/chat', query: { sid: session.id } })
      await loadSession(session.id)
    }
    const ticket = await createHandoff({
      session_id: activeSession.value,
      reason: '用户在对话页申请转人工',
      priority: 'high',
      topic: currentTitle.value,
    })
    messages.value.push({
      id: `local-${Date.now()}`,
      session_id: activeSession.value,
      role: 'assistant',
      content: `已转人工入队，工单 ${ticket.id.slice(0, 8)}…（${ticket.status}）。即将打开「我的工单」。`,
      citations: [],
      route: 'human_review',
      created_at: new Date().toISOString(),
    })
    await router.push('/tickets')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '转人工失败'
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  ensureSessionAndMaybeSeed().catch((e) => {
    error.value = e instanceof Error ? e.message : '初始化失败'
  })
})

watch(
  () => route.query.sid,
  (sid) => {
    if (sid && sid !== activeSession.value) {
      loadSession(String(sid))
    }
  },
)

onUnmounted(closeWs)
</script>

<template>
  <div class="chat-page">
    <aside class="col sessions">
      <button class="btn btn-primary new" type="button" @click="newChat">+ 新对话</button>
      <div class="label">会话</div>
      <button
        v-for="s in sessions"
        :key="s.id"
        type="button"
        class="session"
        :class="{ active: activeSession === s.id }"
        @click="selectSession(s.id)"
      >
        <div class="session-title">{{ s.title }}</div>
        <div class="session-time">{{ formatSessionTime(s.updated_at) }}</div>
      </button>
      <RouterLink to="/services" class="all-svc">全部服务 <span>P04</span></RouterLink>
    </aside>

    <section class="col messages card">
      <div class="mid-head">
        <strong>{{ currentTitle }}</strong>
        <button class="btn btn-ghost" type="button" @click="transfer">转人工</button>
      </div>
      <p v-if="error" class="banner err">{{ error }}</p>
      <p v-if="statusText" class="banner status">{{ statusText }}</p>
      <div class="message-list">
        <p v-if="loading" class="muted">加载中…</p>
        <div v-for="msg in messages" :key="msg.id" class="message-row" :class="msg.role">
          <div class="bubble">
            <p class="content">{{ msg.content }}</p>
            <div v-if="citeLabel(msg)" class="cite">{{ citeLabel(msg) }}</div>
            <span class="msg-time">{{ formatMsgTime(msg.created_at) }}</span>
          </div>
        </div>

        <div v-if="confirmCard" class="confirm-card">
          <div class="confirm-title">确认卡片 · {{ confirmCard.skill_name }}</div>
          <p class="confirm-summary">{{ confirmCard.summary }}</p>
          <p v-if="confirmCard.mock_tool" class="mock-tip">工具：{{ confirmCard.tool_name || 'Mock' }}（模拟调用）</p>
          <div class="confirm-actions">
            <button class="btn btn-ghost" type="button" :disabled="confirming" @click="onCancelSkill">
              取消
            </button>
            <button class="btn btn-primary" type="button" :disabled="confirming" @click="onConfirmSkill">
              {{ confirming ? '处理中…' : '确认办理' }}
            </button>
          </div>
        </div>
      </div>
      <div class="composer">
        <input
          v-model="inputText"
          class="input"
          placeholder="继续提问…"
          :disabled="sending"
          @keyup.enter="sendMessage"
        />
        <div class="composer-actions">
          <span class="chip" @click="transfer">@ 转人工</span>
          <button class="send" type="button" :disabled="sending" @click="sendMessage">↑</button>
        </div>
      </div>
    </section>

    <aside class="col context card">
      <div class="ctx-title">上下文</div>
      <div class="tabs">
        <button type="button" class="tab" :class="{ active: rightTab === 'profile' }" @click="rightTab = 'profile'">
          画像
        </button>
        <button type="button" class="tab" :class="{ active: rightTab === 'evidence' }" @click="rightTab = 'evidence'">
          证据
        </button>
        <button type="button" class="tab" :class="{ active: rightTab === 'progress' }" @click="rightTab = 'progress'">
          进度
        </button>
      </div>
      <div class="panel">
        <template v-if="rightTab === 'profile'">
          <p>
            <strong>{{ auth.user?.name || '员工' }}</strong>
            · {{ auth.user?.department || '—' }}
          </p>
          <p class="muted">账号：{{ auth.user?.username }}</p>
        </template>
        <template v-else-if="rightTab === 'evidence'">
          <template v-if="evidence.length">
            <div v-for="(c, idx) in evidence" :key="idx" class="ev-item">
              <p class="linkish">{{ c.title }}</p>
              <p class="muted">{{ c.text.slice(0, 80) }}{{ c.text.length > 80 ? '…' : '' }}</p>
            </div>
          </template>
          <p v-else class="muted">暂无引用来源，提问制度类问题后显示</p>
        </template>
        <template v-else>
          <p>最近路由：{{ lastRoute }}</p>
          <p class="muted">qa_direct / qa_rag / clarify / skill / human_review</p>
        </template>
      </div>
      <p class="foot-hint">从 P02 发问进入；空态回 Agent 首页</p>
    </aside>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - var(--header-h));
  min-height: 0;
  background: var(--color-bg);
}

.col {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.sessions {
  width: 248px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: 12px;
  gap: 6px;
  overflow: auto;
}

.new {
  height: 36px;
  width: 100%;
}

.label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-top: 6px;
}

.session {
  border: none;
  background: var(--color-bg);
  border-radius: 6px;
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
}

.session.active {
  background: var(--color-primary-soft);
}

.session-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session.active .session-title {
  color: var(--color-primary);
}

.session-time {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.all-svc {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  padding: 8px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  text-decoration: none;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

.messages {
  flex: 1;
  margin: 12px;
  border-radius: 12px;
  overflow: hidden;
}

.mid-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.btn-ghost {
  height: 30px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.banner {
  margin: 8px 16px 0;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
}
.banner.err {
  background: #fff1f0;
  color: #cf1322;
}
.banner.status {
  background: #e6f4ff;
  color: #1677ff;
}

.message-list {
  flex: 1;
  overflow: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 75%;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
}

.message-row.user .bubble {
  background: var(--color-primary-soft);
  border-color: transparent;
}

.content {
  margin: 0;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.55;
}

.cite {
  margin-top: 8px;
  font-size: 11px;
  color: var(--color-primary);
}

.msg-time {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.confirm-card {
  border: 1px solid var(--color-primary);
  background: #f0f7ff;
  border-radius: 10px;
  padding: 12px;
}

.confirm-title {
  font-weight: 700;
  margin-bottom: 6px;
}

.confirm-summary {
  white-space: pre-wrap;
  font-size: 12px;
  margin: 0 0 8px;
}

.mock-tip {
  font-size: 11px;
  color: #d46b08;
  margin: 0 0 8px;
}

.confirm-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.composer {
  border-top: 1px solid var(--color-border);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chip {
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.send {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  cursor: pointer;
  font-size: 16px;
}

.context {
  width: 280px;
  margin: 12px 12px 12px 0;
  border-radius: 12px;
  padding: 12px;
}

.ctx-title {
  font-weight: 700;
  margin-bottom: 8px;
}

.panel {
  flex: 1;
  overflow: auto;
  font-size: 13px;
  line-height: 1.5;
}

.muted {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.linkish {
  color: var(--color-primary);
  font-weight: 600;
  margin: 0 0 2px;
}

.ev-item {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.foot-hint {
  margin-top: auto;
  font-size: 11px;
  color: var(--color-text-secondary);
}

@media (max-width: 1100px) {
  .context {
    display: none;
  }
}
</style>
