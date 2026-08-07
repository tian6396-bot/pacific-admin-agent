<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import { applyTask } from '@/services/taskService'

const route = useRoute()
const router = useRouter()

const serviceNames: Record<string, string> = {
  expense: '费用报销',
  leave: '请假申请',
  meeting: '会议室预订',
  visitor: '访客预约',
  repair: 'IT 报修',
  'planner-demo': '开放式材料任务',
}

const serviceId = computed(() => (route.params.id as string) || 'expense')
const serviceName = computed(() => serviceNames[serviceId.value] || '服务申请')

const form = ref({
  title: '',
  amount: '',
  date: '',
  reason: '',
  department: '行政部',
})

const toast = ref('')
const submitting = ref(false)
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value = ''
  }, 2500)
}

async function submit() {
  if (!form.value.title.trim()) {
    showToast('请填写申请标题')
    return
  }
  submitting.value = true
  try {
    const task = await applyTask({
      service_id: serviceId.value,
      title: form.value.title.trim(),
      form: {
        amount: form.value.amount,
        date: form.value.date,
        reason: form.value.reason,
        department: form.value.department,
      },
    })
    showToast('提交成功，正在跳转任务详情')
    setTimeout(() => {
      router.push(`/tasks/${task.id}`)
    }, 500)
  } catch (e) {
    showToast(e instanceof Error ? e.message : '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page">
    <PageHeader :title="`${serviceName}申请`" description="填写表单并提交审批" icon="◆" />

    <div class="card form-card">
      <div class="field">
        <label class="label" for="title">申请标题</label>
        <input id="title" v-model="form.title" class="input" placeholder="例如：2026年3月上海出差报销" />
      </div>
      <div class="form-row">
        <div class="field">
          <label class="label" for="amount">金额 / 天数（可选）</label>
          <input id="amount" v-model="form.amount" class="input" placeholder="如 2850 或 3" />
        </div>
        <div class="field">
          <label class="label" for="date">发生日期</label>
          <input id="date" v-model="form.date" class="input" type="date" />
        </div>
      </div>
      <div class="field">
        <label class="label" for="department">所属部门</label>
        <select id="department" v-model="form.department" class="input">
          <option>行政部</option>
          <option>人力资源部</option>
          <option>财务部</option>
          <option>信息技术部</option>
        </select>
      </div>
      <div class="field">
        <label class="label" for="reason">事由说明</label>
        <textarea id="reason" v-model="form.reason" class="textarea" placeholder="请详细描述申请事由…" />
      </div>
      <div class="actions">
        <button class="btn btn-ghost" type="button" @click="router.back()">取消</button>
        <button class="btn btn-primary" type="button" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中…' : '提交申请' }}
        </button>
      </div>
    </div>

    <Transition name="toast">
      <div v-if="toast" class="toast" role="status">{{ toast }}</div>
    </Transition>
  </div>
</template>

<style scoped>
.form-card {
  padding: 20px;
  max-width: 720px;
}

.field {
  margin-bottom: 14px;
}

.label {
  display: block;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.textarea {
  width: 100%;
  min-height: 100px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 8px 10px;
  font: inherit;
  resize: vertical;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 32px;
  transform: translateX(-50%);
  background: #111;
  color: #fff;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  z-index: 50;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
}
</style>
