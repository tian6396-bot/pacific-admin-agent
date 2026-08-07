<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import {
  datasetLabel,
  downloadArtifact,
  downloadArtifactPptx,
  exportContentData,
  generateReport,
  getContentCapabilities,
  listContentArtifacts,
  rewriteContent,
  type ContentArtifact,
  type ContentCapabilities,
  type ExportDataset,
} from '@/services/contentService'

const auth = useAuthStore()
const caps = ref<ContentCapabilities | null>(null)
const artifacts = ref<ContentArtifact[]>([])
const active = ref<ContentArtifact | null>(null)
const error = ref('')
const busy = ref(false)

const rewriteText = ref('')
const rewriteTone = ref<'formal' | 'concise' | 'friendly'>('formal')
const rewriteTitle = ref('文档改写')

const reportTopic = ref('')
const reportPoints = ref('')
const reportTitle = ref('行政报告草稿')

const exportDataset = ref<ExportDataset | ''>('')
const exportTitle = ref('数据导出')

const roleHint = computed(() => {
  const r = auth.user?.role
  if (r === 'agent') return '坐席：可改写回复/交接摘要，导出本人经办与回访'
  if (r === 'admin') return '运营：可润色知识稿、出治理报告，导出知识/Bad Case/审计'
  return '员工：可改写本人文稿、出个人小结，仅导出本人任务/工单'
})

