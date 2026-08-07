<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import { listMyTickets, ticketStatusMap, type TicketItem } from '@/services/ticketService'

const router = useRouter()
const tickets = ref<TicketItem[]>([])
const loading = ref(false)
const error = ref('')

function fmt(iso: string) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '-'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    tickets.value = await listMyTickets()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="工单中心" description="查看转人工工单的进度与评价" icon="◆" />
    <div class="toolbar">
      <button type="button" class="btn btn-ghost" :disabled="loading" @click="load">刷新</button>
    </div>

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div class="card table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>工单号</th>
            <th>主题</th>
            <th>来源</th>
            <th>状态</th>
            <th>坐席</th>
            <th>创建时间</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tk in tickets" :key="tk.id">
            <td class="mono">{{ tk.id.slice(0, 8) }}</td>
            <td>{{ tk.subject }}</td>
            <td>{{ tk.channel }}</td>
            <td>
              <span class="tag" :class="ticketStatusMap[tk.status].tag">
                {{ ticketStatusMap[tk.status].label }}
              </span>
            </td>
            <td>{{ tk.agent_name || '—' }}</td>
            <td>{{ fmt(tk.created_at) }}</td>
            <td>{{ fmt(tk.updated_at) }}</td>
          </tr>
          <tr v-if="!loading && !tickets.length">
            <td colspan="7" class="muted">暂无工单。可在对话页点击「转人工」。</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="hint">
      提示：转人工后坐席将在队列接入；也可
      <button class="link" type="button" @click="router.push('/chat')">回对话</button>
      继续提问。
    </p>
  </div>
</template>

<style scoped>
.toolbar {
  margin: -8px 0 12px;
}
.err {
  color: #cf1322;
}
.muted {
  color: var(--color-text-secondary);
  text-align: center;
  padding: 16px;
}
.hint {
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.link {
  border: none;
  background: none;
  color: var(--color-primary);
  cursor: pointer;
  padding: 0;
  font-size: inherit;
}
</style>
