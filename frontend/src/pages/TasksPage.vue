<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import { listTasks, statusMap, type TaskItem, type TaskTab } from '@/services/taskService'

const router = useRouter()
const route = useRoute()

const initialTab = (route.query.tab as TaskTab) || 'active'
const activeTab = ref<TaskTab>(
  ['active', 'approve', 'history', 'planner'].includes(initialTab) ? initialTab : 'active',
)

const tabs: { key: TaskTab; label: string }[] = [
  { key: 'active', label: '进行中' },
  { key: 'approve', label: '待我审批' },
  { key: 'history', label: '历史' },
  { key: 'planner', label: 'Planner' },
]

const tasks = ref<TaskItem[]>([])
const loading = ref(false)
const error = ref('')

const basePath = route.path.startsWith('/agent') ? '/agent/tasks' : '/tasks'

async function load() {
  loading.value = true
  error.value = ''
  try {
    tasks.value = await listTasks(activeTab.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function goDetail(id: string) {
  router.push(`${basePath}/${id}`)
}

function fmtTime(iso: string) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '-'
}

watch(activeTab, (tab) => {
  router.replace({ path: route.path, query: { tab } })
  load()
})

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="我的任务" description="进行中 / 待审批 / 历史 / Planner 占位" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>

    <div class="filters">
      <button
        v-for="f in tabs"
        :key="f.key"
        class="filter-chip"
        :class="{ active: activeTab === f.key }"
        type="button"
        @click="activeTab = f.key"
      >
        {{ f.label }}
      </button>
    </div>

    <div class="card table-wrap">
      <p v-if="loading" class="muted">加载中…</p>
      <table v-else class="table">
        <thead>
          <tr>
            <th>任务编号</th>
            <th>标题</th>
            <th>类型</th>
            <th>状态</th>
            <th>更新时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tasks" :key="t.id">
            <td class="mono">{{ t.id.slice(0, 8) }}</td>
            <td>{{ t.title }}</td>
            <td>{{ t.domain_label || t.service_name }}</td>
            <td>
              <span class="tag" :class="statusMap[t.status].tag">{{ statusMap[t.status].label }}</span>
            </td>
            <td>{{ fmtTime(t.updated_at) }}</td>
            <td>
              <button class="link" type="button" @click="goDetail(t.id)">查看</button>
            </td>
          </tr>
          <tr v-if="!tasks.length">
            <td colspan="6" class="empty">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.filter-chip {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.filter-chip.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 600;
}

.table-wrap {
  overflow-x: auto;
}

.link {
  border: none;
  background: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: inherit;
  padding: 0;
}

.empty,
.muted {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 16px;
}

.err {
  color: #cf1322;
  font-size: 13px;
}
</style>
