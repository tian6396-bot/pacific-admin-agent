<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { getSkillDetail, listSkills, type FlowNode, type SkillItem } from '@/services/skillService'

const skills = ref<SkillItem[]>([])
const selectedId = ref('')
const nodes = ref<FlowNode[]>([])
const loading = ref(false)
const error = ref('')

const nodeTypeMap: Record<string, { label: string; color: string }> = {
  collect: { label: '收集', color: '#1677FF' },
  confirm: { label: '确认', color: '#722ed1' },
  invoke: { label: '调用', color: '#52c41a' },
  compensate: { label: '补偿', color: '#fa8c16' },
}

const active = () => skills.value.find((s) => s.id === selectedId.value)

async function loadList() {
  loading.value = true
  error.value = ''
  try {
    skills.value = await listSkills()
    if (!selectedId.value && skills.value.length) {
      selectedId.value = skills.value[0].id
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadDetail(id: string) {
  if (!id) return
  try {
    const detail = await getSkillDetail(id)
    nodes.value = detail.nodes
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载详情失败'
  }
}

watch(selectedId, (id) => loadDetail(id))
onMounted(loadList)
</script>

<template>
  <div class="page">
    <PageHeader title="Skill 管理" description="13 Skills · 补槽→校验→确认→调用→补偿" icon="◆" />
    <p v-if="error" class="err">{{ error }}</p>

    <div class="split-layout">
      <aside class="card list-panel">
        <div class="panel-head">流程列表</div>
        <p v-if="loading" class="muted">加载中…</p>
        <div
          v-for="wf in skills"
          :key="wf.id"
          class="list-item"
          :class="{ active: selectedId === wf.id }"
          @click="selectedId = wf.id"
        >
          <div class="item-name">{{ wf.name }}</div>
          <div class="item-meta">
            <span class="mono item-id">{{ wf.id }}</span>
            <span class="tag" :class="wf.status === 'published' ? 'tag-success' : 'tag-muted'">
              {{ wf.status === 'published' ? '已发布' : '草稿' }}
            </span>
          </div>
        </div>
      </aside>

      <section class="card flow-panel">
        <div class="panel-head">
          <span>{{ active()?.name || '请选择' }} · 节点编排</span>
          <span class="hint">{{ active()?.priority }} · {{ active()?.domain }}</span>
        </div>
        <div class="flow">
          <div v-for="(n, idx) in nodes" :key="n.id" class="node">
            <div class="node-badge" :style="{ background: nodeTypeMap[n.type]?.color || '#999' }">
              {{ nodeTypeMap[n.type]?.label || n.type }}
            </div>
            <div>
              <strong>{{ n.label }}</strong>
              <p>{{ n.config }}</p>
            </div>
            <div v-if="idx < nodes.length - 1" class="arrow">↓</div>
          </div>
          <p v-if="!nodes.length" class="muted">暂无节点</p>
        </div>
        <p class="foot">
          Intent：{{ active()?.intent }} · 工具：{{ active()?.tool_id || '—' }} ·
          可运行 P0 在对话确认后走 Mock 工具
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.err {
  color: #cf1322;
}
.split-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 12px;
  min-height: 480px;
}
.list-panel,
.flow-panel {
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.panel-head {
  padding: 12px 14px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
}
.list-item {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
}
.list-item.active {
  background: var(--color-primary-soft);
}
.item-name {
  font-size: 13px;
  font-weight: 600;
}
.item-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 4px;
}
.item-id {
  font-size: 11px;
  color: var(--color-text-secondary);
}
.flow {
  padding: 16px;
  flex: 1;
  overflow: auto;
}
.node {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 10px;
  margin-bottom: 8px;
  position: relative;
}
.node-badge {
  color: #fff;
  font-size: 11px;
  border-radius: 6px;
  height: 28px;
  display: grid;
  place-items: center;
}
.node p {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.arrow {
  grid-column: 1 / -1;
  text-align: center;
  color: var(--color-text-secondary);
  margin: 2px 0 8px;
}
.foot,
.hint,
.muted {
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 10px 14px;
}
@media (max-width: 900px) {
  .split-layout {
    grid-template-columns: 1fr;
  }
}
</style>
