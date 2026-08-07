<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getKnowledge,
  reindexKnowledge,
  submitKnowledge,
  updateChunk,
  type KnowledgeDetail,
} from '@/services/knowledgeService'

const route = useRoute()
const router = useRouter()
const docId = computed(() => (route.params.id as string) || '')

const detail = ref<KnowledgeDetail | null>(null)
const loading = ref(false)
const error = ref('')
const message = ref('')
const draftTexts = ref<Record<string, string>>({})
const savingId = ref('')

const lowCount = computed(() => detail.value?.low_confidence_count || 0)

const fields = computed(() => {
  const d = detail.value
  if (!d) return []
  return [
    { label: '标题', value: d.title },
    { label: '业务域', value: d.category },
    { label: '生效日', value: d.effective_from || '-' },
    { label: '权限标签', value: d.permission_tags || '全员可读' },
    { label: '版本', value: `${d.version}（${statusLabel(d.status)}）` },
  ]
})

function statusLabel(status: string) {
  const map: Record<string, string> = {
    draft: '草稿',
    review: '审核中',
    published: '已发布',
    offline: '已下线',
  }
  return map[status] || status
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    detail.value = await getKnowledge(docId.value)
    draftTexts.value = {}
    for (const c of detail.value.chunks) {
      if (c.needs_review) draftTexts.value[c.id] = c.text
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function saveChunk(chunkId: string) {
  const text = (draftTexts.value[chunkId] || '').trim()
  if (!text) {
    error.value = '校正文本不能为空'
    return
  }
  savingId.value = chunkId
  error.value = ''
  message.value = ''
  try {
    await updateChunk(docId.value, chunkId, text)
    message.value = 'Chunk 已校对'
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '校对失败'
  } finally {
    savingId.value = ''
  }
}

async function onReindex() {
  error.value = ''
  message.value = ''
  try {
    detail.value = await reindexKnowledge(docId.value)
    message.value = '已重建 Chunk'
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '重建失败'
  }
}

async function onSubmit() {
  error.value = ''
  message.value = ''
  try {
    detail.value = await submitKnowledge(docId.value)
    message.value = '已提交审核'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  }
}

onMounted(load)
</script>

<template>
  <div class="parse-page">
    <header class="head">
      <div>
        <h1>知识解析详情</h1>
        <p>
          {{ detail?.source_filename || detail?.title || '加载中' }} · {{ docId.slice(0, 8) }} ·
          {{ detail ? statusLabel(detail.status) : '…' }}
        </p>
      </div>
      <button class="btn btn-ghost" type="button" @click="router.push('/ops/knowledge')">返回列表</button>
    </header>

    <p v-if="error" class="banner err">{{ error }}</p>
    <p v-if="message" class="banner ok">{{ message }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-if="detail" class="cols">
      <section class="card col">
        <div class="col-head">
          <strong>原文预览</strong>
          <span>{{ detail.chunk_count }} 个片段</span>
        </div>
        <div class="preview">
          <p class="muted">{{ detail.source_filename || '文本知识' }}</p>
          <h3>{{ detail.title }}</h3>
          <p class="body">{{ detail.content }}</p>
        </div>
      </section>

      <section class="card col">
        <strong>元数据</strong>
        <div v-for="f in fields" :key="f.label" class="field">
          <label>{{ f.label }}</label>
          <input class="input" :value="f.value" readonly />
        </div>
      </section>

      <section class="card col">
        <div class="col-head">
          <strong>Chunk 列表</strong>
          <span v-if="lowCount" class="warn">低置信 {{ lowCount }} 条</span>
          <span v-else class="ok">无需校对</span>
        </div>
        <article
          v-for="c in detail.chunks"
          :key="c.id"
          class="chunk"
          :class="{ warn: c.needs_review }"
        >
          <div class="chunk-head">
            <span>Chunk #{{ c.index }}</span>
            <span :class="c.needs_review ? 'warn' : 'ok'">
              置信 {{ c.confidence.toFixed(2) }}{{ c.needs_review ? ' · 需校对' : '' }}
            </span>
          </div>
          <p>{{ c.text }}</p>
          <template v-if="c.needs_review && detail.status !== 'published'">
            <input v-model="draftTexts[c.id]" class="input" placeholder="点击校正文本…" />
            <button
              class="btn btn-primary btn-sm"
              type="button"
              :disabled="savingId === c.id"
              @click="saveChunk(c.id)"
            >
              {{ savingId === c.id ? '保存中…' : '保存校对' }}
            </button>
          </template>
        </article>
      </section>
    </div>

    <footer v-if="detail" class="foot card">
      <span>
        effective_from = {{ detail.effective_from || '-' }} ·
        {{ detail.status === 'published' ? '已进索引' : '重建索引后可提交审核' }}
      </span>
      <div class="foot-actions">
        <button
          class="btn btn-ghost"
          type="button"
          :disabled="detail.status === 'published'"
          @click="onReindex"
        >
          重建索引
        </button>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="detail.status !== 'draft'"
          @click="onSubmit"
        >
          提交审核
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.parse-page {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: calc(100vh - var(--header-h));
  min-height: 0;
}

.banner {
  margin: 0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}
.banner.err {
  background: #fff1f0;
  color: #cf1322;
}
.banner.ok {
  background: #f6ffed;
  color: #389e0d;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.head h1 {
  margin: 0 0 4px;
  font-size: 18px;
}

.head p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.cols {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.col {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  overflow: auto;
}

.col-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.preview {
  flex: 1;
  background: var(--color-bg);
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.6;
}

.preview h3 {
  margin: 8px 0;
  font-size: 14px;
}

.body {
  white-space: pre-wrap;
  word-break: break-word;
}

.muted {
  color: var(--color-text-secondary);
}

.field label {
  display: block;
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.field {
  margin-bottom: 4px;
}

.chunk {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 10px;
  background: var(--color-bg);
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chunk.warn {
  border-color: var(--color-warning);
  background: #fff7e6;
}

.chunk-head {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
}

.warn {
  color: var(--color-warning);
}

.ok {
  color: var(--color-success);
}

.foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.foot-actions {
  display: flex;
  gap: 8px;
}

.btn-ghost {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.btn-sm {
  height: 28px;
  align-self: flex-start;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .cols {
    grid-template-columns: 1fr;
  }
}
</style>
