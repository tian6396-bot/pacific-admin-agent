<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <header class="page-header">
    <div class="icon-box" aria-hidden="true">{{ icon || '◆' }}</div>
    <div>
      <h1>
        {{ title }}
        <slot name="badge" />
      </h1>
      <p v-if="description">{{ description }}</p>
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.icon-box {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
}

p {
  margin: 2px 0 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
