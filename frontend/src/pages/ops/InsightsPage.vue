<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import MetricsPage from '@/pages/ops/MetricsPage.vue'
import BadCasesPage from '@/pages/ops/BadCasesPage.vue'

const tab = ref<'metrics' | 'badcase'>('metrics')
</script>

<template>
  <div class="insights">
    <PageHeader title="运营洞察" description="指标看板 + Bad Case 治理（合并页）" icon="◆" />

    <div class="tabs">
      <button type="button" class="tab" :class="{ active: tab === 'metrics' }" @click="tab = 'metrics'">
        指标
      </button>
      <button type="button" class="tab" :class="{ active: tab === 'badcase' }" @click="tab = 'badcase'">
        Bad Case
      </button>
    </div>

    <div class="panel">
      <MetricsPage v-if="tab === 'metrics'" embedded />
      <BadCasesPage v-else embedded />
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 12px;
}

.tab {
  border: none;
  background: none;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text-secondary);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.tab.active {
  color: var(--color-primary);
  font-weight: 600;
  border-bottom-color: var(--color-primary);
}
</style>
