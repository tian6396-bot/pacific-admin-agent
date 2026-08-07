import axios from 'axios'

/** 解析 API 根地址；相对路径时拼当前页面 origin（便于局域网分享）。 */
export function resolveApiBase(): string {
  const raw = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api'
  if (/^https?:\/\//i.test(raw)) return raw.replace(/\/$/, '')
  const origin =
    typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173'
  const path = raw.startsWith('/') ? raw : `/${raw}`
  return `${origin}${path}`.replace(/\/$/, '')
}

export function resolveWsBase(): string {
  return resolveApiBase().replace(/^http/i, 'ws')
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = String(error.config?.url || '')
    const isLogin = url.includes('/auth/login')
    if (error.response?.status === 401 && !isLogin) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api
