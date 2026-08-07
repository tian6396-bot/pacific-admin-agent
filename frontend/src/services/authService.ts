import type { LoginPayload, UserInfo, UserRole } from '@/types/auth'
import api from './api'

const DEMO_USERS: Record<string, { password: string; user: UserInfo }> = {
  emp: {
    password: '123456',
    user: {
      id: 'u-emp',
      name: '张敏',
      username: 'emp',
      role: 'employee',
      department: '行政部',
    },
  },
  agent: {
    password: '123456',
    user: {
      id: 'u-agent',
      name: '王敏',
      username: 'agent',
      role: 'agent',
      department: '财务组',
    },
  },
  admin: {
    password: '123456',
    user: {
      id: 'u-admin',
      name: '陈浩',
      username: 'admin',
      role: 'admin',
      department: '运营中心',
    },
  },
}

const useMock = import.meta.env.VITE_USE_MOCK !== 'false'

interface ApiEnvelope<T> {
  success: boolean
  data: T
  message?: string
  error?: string
}

export async function login(payload: LoginPayload): Promise<{ token: string; user: UserInfo }> {
  if (useMock) {
    await new Promise((r) => setTimeout(r, 300))
    const found = DEMO_USERS[payload.username]
    if (!found || found.password !== payload.password) {
      throw new Error('账号或密码错误')
    }
    return { token: `mock-jwt-${found.user.role}`, user: found.user }
  }

  try {
    const { data: envelope } = await api.post<ApiEnvelope<{ token: string; user: UserInfo }>>(
      '/auth/login',
      payload,
    )
    if (!envelope?.success || !envelope.data?.token) {
      throw new Error(envelope?.error || '登录失败')
    }
    return envelope.data
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string; error?: string } } }
    const detail = axiosErr.response?.data?.detail || axiosErr.response?.data?.error
    throw new Error(typeof detail === 'string' ? detail : '账号或密码错误')
  }
}

export function homePathByRole(role: UserRole): string {
  if (role === 'agent') return '/agent/queue'
  if (role === 'admin') return '/ops/knowledge'
  return '/workbench'
}

export function demoAccounts() {
  return [
    { username: 'emp', password: '123456', roleLabel: '员工' },
    { username: 'agent', password: '123456', roleLabel: '坐席' },
    { username: 'admin', password: '123456', roleLabel: '管理员' },
  ]
}
