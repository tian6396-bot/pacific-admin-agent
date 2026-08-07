<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import {
  createKnowledge,
  listKnowledge,
  offlineKnowledge,
  publishKnowledge,
  searchKnowledge,
  submitKnowledge,
  type KnowledgeItem,
  type KnowledgeStatus,
  type KnowledgeType,
  type SearchHit,
} from '@/services/knowledgeService'

const activeTab = ref<KnowledgeType>('faq')
const items = ref<KnowledgeItem[]>([])
const loading = ref(false)
const error = ref('')
const message = ref('')
const showCreate = ref(false)
const creating = ref(false)
const searchQ = ref('')
const searchHits = ref<SearchHit[]>([])

const form = ref({
  title: '',
  category: '行政制度',
  content: '',
  version: 'v1',
})

const statusMap: Record<KnowledgeStatus, { label: string; tag: string }> = {
  draft: { label: '草稿', tag: 'tag-muted' },
  review: { label: '审核中', tag: 'tag-primary' },
  published: { label: '已发布', tag: 'tag-success' },
  offline: { label: '已下线', tag: 'tag-danger' },
}

const filtered = computed(() => items.value.filter((i) => i.type === activeTab.value))

function fmtDate(value: string) {
  return value ? value.slice(0, 10) : '-'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listKnowledge()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    error.value = '请填写标题与正文'
    return
  }
  creating.value = true
  error.value = ''
  message.value = ''
  try {
    await createKnowledge({
      title: form.value.title.trim(),
      type: activeTab.value,
      category: form.value.category.trim() || '未分类',
      content: form.value.content.trim(),
      version: form.value.version || 'v1',
    })
    showCreate.value = false
    form.value = { title: '', category: '行政制度', content: '', version: 'v1' }
    message.value = '已创建为草稿'
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    creating.value = false
  }
}

async function onSubmit(item: KnowledgeItem) {
  error.value = ''
  message.value = ''
  try {
    await submitKnowledge(item.id)
    message.value = `已提交审核：${item.title}`
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '提交失败'
  }
}

async function onPublish(item: KnowledgeItem) {
  error.value = ''
  message.value = ''
  try {
    await publishKnowledge(item.id)
    message.value = `已发布：${item.title}`
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '发布失败'
  }
}

async function onOffline(item: KnowledgeItem) {
  error.value = ''
  message.value = ''
  try {
    await offlineKnowledge(item.id)
    message.value = `已下线：${item.title}`
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '下线失败'
  }
}

async function onSearch() {
  error.value = ''
  if (!searchQ.value.trim()) {
    searchHits.value = []
    return
  }
  try {
    searchHits.value = await searchKnowledge(searchQ.value.trim())
    if (!searchHits.value.length) message.value = '未召回结果（可能已下线或无匹配）'
  } catch (e) {
    error.value = e instanceof Error ? e.message : '检索失败'
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="知识管理" description="FAQ 与文档的审核、发布与下线" icon="◆" />

    <p v-if="error" class="banner err">{{ error }}</p>
    <p v-if="message" class="banner ok">{{ message }}</p>

    <div class="toolbar">
      <div class="tabs">
        <button type="button" class="tab" :class="{ active: activeTab === 'faq' }" @click="activeTab = 'faq'">
          FAQ
        </button>
        <button type="button" class="tab" :class="{ active: activeTab === 'doc' }" @click="activeTab = 'doc'">
          文档
        </button>
      </div>
      <div class="toolbar-right">
        <input v-model="searchQ" class="input search" placeholder="试检索已发布知识…" @keyup.enter="onSearch" />
        <button type="button" class="btn btn-ghost" @click="onSearch">检索</button>
        <button type="button" class="btn btn-primary" @click="showCreate = !showCreate">
          新建{{ activeTab === 'faq' ? ' FAQ' : '文档' }}
        </button>
      </div>
    </div>

    <div v-if="showCreate" class="card create-panel">
      <h3>新建{{ activeTab === 'faq' ? ' FAQ' : '文档' }}</h3>
      <div class="form-grid">
        <label>
          标题
          <input v-model="form.title" class="input" />
        </label>
        <label>
          分类
          <input v-model="form.category" class="input" />
        </label>
        <label>
          版本
          <input v-model="form.version" class="input" />
        </label>
      </div>
      <label class="block">
        正文
        <textarea v-model="form.content" class="input area" rows="4" placeholder="输入 FAQ 答案或文档正文…" />
      </label>
      <div class="form-actions">
        <button type="button" class="btn btn-ghost" @click="showCreate = false">取消</button>
        <button type="button" class="btn btn-primary" :disabled="creating" @click="onCreate">
          {{ creating ? '创建中…' : '保存为草稿' }}
        </button>
      </div>
    </div>

    <div v-if="searchHits.length" class="card search-panel">
      <h3>检索结果（{{ searchHits.length }}）</h3>
      <article v-for="hit in searchHits" :key="hit.chunk_id" class="hit">
        <div class="hit-head">
          <strong>{{ hit.title }}</strong>
          <span class="mono">score {{ hit.score }}</span>
        </div>
        <p>{{ hit.text }}</p>
      </article>
    </div>

    <div class="card table-wrap">
      <p v-if="loading" class="muted">加载中…</p>
      <table v-else class="table">
        <thead>
          <tr>
            <th>编号</th>
            <th>标题</th>
            <th>分类</th>
            <th>状态</th>
            <th>版本</th>
            <th>更新人</th>
            <th>更新时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td class="mono">{{ item.id.slice(0, 8) }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.category }}</td>
            <td>
              <span class="tag" :class="statusMap[item.status].tag">
                {{ statusMap[item.status].label }}
              </span>
            </td>
            <td>{{ item.version }}</td>
            <td>{{ item.author }}</td>
            <td>{{ fmtDate(item.updated_at) }}</td>
            <td class="ops">
              <RouterLink class="link" :to="`/ops/knowledge/${item.id}/parse`">查看解析</RouterLink>
              <button
                v-if="item.status === 'draft'"
                type="button"
                class="link"
                @click="onSubmit(item)"
              >
                提交审核
              </button>
              <button
                v-if="item.status === 'draft' || item.status === 'review'"
                type="button"
                class="link"
                @click="onPublish(item)"
              >
                发布
              </button>
              <button
                v-if="item.status === 'published'"
                type="button"
                class="link"
                @click="onOffline(item)"
              >
                下线
              </button>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="8" class="muted">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.banner {
  margin: 0 0 12px;
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

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.toolbar .tabs {
  border-bottom: none;
}

.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search {
  width: 220px;
}

.create-panel,
.search-panel {
  padding: 16px;
  margin-bottom: 16px;
}

.create-panel h3,
.search-panel h3 {
  margin: 0 0 12px;
  font-size: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.form-grid label,
.block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.area {
  resize: vertical;
  min-height: 96px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

.hit {
  border-top: 1px solid var(--color-border);
  padding: 10px 0;
  font-size: 13px;
}

.hit-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.table-wrap {
  overflow-x: auto;
}

.ops .link + .link {
  margin-left: 10px;
}

.muted {
  color: var(--color-text-secondary);
  padding: 12px;
}

button.link {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-primary, #1677ff);
  cursor: pointer;
  font-size: inherit;
}
</style>
