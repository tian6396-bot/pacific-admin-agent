import api from './api'

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

export interface NotificationItem {
  id: string
  title: string
  preview: string
  type: 'task' | 'system' | 'ticket' | 'material'
  read: boolean
  link?: string | null
  created_at: string
}

export interface PreferenceItem {
  language: string
  notify_task: boolean
  notify_ticket: boolean
  notify_system: boolean
  auto_handoff: boolean
  confidence_threshold: number
}

export async function listNotifications(): Promise<{ items: NotificationItem[]; unread: number }> {
  try {
    const { data } = await api.get<ApiEnvelope<{ items: NotificationItem[]; unread: number }>>(
      '/notifications',
    )
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || { items: [], unread: 0 }
  } catch (err) {
    throw unwrapError(err, '加载消息失败')
  }
}

export async function markAllNotificationsRead(): Promise<void> {
  try {
    const { data } = await api.post<ApiEnvelope<{ updated: number }>>('/notifications/read-all')
    if (!data.success) throw new Error(data.error || '操作失败')
  } catch (err) {
    throw unwrapError(err, '标记已读失败')
  }
}

export async function markNotificationRead(id: string): Promise<void> {
  try {
    await api.post(`/notifications/${id}/read`)
  } catch (err) {
    throw unwrapError(err, '标记已读失败')
  }
}

export async function getUnreadCount(): Promise<number> {
  try {
    const { data } = await api.get<ApiEnvelope<{ unread: number }>>('/notifications/unread-count')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data?.unread ?? 0
  } catch (err) {
    throw unwrapError(err, '加载未读数失败')
  }
}

export async function getPreferences(): Promise<PreferenceItem> {
  try {
    const { data } = await api.get<ApiEnvelope<PreferenceItem>>('/users/me/preferences')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载偏好失败')
  }
}

export async function savePreferences(body: Partial<PreferenceItem>): Promise<PreferenceItem> {
  try {
    const { data } = await api.put<ApiEnvelope<PreferenceItem>>('/users/me/preferences', body)
    if (!data.success) throw new Error(data.error || '保存失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '保存偏好失败')
  }
}

export async function getSlaBoard(): Promise<{
  kpi: { sla_ok_rate: number; overdue: number; avg_wait_minutes: number; waiting: number }
  queues: { queue: string; target: string; actual: string; rate: number; status: string }[]
  trend_labels: string[]
  trend_resolved: number[]
  shifts: {
    name: string
    time: string
    agents: number
    online: number
    sla: number
    demo?: boolean
  }[]
}> {
  try {
    const { data } = await api.get<ApiEnvelope<any>>('/agent/sla-board')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载 SLA 看板失败')
  }
}
