<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from '@/services/notifyService'

const messages = ref<NotificationItem[]>([])
const unread = ref(0)
const loading = ref(false)
const error = ref('')

const typeMap = {
  task: { label: '任务', tag: 'tag-primary' },
  system: { label: '系统', tag: 'tag-muted' },
  ticket: { label: '工单', tag: 'tag-success' },
  material: { label: '材料', tag: 'tag-primary' },
} as const

function fmtTime(iso: string) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '—'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await listNotifications()
    messages.value = res.items
    unread.value = res.unread
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function markRead(id: string) {
  await markNotificationRead(id)
  await load()
}

async function markAllRead() {
  await markAllNotificationsRead()
  await load()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="消息中心" description="任务、工单与材料动态（站内聚合）" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>

    <div class="toolbar">
      <button class="btn btn-ghost" type="button" :disabled="loading" @click="markAllRead">
        全部标为已读
      </button>
      <span class="meta">未读 {{ unread }}</span>
      <button class="btn btn-ghost" type="button" :disabled="loading" @click="load">刷新</button>
    </div>

    <div class="card list">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="row"
        :class="{ unread: !msg.read }"
        @click="markRead(msg.id)"
      >
        <div class="main">
          <div class="title-row">
            <span class="tag" :class="typeMap[msg.type].tag">{{ typeMap[msg.type].label }}</span>
            <strong>{{ msg.title }}</strong>
          </div>
          <p>{{ msg.preview }}</p>
          <RouterLink v-if="msg.link" :to="msg.link" class="link" @click.stop>
            查看详情
          </RouterLink>
        </div>
        <time>{{ fmtTime(msg.created_at) }}</time>
      </div>
      <p v-if="!loading && !messages.length" class="muted">暂无消息</p>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.meta {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.list {
  padding: 0;
}
.row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
}
.row.unread {
  background: var(--color-primary-soft);
}
.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.main p {
  margin: 0 0 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
time {
  font-size: 12px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}
.muted {
  text-align: center;
  padding: 24px;
  color: var(--color-text-secondary);
}
.err {
  color: #cf1322;
  font-size: 13px;
}
</style>
