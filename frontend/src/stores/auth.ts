import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { LoginPayload, UserInfo } from '@/types/auth'
import { homePathByRole, login as loginApi } from '@/services/authService'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(
    localStorage.getItem('user') ? (JSON.parse(localStorage.getItem('user')!) as UserInfo) : null,
  )

  const isAuthenticated = computed(() => Boolean(token.value))
  const role = computed(() => user.value?.role)

  async function login(payload: LoginPayload) {
    const res = await loginApi(payload)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
    return homePathByRole(res.user.role)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, role, login, logout }
})
