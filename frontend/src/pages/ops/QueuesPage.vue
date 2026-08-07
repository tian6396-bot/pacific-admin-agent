<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { listQueues, updateQueue, type QueueSlaItem } from '@/services/opsService'

const queues = ref<QueueSlaItem[]>([])
const selectedId = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const message = ref('')

const form = ref({
  name: '',
  skill_group: '',
  sla_minutes: 5,
  priority: 1,
  max_wait: 10,
  alert_threshold: 80,
})

function selectQueue(id: string) {
  selectedId.value = id
  const q = queues.value.find((item) => item.id === id)
  if (q) {
    form.value = {
      name: q.name,
      skill_group: q.skill_group,
      sla_minutes: q.sla_minutes,
      priority: q.priority,
      max_wait: q.max_wait,
      alert_threshold: q.alert_threshold,
    }
  }
  message.value = ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    queues.value = await listQueues()
    if (!selectedId.value && queues.value.length) {
      selectQueue(queues.value[0].id)
    } else if (selectedId.value) {
      selectQueue(selectedId.value)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function resetForm() {
  if (selectedId.value) selectQueue(selectedId.value)
}

async function save() {
  if (!selectedId.value) return
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    const updated = await updateQueue(selectedId.value, { ...form.value })
    const idx = queues.value.findIndex((q) => q.id === updated.id)
    if (idx >= 0) queues.value[idx] = updated
    message.value = '已保存'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="队列与 SLA 管理" description="技能组队列配置与 SLA 阈值" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-else-if="message" class="ok">{{ message }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="layout">
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>队列 ID</th>
              <th>名称</th>
              <th>技能组</th>
              <th>坐席数</th>
              <th>SLA</th>
              <th>优先级</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="q in queues"
              :key="q.id"
              :class="{ active: selectedId === q.id }"
              @click="selectQueue(q.id)"
            >
              <td class="mono">{{ q.id }}</td>
              <td>{{ q.name }}</td>
              <td>{{ q.skill_group }}</td>
              <td>{{ q.agents }}</td>
              <td>{{ q.sla_minutes }} 分钟</td>
              <td>{{ q.priority }}</td>
              <td>
                <span class="tag" :class="q.status === 'active' ? 'tag-success' : 'tag-muted'">
                  {{ q.status === 'active' ? '启用' : '禁用' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <aside class="card form-panel">
        <div class="panel-head">SLA 配置 · {{ form.name || '—' }}</div>
        <div class="form-body">
          <div class="field">
            <label class="label" for="q-name">队列名称</label>
            <input id="q-name" v-model="form.name" class="input" />
          </div>
          <div class="field">
            <label class="label" for="q-skill">技能组</label>
            <input id="q-skill" v-model="form.skill_group" class="input" />
          </div>
          <div class="field">
            <label class="label" for="q-sla">SLA 响应时限（分钟）</label>
            <input id="q-sla" v-model.number="form.sla_minutes" type="number" class="input" />
          </div>
          <div class="field">
            <label class="label" for="q-priority">优先级</label>
            <input id="q-priority" v-model.number="form.priority" type="number" class="input" />
          </div>
          <div class="field">
            <label class="label" for="q-max">最大等待（分钟）</label>
            <input id="q-max" v-model.number="form.max_wait" type="number" class="input" />
          </div>
          <div class="field">
            <label class="label" for="q-alert">预警阈值（%）</label>
            <input id="q-alert" v-model.number="form.alert_threshold" type="number" class="input" />
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-ghost" :disabled="saving" @click="resetForm">
              重置
            </button>
            <button type="button" class="btn btn-primary" :disabled="saving" @click="save">
              保存配置
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
.ok {
  color: var(--color-success, #389e0d);
  font-size: 13px;
  margin: 0 0 12px;
}
.hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}
.layout {
  display: grid;
  grid-template-columns: 1fr 340px;
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
  font-size: 13px;
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
}
.form-body {
  padding: 20px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
