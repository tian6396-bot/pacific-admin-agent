<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { getUnreadCount } from '@/services/notifyService'
import { listTasks } from '@/services/taskService'

const menus = [
  { label: '工作台', to: '/workbench' },
  { label: '智能对话', to: '/chat' },
  { label: '我的任务', to: '/tasks' },
  { label: '我的工单', to: '/tickets' },
  { label: '材料', to: '/materials' },
  { label: '内容产出', to: '/content' },
  { label: '消息', to: '/messages' },
  { label: '设置', to: '/settings' },
]

const route = useRoute()
const todoCount = ref(0)
const unread = ref(0)

async function refreshMeta() {
  try {
    const [tasks, n] = await Promise.all([listTasks('active'), getUnreadCount()])
    todoCount.value = tasks.length
    unread.value = n
  } catch {
    /* 顶栏摘要失败不阻断页面 */
  }
}

onMounted(refreshMeta)
watch(
  () => route.fullPath,
  () => {
    void refreshMeta()
  },
)
</script>

<template>
  <div class="layout">
    <AppHeader brand="P-Assistant" :menus="menus">
      <template #meta>
        <span class="meta">
          <RouterLink class="meta-link" to="/tasks" title="查看我的任务">待办 {{ todoCount }}</RouterLink>
          <span class="meta-sep">·</span>
          <RouterLink class="meta-link" to="/messages" title="查看消息">未读 {{ unread }}</RouterLink>
        </span>
      </template>
    </AppHeader>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  min-height: 0;
}

.meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-right: 4px;
}

.meta-sep {
  opacity: 0.55;
}

.meta-link {
  color: inherit;
  text-decoration: none;
  border-radius: 4px;
  padding: 2px 4px;
  transition: color 0.15s ease, background 0.15s ease;
}

.meta-link:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft, rgba(22, 119, 255, 0.08));
}

.meta-link.router-link-active {
  color: var(--color-primary);
  font-weight: 600;
}
</style>