async function refresh() {
  error.value = ''
  try {
    const [c, list] = await Promise.all([getContentCapabilities(), listContentArtifacts()])
    caps.value = c
    artifacts.value = list
    if (c.export_datasets.length && !exportDataset.value) {
      exportDataset.value = c.export_datasets[0]
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  }
}

function showResult(item: ContentArtifact) {
  active.value = item
  artifacts.value = [item, ...artifacts.value.filter((x) => x.id !== item.id)]
}

async function onRewrite() {
  if (!rewriteText.value.trim() || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const item = await rewriteContent({
      text: rewriteText.value,
      tone: rewriteTone.value,
      title: rewriteTitle.value || '文档改写',
    })
    showResult(item)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '改写失败'
  } finally {
    busy.value = false
  }
}

async function onReport() {
  if (!reportTopic.value.trim() || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const item = await generateReport({
      topic: reportTopic.value,
      points: reportPoints.value,
      title: reportTitle.value || '报告草稿',
    })
    showResult(item)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '生成失败'
  } finally {
    busy.value = false
  }
}

async function onExport() {
  if (!exportDataset.value || busy.value) return
  busy.value = true
  error.value = ''
  try {
    const item = await exportContentData({
      dataset: exportDataset.value,
      title: exportTitle.value || datasetLabel[exportDataset.value],
    })
    showResult(item)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '导出失败'
  } finally {
    busy.value = false
  }
}

async function onDownloadPptx() {
  if (!active.value?.has_pptx) return
  try {
    await downloadArtifactPptx(active.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '下载 PPTX 失败'
  }
}

onMounted(refresh)
</script>

<template>
  <div class="page">
    <PageHeader
      title="内容产出"
      description="改写文档 · 报告草稿 · 权限内数据导出（按角色授权，并非全都有）"
      icon="✎"
    />

    <p class="hint">{{ roleHint }}</p>
    <p v-if="error" class="err">{{ error }}</p>

    <div class="grid">
      <section v-if="caps?.can_rewrite" class="card panel">
        <h3>文档改写</h3>
        <label class="label">标题</label>
        <input v-model="rewriteTitle" class="input" />
        <label class="label">语气</label>
        <select v-model="rewriteTone" class="input">
          <option value="formal">正式规范</option>
          <option value="concise">简洁干练</option>
          <option value="friendly">友好清晰</option>
        </select>
        <label class="label">原文</label>
        <textarea v-model="rewriteText" class="input area" rows="8" placeholder="粘贴待改写文稿…" />
        <button class="btn btn-primary" type="button" :disabled="busy" @click="onRewrite">
          开始改写
        </button>
      </section>

      <section v-if="caps?.can_report" class="card panel">
        <h3>报告草稿</h3>
        <label class="label">报告标题</label>
        <input v-model="reportTitle" class="input" />
        <label class="label">主题</label>
        <input v-model="reportTopic" class="input" placeholder="如：本周行政咨询小结" />
        <label class="label">补充要点</label>
        <textarea v-model="reportPoints" class="input area" rows="6" placeholder="可选要点，一行一条" />
        <button class="btn btn-primary" type="button" :disabled="busy" @click="onReport">
          生成报告
        </button>
      </section>

      <section v-if="caps?.export_datasets?.length" class="card panel">
        <h3>数据导出</h3>
        <label class="label">导出标题</label>
        <input v-model="exportTitle" class="input" />
        <label class="label">数据集（仅显示你有权的）</label>
        <select v-model="exportDataset" class="input">
          <option v-for="d in caps.export_datasets" :key="d" :value="d">
            {{ datasetLabel[d] }}
          </option>
        </select>
        <button class="btn btn-primary" type="button" :disabled="busy" @click="onExport">
          导出 CSV
        </button>
      </section>
    </div>

    <ul v-if="caps?.notes?.length" class="notes">
      <li v-for="(n, i) in caps.notes" :key="i">{{ n }}</li>
    </ul>

    <div class="result-wrap">
      <aside class="card list">
        <div class="list-head">
          <strong>我的产出</strong>
          <button class="btn btn-ghost btn-sm" type="button" @click="refresh">刷新</button>
        </div>
        <button
          v-for="a in artifacts"
          :key="a.id"
          type="button"
          class="item"
          :class="{ active: a.id === active?.id }"
          @click="active = a"
        >
          <span class="kind">{{ a.kind }}</span>
          <span class="t">{{ a.title }}</span>
        </button>
        <p v-if="!artifacts.length" class="muted">暂无产出</p>
      </aside>

      <section class="card preview">
        <template v-if="active">
          <div class="preview-head">
            <div>
              <h3>{{ active.title }}</h3>
              <p class="muted">{{ active.summary }}</p>
            </div>
            <div class="preview-actions">
              <button class="btn btn-ghost btn-sm" type="button" @click="downloadArtifact(active!)">
                下载 {{ active.kind === 'export' ? 'CSV' : 'MD' }}
              </button>
              <button
                v-if="active.has_pptx"
                class="btn btn-primary btn-sm"
                type="button"
                @click="onDownloadPptx"
              >
                下载 PPTX
              </button>
            </div>
          </div>
          <pre class="body">{{ active.body }}</pre>
        </template>
        <p v-else class="muted">生成或选择左侧产出查看</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 10px;
}
.err {
  color: #cf1322;
  margin-bottom: 8px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.panel h3 {
  margin: 0 0 10px;
  font-size: 15px;
}
.label {
  display: block;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 8px 0 4px;
}
.area {
  resize: vertical;
  min-height: 100px;
}
.panel .btn {
  margin-top: 12px;
}
.notes {
  margin: 0 0 14px;
  padding-left: 18px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
.result-wrap {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 12px;
  min-height: 320px;
}
.list-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.item {
  width: 100%;
  text-align: left;
  border: none;
  background: var(--color-bg);
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.item.active {
  background: var(--color-primary-soft);
}
.kind {
  font-size: 11px;
  color: var(--color-primary);
  text-transform: uppercase;
}
.t {
  font-size: 13px;
}
.preview-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.preview-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.preview-head h3 {
  margin: 0 0 4px;
}
.body {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.55;
  background: var(--color-bg);
  padding: 12px;
  border-radius: 8px;
  max-height: 480px;
  overflow: auto;
}
.muted {
  color: var(--color-text-secondary);
  font-size: 13px;
}
@media (max-width: 900px) {
  .result-wrap {
    grid-template-columns: 1fr;
  }
}
</style>
