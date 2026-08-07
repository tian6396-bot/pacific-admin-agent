<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import { listServices, type ServiceItem } from '@/services/catalogService'

const services = ref<ServiceItem[]>([])
const selectedId = ref('')
const loading = ref(false)
const error = ref('')

const activeService = computed(() => services.value.find((s) => s.id === selectedId.value))

async function load() {
  loading.value = true
  error.value = ''
  try {
    services.value = await listServices()
    if (!selectedId.value && services.value.length) {
      selectedId.value = services.value[0].id
    }
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
    <PageHeader title="服务目录与表单配置" description="事项目录只读（发布配置沿用 B4 种子）" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="split-layout">
      <aside class="card list-panel">
        <div class="panel-head">服务事项</div>
        <div
          v-for="svc in services"
          :key="svc.id"
          class="list-item"
          :class="{ active: selectedId === svc.id }"
          @click="selectedId = svc.id"
        >
          <div class="item-name">{{ svc.name }}</div>
          <div class="item-meta">
            <span class="tag tag-muted">{{ svc.domain_label || svc.domain }}</span>
            <span class="tag" :class="svc.can_apply ? 'tag-success' : 'tag-muted'">
              {{ svc.can_apply ? '可申请' : '只读' }}
            </span>
          </div>
        </div>
      </aside>

      <section class="card config-panel">
        <div class="panel-head">
          <span>{{ activeService?.name || '—' }} · 详情</span>
        </div>
        <div v-if="activeService" class="detail">
          <p><strong>ID</strong> <span class="mono">{{ activeService.id }}</span></p>
          <p><strong>领域</strong> {{ activeService.domain_label }}（{{ activeService.domain }}）</p>
          <p><strong>优先级</strong> {{ activeService.priority }}</p>
          <p><strong>动作</strong> {{ activeService.action }}</p>
          <p><strong>说明</strong> {{ activeService.description || '—' }}</p>
          <p class="note">表单字段编辑为后续增强；当前申请表单由员工端按服务类型渲染。</p>
        </div>
      </section>
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
.split-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
  min-height: 480px;
}
.panel-head {
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
}
.list-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border);
}
.list-item:hover {
  background: var(--color-bg);
}
.list-item.active {
  background: var(--color-primary-soft);
}
.item-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
}
.item-meta {
  display: flex;
  gap: 6px;
}
.detail {
  padding: 20px;
  font-size: 13px;
  line-height: 1.7;
}
.note {
  margin-top: 16px;
  color: var(--color-text-secondary);
}
@media (max-width: 900px) {
  .split-layout {
    grid-template-columns: 1fr;
  }
}
</style>
