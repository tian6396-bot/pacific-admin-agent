<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

const props = defineProps<{
  brand: string
  menus: { label: string; to: string }[]
}>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const roleLabel = computed(() => {
  const map: Record<UserRole, string> = {
    employee: '员工',
    agent: '坐席',
    admin: '管理员',
  }
  return auth.user ? `${map[auth.user.role]} ${auth.user.name}` : ''
})

function isActive(to: string) {
  return route.path === to || route.path.startsWith(to + '/')
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <div class="left">
      <div class="brand">
        <span class="logo" aria-hidden="true" />
        <span class="brand-text">{{ brand }}</span>
      </div>
      <nav>
        <RouterLink
          v-for="item in menus"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
    <div class="right">
      <slot name="meta" />
      <span class="user">{{ roleLabel }}</span>
      <button class="link" type="button" @click="logout">退出</button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: var(--header-h);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 20;
}

.left {
  display: flex;
  align-items: center;
  gap: 20px;
  min-width: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.logo {
  width: 24px;
  height: 24px;
  background: var(--color-primary);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}

.brand-text {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
}

nav {
  display: flex;
  align-items: center;
  gap: 2px;
  height: var(--header-h);
  overflow-x: auto;
}

.nav-item {
  height: 100%;
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  color: var(--color-text);
  font-size: 12px;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
}

.nav-item.active {
  color: var(--color-primary);
  font-weight: 600;
  border-bottom-color: var(--color-primary);
}

.right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.user {
  font-size: 13px;
  font-weight: 500;
}
</style>
