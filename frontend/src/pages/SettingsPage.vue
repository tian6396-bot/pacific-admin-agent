<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { getPreferences, savePreferences, type PreferenceItem } from '@/services/notifyService'

const auth = useAuthStore()
const form = ref<PreferenceItem>({
  language: 'zh-CN',
  notify_task: true,
  notify_ticket: true,
  notify_system: false,
  auto_handoff: true,
  confidence_threshold: 0.7,
})
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const toast = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value = ''
  }, 2500)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    form.value = await getPreferences()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    form.value = await savePreferences({ ...form.value })
    showToast('偏好设置已保存')
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
    <PageHeader title="个人设置" description="账号资料与通知偏好" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="toast" class="ok">{{ toast }}</p>

    <div class="card form-card">
      <section class="section">
        <h3>账号</h3>
        <p class="profile">
          {{ auth.user?.name }}（{{ auth.user?.username }}）· {{ auth.user?.role }} ·
          {{ auth.user?.department || '—' }}
        </p>
      </section>

      <section class="section">
        <h3>通用</h3>
        <div class="field">
          <label class="label" for="language">界面语言</label>
          <select id="language" v-model="form.language" class="input" :disabled="loading">
            <option value="zh-CN">简体中文</option>
            <option value="en-US">English</option>
          </select>
        </div>
      </section>

      <section class="section">
        <h3>消息通知</h3>
        <label class="check">
          <input v-model="form.notify_task" type="checkbox" />
          任务提醒
        </label>
        <label class="check">
          <input v-model="form.notify_ticket" type="checkbox" />
          工单动态
        </label>
        <label class="check">
          <input v-model="form.notify_system" type="checkbox" />
          系统通知
        </label>
      </section>

      <section class="section">
        <h3>对话行为</h3>
        <label class="check">
          <input v-model="form.auto_handoff" type="checkbox" />
          低置信时建议转人工
        </label>
        <div class="field">
          <label class="label" for="conf">置信度阈值（展示用）</label>
          <input
            id="conf"
            v-model.number="form.confidence_threshold"
            type="number"
            step="0.05"
            min="0.1"
            max="1"
            class="input"
          />
        </div>
      </section>

      <button type="button" class="btn btn-primary" :disabled="saving || loading" @click="save">
        保存
      </button>
    </div>
  </div>
</template>

<style scoped>
.form-card {
  padding: 20px;
  max-width: 560px;
}
.section {
  margin-bottom: 20px;
}
.section h3 {
  margin: 0 0 10px;
  font-size: 14px;
}
.profile {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.check {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}
.field {
  margin-top: 10px;
}
.err {
  color: #cf1322;
}
.ok {
  color: #389e0d;
}
</style>
