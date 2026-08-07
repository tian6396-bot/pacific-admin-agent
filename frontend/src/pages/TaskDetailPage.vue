<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import {
  approveTask,
  getTask,
  rejectTask,
  requestMaterials,
  statusMap,
  type TaskDetail,
} from '@/services/taskService'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const taskId = computed(() => (route.params.id as string) || '')
const detail = ref<TaskDetail | null>(null)
const loading = ref(false)
const error = ref('')
const message = ref('')
const acting = ref(false)

const listPath = computed(() => (route.path.startsWith('/agent') ? '/agent/tasks' : '/tasks'))

const canApprove = computed(() => {
  if (!detail.value) return false
  if (detail.value.status !== 'pending_approve') return false
  // 后端以 approver_id 校验；前端按角色展示按钮（坐席/管理员）
  return auth.user?.role === 'agent' || auth.user?.role === 'admin'
})

const canRequestMaterials = computed(() => {
  if (!detail.value || !auth.user) return false
  return (
    detail.value.status !== 'done' &&
    detail.value.status !== 'rejected' &&
    detail.value.status !== 'cancelled' &&
    ['pending_approve', 'processing'].includes(detail.value.status) &&
    auth.user.role === 'employee'
  )
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    detail.value = await getTask(taskId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function onApprove() {
  acting.value = true
  try {
    detail.value = await approveTask(taskId.value, '演示审批通过')
    message.value = '已通过'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '审批失败'
  } finally {
    acting.value = false
  }
}

async function onReject() {
  acting.value = true
  try {
    detail.value = await rejectTask(taskId.value, '演示驳回')
    message.value = '已驳回'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '驳回失败'
  } finally {
    acting.value = false
  }
}

async function onMaterials() {
  acting.value = true
  try {
    detail.value = await requestMaterials(taskId.value)
    message.value = '已标记待补充材料'
    setTimeout(() => router.push('/materials'), 600)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    acting.value = false
  }
}

function fmtTime(iso: string) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '—'
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader
      :title="`任务详情 · ${taskId.slice(0, 8)}`"
      :description="detail ? `${detail.service_name} · ${detail.title}` : '加载中'"
      icon="◆"
    />

    <p v-if="error" class="banner err">{{ error }}</p>
    <p v-if="message" class="banner ok">{{ message }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-if="detail" class="detail-grid">
      <div class="card info-card">
        <h3>基本信息</h3>
        <dl>
          <dt>任务编号</dt>
          <dd class="mono">{{ detail.id }}</dd>
          <dt>申请类型</dt>
          <dd>{{ detail.service_name }}</dd>
          <dt>当前状态</dt>
          <dd>
            <span class="tag" :class="statusMap[detail.status].tag">
              {{ statusMap[detail.status].label }}
            </span>
          </dd>
          <dt>申请人</dt>
          <dd>{{ detail.applicant_name }}</dd>
          <dt>审批人</dt>
          <dd>{{ detail.approver_name || '—' }}</dd>
          <dt>表单摘要</dt>
          <dd>
            金额/天数：{{ detail.form.amount || '—' }} · 日期：{{ detail.form.date || '—' }}
            <br />
            部门：{{ detail.form.department || '—' }}
            <br />
            事由：{{ detail.form.reason || '—' }}
          </dd>
          <dt>创建时间</dt>
          <dd>{{ fmtTime(detail.created_at) }}</dd>
        </dl>
        <div class="actions">
          <button class="btn btn-ghost" type="button" @click="router.push(listPath)">返回列表</button>
          <button
            v-if="canRequestMaterials"
            class="btn btn-ghost"
            type="button"
            :disabled="acting"
            @click="onMaterials"
          >
            补充材料
          </button>
          <button
            v-if="canApprove"
            class="btn btn-ghost"
            type="button"
            :disabled="acting"
            @click="onReject"
          >
            驳回
          </button>
          <button
            v-if="canApprove"
            class="btn btn-primary"
            type="button"
            :disabled="acting"
            @click="onApprove"
          >
            通过
          </button>
        </div>
      </div>

      <div class="card timeline-card">
        <h3>办理进度</h3>
        <ul class="timeline">
          <li
            v-for="(item, idx) in detail.events"
            :key="item.id"
            :class="{
              done: item.done,
              current: !item.done && detail.events.slice(0, idx).every((e) => e.done),
            }"
          >
            <div class="dot" />
            <div class="content">
              <div class="tl-head">
                <span class="tl-title">{{ item.title }}</span>
                <span class="tl-time">{{ fmtTime(item.time) }}</span>
              </div>
              <p class="tl-desc">{{ item.desc }}</p>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.banner {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  margin-bottom: 12px;
}
.banner.err {
  background: #fff1f0;
  color: #cf1322;
}
.banner.ok {
  background: #f6ffed;
  color: #389e0d;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 14px;
}

.info-card,
.timeline-card {
  padding: 16px;
}

h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

dl {
  margin: 0;
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 8px 10px;
  font-size: 13px;
}

dt {
  color: var(--color-text-secondary);
}

dd {
  margin: 0;
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline li {
  display: flex;
  gap: 10px;
  padding-bottom: 14px;
  position: relative;
}

.timeline li:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 14px;
  bottom: 0;
  width: 2px;
  background: var(--color-border);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-border);
  margin-top: 3px;
  flex-shrink: 0;
  z-index: 1;
}

.timeline li.done .dot {
  background: var(--color-success, #52c41a);
}

.timeline li.current .dot {
  background: var(--color-primary);
}

.tl-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
}

.tl-title {
  font-weight: 600;
}

.tl-time {
  color: var(--color-text-secondary);
  font-size: 11px;
}

.tl-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.muted {
  color: var(--color-text-secondary);
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
