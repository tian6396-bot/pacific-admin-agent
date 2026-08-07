<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import {
  linkMaterialTask,
  listMaterials,
  retryMaterial,
  uploadMaterial,
  type MaterialItem,
  type MaterialStatus,
} from '@/services/materialService'
import { listTasks, type TaskItem } from '@/services/taskService'

const materials = ref<MaterialItem[]>([])
const tasks = ref<TaskItem[]>([])
const loading = ref(false)
const uploading = ref(false)
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const parseMap: Record<MaterialStatus, { label: string; tag: string }> = {
  pending: { label: '待解析', tag: 'tag-muted' },
  parsing: { label: '解析中', tag: 'tag-primary' },
  success: { label: '解析成功', tag: 'tag-success' },
  failed: { label: '解析失败', tag: 'tag-danger' },
}

function fmtTime(iso: string) {
  return iso ? iso.replace('T', ' ').slice(0, 16) : '—'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [mats, taskList] = await Promise.all([listMaterials(), listTasks('active')])
    materials.value = mats
    tasks.value = taskList
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  error.value = ''
  try {
    await uploadMaterial(file)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '上传失败'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function onRetry(id: string) {
  try {
    await retryMaterial(id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '重试失败'
  }
}

async function onLink(id: string, taskId: string) {
  try {
    await linkMaterialTask(id, taskId || null)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '关联失败'
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="材料中心" description="上传、简易解析状态与任务引用（非真 OCR）" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>

    <div class="toolbar">
      <button
        class="btn btn-primary"
        type="button"
        :disabled="uploading"
        @click="fileInput?.click()"
      >
        {{ uploading ? '上传中…' : '上传材料' }}
      </button>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept=".pdf,.jpg,.jpeg,.png,.webp"
        @change="onFileChange"
      />
      <button class="btn btn-ghost" type="button" :disabled="loading" @click="load">刷新</button>
    </div>

    <p v-if="loading" class="muted">加载中…</p>

    <div class="card table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>材料编号</th>
            <th>文件名</th>
            <th>类型</th>
            <th>大小</th>
            <th>解析状态</th>
            <th>关联任务</th>
            <th>上传时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="mat in materials" :key="mat.id">
            <td class="mono">{{ mat.id.slice(0, 8) }}</td>
            <td>{{ mat.filename }}</td>
            <td>{{ mat.file_kind }}</td>
            <td>{{ mat.size_label }}</td>
            <td>
              <span class="tag" :class="parseMap[mat.status].tag">
                {{ parseMap[mat.status].label }}
              </span>
              <span v-if="mat.error" class="err-inline">{{ mat.error }}</span>
            </td>
            <td>
              <select
                class="input select"
                :value="mat.task_id || ''"
                @change="onLink(mat.id, ($event.target as HTMLSelectElement).value)"
              >
                <option value="">未关联</option>
                <option v-for="t in tasks" :key="t.id" :value="t.id">
                  {{ t.id.slice(0, 8) }} · {{ t.title }}
                </option>
              </select>
              <RouterLink
                v-if="mat.task_id"
                :to="`/tasks/${mat.task_id}`"
                class="link mono"
              >
                查看
              </RouterLink>
            </td>
            <td>{{ fmtTime(mat.created_at) }}</td>
            <td>
              <button
                v-if="mat.status === 'failed' || mat.status === 'success'"
                type="button"
                class="link"
                @click="onRetry(mat.id)"
              >
                重试解析
              </button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
          <tr v-if="!loading && !materials.length">
            <td colspan="8" class="muted">暂无材料，请上传 PDF 或图片</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.hidden {
  display: none;
}
.table-wrap {
  overflow-x: auto;
}
.muted {
  color: var(--color-text-secondary);
  text-align: center;
  padding: 12px;
}
.err {
  color: #cf1322;
  font-size: 13px;
}
.err-inline {
  display: block;
  font-size: 11px;
  color: #cf1322;
  margin-top: 4px;
}
.select {
  max-width: 180px;
  font-size: 12px;
  padding: 4px 8px;
  display: block;
  margin-bottom: 4px;
}
</style>
