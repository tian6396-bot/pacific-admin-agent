<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  listBadCases,
  updateBadCase,
  type BadCaseItem,
  type BadCaseStatus,
} from '@/services/opsService'

const props = defineProps<{ embedded?: boolean }>()

const filters = ['全部', '行政', '财务', 'HR', 'IT'] as const
const activeFilter = ref<string>('全部')
const cases = ref<BadCaseItem[]>([])
const selectedId = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const selected = computed(() => cases.value.find((c) => c.id === selectedId.value))

const severityMap = {
  high: { label: '高', tag: 'tag-danger' },
  medium: { label: '中', tag: 'tag-primary' },
  low: { label: '低', tag: 'tag-muted' },
} as const

const statusMap: Record<BadCaseStatus, { label: string; tag: string }> = {
  open: { label: '待处理', tag: 'tag-danger' },
  improved: { label: '已改进', tag: 'tag-success' },
  ignored: { label: '已忽略', tag: 'tag-muted' },
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    cases.value = await listBadCases(activeFilter.value)
    if (!cases.value.find((c) => c.id === selectedId.value)) {
      selectedId.value = cases.value[0]?.id || ''
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function setStatus(status: BadCaseStatus) {
  if (!selected.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await updateBadCase(selected.value.id, { status })
    const idx = cases.value.findIndex((c) => c.id === updated.id)
    if (idx >= 0) cases.value[idx] = updated
  } catch (e) {
    error.value = e instanceof Error ? e.message : '更新失败'
  } finally {
    saving.value = false
  }
}

function fmtDate(iso: string) {
  return iso?.slice(0, 10) || '—'
}

watch(activeFilter, load)
onMounted(load)
</script>

<template>
  <div class="page" :class="{ embedded: props.embedded }">
    <PageHeader
      v-if="!props.embedded"
      title="Bad Case 管理"
      description="坏例沉淀、根因分析与优化建议"
      icon="◆"
    />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="filters">
      <button
        v-for="f in filters"
        :key="f"
        type="button"
        class="filter-chip"
        :class="{ active: activeFilter === f }"
        @click="activeFilter = f"
      >
        {{ f }}
      </button>
    </div>

    <div class="layout">
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>编号</th>
              <th>标题</th>
              <th>领域</th>
              <th>意图</th>
              <th>严重度</th>
              <th>状态</th>
              <th>上报日期</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in cases"
              :key="c.id"
              :class="{ active: selectedId === c.id }"
              @click="selectedId = c.id"
            >
              <td class="mono">{{ c.id.slice(0, 8) }}</td>
              <td>{{ c.title }}</td>
              <td>{{ c.domain }}</td>
              <td>{{ c.intent }}</td>
              <td>
                <span class="tag" :class="severityMap[c.severity].tag">
                  {{ severityMap[c.severity].label }}
                </span>
              </td>
              <td>
                <span class="tag" :class="statusMap[c.status].tag">
                  {{ statusMap[c.status].label }}
                </span>
              </td>
              <td>{{ fmtDate(c.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <aside v-if="selected" class="card detail-panel">
        <div class="panel-head">{{ selected.title }}</div>
        <div class="detail-body">
          <div class="meta-row">
            <span class="mono">{{ selected.id }}</span>
            <span class="mono">{{ selected.session_id || '—' }}</span>
          </div>
          <div class="block">
            <span class="label">问题描述</span>
            <p>{{ selected.description || '—' }}</p>
          </div>
          <div class="block">
            <span class="label">根因分析</span>
            <p>{{ selected.root_cause || '—' }}</p>
          </div>
          <div class="block">
            <span class="label">优化建议</span>
            <p class="suggestion">{{ selected.suggestion || '—' }}</p>
          </div>
          <div class="detail-actions">
            <button
              type="button"
              class="btn btn-primary"
              :disabled="saving || selected.status === 'improved'"
              @click="setStatus('improved')"
            >
              标记已改进
            </button>
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="saving || selected.status === 'ignored'"
              @click="setStatus('ignored')"
            >
              忽略
            </button>
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="saving || selected.status === 'open'"
              @click="setStatus('open')"
            >
              重开
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.err {
  color: var(--color-danger, #cf1322);
  font-size: 13px;
  margin: 0 0 12px;
}
.hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}
.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.layout {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
}
.table-wrap {
  overflow-x: auto;
}
.table tbody tr {
  cursor: pointer;
}
.panel-head {
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
}
.detail-body {
  padding: 16px;
}
.meta-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.block {
  margin-bottom: 16px;
}
.block p {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.6;
}
.suggestion {
  white-space: pre-line;
}
.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}
@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
