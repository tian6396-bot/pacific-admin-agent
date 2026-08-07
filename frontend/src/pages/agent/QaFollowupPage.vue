<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  listFollowups,
  listQaRecords,
  updateFollowup,
  type FollowupItem,
  type QaRecord,
} from '@/services/qaService'

const activeTab = ref<'qa' | 'followup'>('qa')
const qaRecords = ref<QaRecord[]>([])
const followups = ref<FollowupItem[]>([])
const loading = ref(false)
const error = ref('')

const statusMap = {
  pending: { label: '待回访', tag: 'tag-primary' },
  done: { label: '已完成', tag: 'tag-success' },
  overdue: { label: '已逾期', tag: 'tag-danger' },
} as const

function scoreTag(score: number) {
  if (score >= 90) return 'tag-success'
  if (score >= 75) return 'tag-primary'
  return 'tag-danger'
}

function fmtTime(iso: string) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '—'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [qa, fu] = await Promise.all([listQaRecords(), listFollowups()])
    qaRecords.value = qa
    followups.value = fu
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function completeFollowup(id: string) {
  try {
    await updateFollowup(id, { status: 'done' })
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '更新失败'
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="质检与回访" description="会话质检打分与回访任务管理" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>

    <div class="tabs">
      <button
        type="button"
        class="tab"
        :class="{ active: activeTab === 'qa' }"
        @click="activeTab = 'qa'"
      >
        质检打分
      </button>
      <button
        type="button"
        class="tab"
        :class="{ active: activeTab === 'followup' }"
        @click="activeTab = 'followup'"
      >
        回访任务
      </button>
      <button type="button" class="btn btn-ghost" :disabled="loading" @click="load">刷新</button>
    </div>

    <div v-if="activeTab === 'qa'" class="card table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>质检编号</th>
            <th>会话</th>
            <th>坐席</th>
            <th>总分</th>
            <th>评分明细</th>
            <th>质检员</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in qaRecords" :key="r.id">
            <td class="mono">{{ r.id.slice(0, 8) }}</td>
            <td class="mono">{{ r.session_label || '—' }}</td>
            <td>{{ r.agent_name }}</td>
            <td>
              <span class="tag" :class="scoreTag(r.score)">{{ r.score }} 分</span>
            </td>
            <td>
              <span v-for="item in r.items" :key="item.label" class="score-chip">
                {{ item.label }} {{ item.score }}/{{ item.max }}
              </span>
            </td>
            <td>{{ r.reviewer }}</td>
            <td>{{ fmtTime(r.created_at) }}</td>
          </tr>
          <tr v-if="!loading && !qaRecords.length">
            <td colspan="7" class="muted">暂无质检记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="card table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>任务编号</th>
            <th>员工</th>
            <th>回访类型</th>
            <th>截止日期</th>
            <th>负责人</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in followups" :key="t.id">
            <td class="mono">{{ t.id }}</td>
            <td>{{ t.employee_name }}</td>
            <td>{{ t.type }}</td>
            <td>{{ t.due_date }}</td>
            <td>{{ t.assignee }}</td>
            <td>
              <span class="tag" :class="statusMap[t.status].tag">
                {{ statusMap[t.status].label }}
              </span>
            </td>
            <td>
              <button
                v-if="t.status !== 'done'"
                type="button"
                class="link"
                @click="completeFollowup(t.id)"
              >
                标记完成
              </button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.tab {
  padding: 8px 14px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
}
.tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}
.table-wrap {
  overflow-x: auto;
}
.score-chip {
  display: inline-block;
  margin: 2px 4px 2px 0;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-bg);
  font-size: 11px;
  color: var(--color-text-secondary);
}
.err {
  color: #cf1322;
}
.muted {
  color: var(--color-text-secondary);
  text-align: center;
  padding: 12px;
}
</style>
