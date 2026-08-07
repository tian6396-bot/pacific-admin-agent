<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'

const menus = [
  { label: '知识', to: '/ops/knowledge' },
  { label: '服务目录', to: '/ops/catalog' },
  { label: '意图·Prompt', to: '/ops/intents' },
  { label: 'Skill', to: '/ops/skills' },
  { label: '工具', to: '/ops/tools' },
  { label: '队列SLA', to: '/ops/queues' },
  { label: '运营洞察', to: '/ops/insights' },
  { label: '内容产出', to: '/ops/content' },
  { label: '权限审计', to: '/ops/security' },
]
</script>

<template>
  <div class="layout">
    <AppHeader brand="P-Assistant 运营" :menus="menus" />
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
