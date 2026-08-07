<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import {
  createSession,
  formatSessionTime,
  listSessions,
  type ChatSession,
} from '@/services/chatService'

const router = useRouter()
const inputText = ref('')
const sessions = ref<ChatSession[]>([])
const loading = ref(false)
const sending = ref(false)
const error = ref('')

const p0Items = [
  { label: '费用报销', to: '/services/expense/apply' },
  { label: '年假申请', to: '/services/leave/apply' },
  { label: 'IT 报修', to: '/services/repair/apply' },
  { label: '会议室预订', to: '/services/meeting/apply' },
]

const chips = ['@ 转人工', '费用报销', '请假']

const suggestions = [
  'T3 去深圳酒店住宿标准是多少？',
  '帮我发起一笔差旅交通报销',
  '今年年假还剩几天，怎么请？',
  '笔记本无法开机，如何 IT 报修？',
]

async function loadSessions() {
  loading.value = true
  error.value = ''
  try {
    sessions.value = await listSessions()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载会话失败'
  } finally {
    loading.value = false
  }
}

async function goChat(seed?: string) {
  if (sending.value) return
  sending.value = true
  error.value = ''
  if (seed) sessionStorage.setItem('chat_seed', seed)
  try {
    const session = await createSession()
    await router.push({ path: '/chat', query: { sid: session.id } })
  } catch (e) {
    error.value =
      e instanceof Error
        ? `无法进入对话：${e.message}（请确认后端 8010 / 前端 5173 已启动）`
        : '无法进入对话，请确认服务已启动'
    // 仍尝试进入对话页，由 ChatPage 自行建会话
    try {
      await router.push('/chat')
    } catch {
      /* ignore */
    }
  } finally {
    sending.value = false
  }
}

function send() {
  const text = inputText.value.trim()
  if (!text) {
    void goChat()
    return
  }
  void goChat(text)
}

function openSession(id: string) {
  router.push({ path: '/chat', query: { sid: id } })
}

onMounted(loadSessions)
</script>

<template>
  <div class="agent-home">
    <aside class="side">
      <button class="btn btn-primary new-chat" type="button" @click="goChat()">+ 新对话</button>
      <div class="section-label">最近会话</div>
      <p v-if="loading" class="hint">加载中…</p>
      <p v-else-if="error" class="hint err">{{ error }}</p>
      <button
        v-for="s in sessions"
        :key="s.id"
        type="button"
        class="side-item"
        @click="openSession(s.id)"
      >
        <span class="side-title">{{ s.title }}</span>
        <span class="side-time">{{ formatSessionTime(s.updated_at) }}</span>
      </button>
      <p v-if="!loading && !sessions.length" class="hint">暂无会话，直接提问开始</p>
      <div class="divider" />
      <div class="section-label">P0 快捷办理</div>
      <RouterLink v-for="p in p0Items" :key="p.label" :to="p.to" class="side-item muted">
        {{ p.label }}
      </RouterLink>
      <RouterLink to="/services" class="all-services">
        <span>全部服务</span>
        <span class="arrow">→</span>
      </RouterLink>
      <p class="hint">主路径：直接问 Agent</p>
    </aside>

    <section class="main">
      <div class="hero">
        <div class="avatar">AI</div>
        <h1>Hi，今天我能为你做些什么？</h1>
        <p class="sub">行政制度问答 · 服务办理引导 · 低置信可转人工</p>
      </div>

      <div class="composer card">
        <p v-if="error" class="hint err composer-err">{{ error }}</p>
        <input
          v-model="inputText"
          class="input"
          placeholder="例如：T3 去深圳酒店标准是多少？"
          :disabled="sending"
          @keyup.enter="send"
        />
        <div class="composer-bar">
          <div class="chips">
            <button
              v-for="c in chips"
              :key="c"
              type="button"
              class="chip"
              :disabled="sending"
              @click="goChat(c)"
            >
              {{ c }}
            </button>
          </div>
          <button class="btn btn-primary send-btn" type="button" :disabled="sending" @click="send">
            {{ sending ? '跳转中…' : '发送' }}
          </button>
        </div>
      </div>

      <div class="suggestions">
        <button
          v-for="s in suggestions"
          :key="s"
          type="button"
          class="suggest"
          @click="goChat(s)"
        >
          {{ s }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.agent-home {
  display: flex;
  min-height: calc(100vh - var(--header-h));
  background: var(--color-bg);
}

.side {
  width: 260px;
  border-right: 1px solid var(--color-border);
  background: var(--color-surface);
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.new-chat {
  height: 36px;
  width: 100%;
  margin-bottom: 8px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 8px 4px 4px;
}

.side-item {
  border: none;
  background: transparent;
  text-align: left;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text);
  text-decoration: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.side-item:hover {
  background: var(--color-bg);
}

.side-item.muted {
  color: var(--color-text-secondary);
}

.side-title {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.side-time {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.divider {
  height: 1px;
  background: var(--color-border);
  margin: 8px 0;
}

.all-services {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  text-decoration: none;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 600;
}

.hint {
  font-size: 11px;
  color: var(--color-text-secondary);
  padding: 4px 8px;
  margin: 0;
}

.hint.err {
  color: #cf1322;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px 32px;
  gap: 20px;
}

.hero {
  text-align: center;
}

.avatar {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 50%;
  background: var(--color-primary-soft, #e6f4ff);
  color: var(--color-primary);
  display: grid;
  place-items: center;
  font-weight: 700;
}

.hero h1 {
  margin: 0 0 8px;
  font-size: 26px;
}

.sub {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.composer {
  width: min(720px, 100%);
  padding: 12px;
}

.composer-err {
  margin-bottom: 8px;
}

.composer .input {
  width: 100%;
  height: 44px;
}

.composer-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  gap: 8px;
}

.send-btn {
  flex: 0 0 auto;
  white-space: nowrap;
  writing-mode: horizontal-tb;
  min-width: 72px;
}

.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.suggestions {
  width: min(720px, 100%);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.suggest {
  text-align: left;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text);
}

.suggest:hover {
  border-color: var(--color-primary);
}

@media (max-width: 800px) {
  .agent-home {
    flex-direction: column;
  }
  .side {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
  .suggestions {
    grid-template-columns: 1fr;
  }
}
</style>
