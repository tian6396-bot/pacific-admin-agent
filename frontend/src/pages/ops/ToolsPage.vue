<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { listTools, type ToolItem } from '@/services/skillService'

const tools = ref<ToolItem[]>([])
const selectedId = ref('')
const loading = ref(false)
const error = ref('')

const active = computed(() => tools.value.find((t) => t.id === selectedId.value))

async function load() {
  loading.value = true
  error.value = ''
  try {
    tools.value = await listTools()
    if (tools.value.length) selectedId.value = tools.value[0].id
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="工具与模型管理" description="工具注册、Schema 定义与 Mock 响应" icon="◆" />
    <p v-if="error" class="err">{{ error }}</p>

    <div class="layout">
      <aside class="card list">
        <div class="head">工具列表</div>
        <p v-if="loading" class="muted">加载中…</p>
        <button
          v-for="t in tools"
          :key="t.id"
          type="button"
          class="item"
          :class="{ active: t.id === selectedId }"
          @click="selectedId = t.id"
        >
          <div class="name">{{ t.name }}</div>
          <div class="meta">
            <span class="mono">{{ t.id }}</span>
            <span class="tag" :class="t.mock_enabled ? 'tag-warning' : 'tag-muted'">
              {{ t.mock_enabled ? 'Mock' : 'Live' }}
            </span>
          </div>
        </button>
      </aside>

      <section class="card detail" v-if="active">
        <div class="head">{{ active.name }}</div>
        <dl>
          <dt>Endpoint</dt>
          <dd class="mono">{{ active.method }} {{ active.endpoint }}</dd>
          <dt>超时 / 重试</dt>
          <dd>{{ active.timeout_ms }} ms / {{ active.retries }}</dd>
          <dt>状态</dt>
          <dd>{{ active.status }}</dd>
        </dl>
        <h4>Schema</h4>
        <pre>{{ active.schema_json }}</pre>
        <h4>Mock 响应</h4>
        <pre>{{ active.mock_response }}</pre>
      </section>
    </div>
  </div>
</template>

<style scoped>
.err {
  color: #cf1322;
}
.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
}
.list,
.detail {
  padding: 0;
  min-height: 420px;
}
.head {
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
}
.item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
}
.item.active {
  background: var(--color-primary-soft);
}
.name {
  font-size: 13px;
  font-weight: 600;
}
.meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
}
.detail {
  padding-bottom: 16px;
}
dl {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 8px;
  padding: 14px;
  margin: 0;
  font-size: 13px;
}
dt {
  color: var(--color-text-secondary);
}
dd {
  margin: 0;
}
h4 {
  margin: 0 14px 6px;
  font-size: 13px;
}
pre {
  margin: 0 14px 14px;
  padding: 10px;
  background: var(--color-bg);
  border-radius: 6px;
  font-size: 12px;
  overflow: auto;
}
.muted {
  padding: 12px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
