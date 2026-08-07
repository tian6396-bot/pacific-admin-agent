import api from './api'

export interface ServiceItem {
  id: string
  name: string
  domain: string
  domain_label: string
  priority: 'P0' | 'P1' | 'P2'
  description: string
  action: string
  can_apply: boolean
}

interface ApiEnvelope<T> {
  success: boolean
  data: T
  error?: string
}

function unwrapError(err: unknown, fallback: string): Error {
  const axiosErr = err as { response?: { data?: { detail?: string; error?: string } } }
  const detail = axiosErr.response?.data?.detail || axiosErr.response?.data?.error
  return new Error(typeof detail === 'string' ? detail : fallback)
}

export async function listServices(domain?: string): Promise<ServiceItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<ServiceItem[]>>('/services', {
      params: domain && domain !== 'all' ? { domain } : undefined,
    })
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载服务目录失败')
  }
}
