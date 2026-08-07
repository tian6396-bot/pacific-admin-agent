<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { demoAccounts } from '@/services/authService'

const router = useRouter()
const auth = useAuthStore()
const username = ref('emp')
const password = ref('123456')
const loading = ref(false)
const error = ref('')
const demos = demoAccounts()

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const path = await auth.login({ username: username.value, password: password.value })
    await router.push(path)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}

function fill(u: string, p: string) {
  username.value = u
  password.value = p
}
</script>

<template>
  <div class="login-page">
    <div class="card login-card">
      <div class="brand">
        <span class="logo" />
        <h1>太平洋金科</h1>
        <p>智能行政咨询助手</p>
      </div>
      <form @submit.prevent="submit">
        <div class="field">
          <label class="label" for="username">账号</label>
          <input id="username" v-model="username" class="input" autocomplete="username" />
        </div>
        <div class="field">
          <label class="label" for="password">密码</label>
          <input
            id="password"
            v-model="password"
            class="input"
            type="password"
            autocomplete="current-password"
          />
        </div>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button class="btn btn-primary submit" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>
      <div class="demo">
        <div class="demo-title">演示账号</div>
        <button
          v-for="d in demos"
          :key="d.username"
          type="button"
          class="demo-item"
          @click="fill(d.username, d.password)"
        >
          {{ d.roleLabel }}：{{ d.username }} / {{ d.password }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at 20% 20%, #e6f4ff 0%, transparent 40%),
    radial-gradient(circle at 80% 0%, #f0f5ff 0%, transparent 35%),
    var(--color-bg);
}

.login-card {
  width: 420px;
  padding: 40px;
  box-shadow: 0 4px 16px #00000014;
}

.brand {
  text-align: center;
  margin-bottom: 28px;
}

.logo {
  display: inline-block;
  width: 40px;
  height: 40px;
  background: var(--color-primary);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  margin-bottom: 12px;
}

h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 24px;
}

.brand p {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.submit {
  width: 100%;
  height: 40px;
  margin-top: 8px;
}

.error {
  color: var(--color-danger);
  font-size: 13px;
  margin: 0 0 8px;
}

.demo {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.demo-title {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.demo-item {
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 6px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  cursor: pointer;
  font-size: 12px;
  color: var(--color-text);
}

.demo-item:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
</style>
