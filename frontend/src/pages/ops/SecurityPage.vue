<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  getRbac,
  listAudits,
  type AuditLogItem,
  type RbacMatrix,
} from '@/services/opsService'

const activeTab = ref<'matrix' | 'audit'>('matrix')
const rbac = ref<RbacMatrix | null>(null)
const auditLogs = ref<AuditLogItem[]>([])
const filterOperator = ref('')
const filterAction = ref('')
const loading = ref(false)
const error = ref('')

const roleLabel: Record<string, string> = {
  employee: '员工',
  agent: '坐席',
  admin: '运营管理员',
  system: '系统',
}

async function loadRbac() {
  rbac.value = await getRbac()
}

async function loadAudits() {
  auditLogs.value = await listAudits({
    operator: filterOperator.value.trim() || undefined,
    action: filterAction.value.trim() || undefined,
  })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([loadRbac(), loadAudits()])
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function fmtTime(iso: string) {
  if (!iso) return '—'
  return iso.replace('T', ' ').slice(0, 19)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="权限与安全审计" description="RBAC 权限矩阵与操作审计日志" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="tabs">
      <button
        type="button"
        class="tab"
        :class="{ active: activeTab === 'matrix' }"
        @click="activeTab = 'matrix'"
      >
        权限矩阵
      </button>
      <button
        type="button"
        class="tab"
        :class="{ active: activeTab === 'audit' }"
        @click="activeTab = 'audit'"
      >
        审计日志
      </button>
    </div>

    <div v-if="activeTab === 'matrix' && rbac" class="card table-wrap">
      <table class="table matrix-table">
        <thead>
          <tr>
            <th>权限项</th>
            <th v-for="role in rbac.roles" :key="role">{{ role }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="perm in rbac.permissions" :key="perm.key">
            <td>{{ perm.label }}</td>
            <td v-for="role in rbac.roles" :key="role" class="cell-center">
              <span v-if="rbac.matrix[role]?.[perm.key]" class="tag tag-success">✓</span>
              <span v-else class="tag tag-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="activeTab === 'audit'" class="audit-wrap">
      <div class="filters">
        <input v-model="filterOperator" class="input" placeholder="操作人" />
        <input v-model="filterAction" class="input" placeholder="动作关键词" />
        <button type="button" class="btn btn-primary" @click="loadAudits">筛选</button>
      </div>
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>日志 ID</th>
              <th>操作人</th>
              <th>角色</th>
              <th>操作</th>
              <th>目标</th>
              <th>IP</th>
              <th>时间</th>
              <th>结果</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in auditLogs" :key="log.id">
              <td class="mono">{{ log.id.slice(0, 8) }}</td>
              <td>{{ log.operator }}</td>
              <td>{{ roleLabel[log.role] || log.role }}</td>
              <td>{{ log.action }}</td>
              <td>{{ log.target }}</td>
              <td class="mono">{{ log.ip }}</td>
              <td>{{ fmtTime(log.created_at) }}</td>
              <td>
                <span class="tag" :class="log.result === 'success' ? 'tag-success' : 'tag-danger'">
                  {{ log.result === 'success' ? '成功' : '拒绝' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
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
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 16px;
}
.tab {
  padding: 10px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}
.tab.active {
  color: var(--color-primary, #1677ff);
  border-bottom-color: var(--color-primary, #1677ff);
  font-weight: 600;
}
.table-wrap {
  overflow-x: auto;
}
.cell-center {
  text-align: center;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.filters .input {
  max-width: 200px;
}
</style>
