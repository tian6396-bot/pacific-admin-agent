<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'

const menus = [
  { label: '队列看板', to: '/agent/queue' },
  { label: '会话工作台', to: '/agent/sessions' },
  { label: '待审批', to: '/agent/tasks?tab=approve' },
  { label: 'SLA', to: '/agent/sla' },
  { label: '质检回访', to: '/agent/qa' },
]
</script>

<template>
  <div class="layout">
    <AppHeader brand="P-Assistant 坐席" :menus="menus" />
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  min-height: 0;
}
</style>
