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

export type ConfigStatus = 'draft' | 'published' | 'offline'
export type BadCaseStatus = 'open' | 'improved' | 'ignored'

export interface IntentItem {
  id: string
  name: string
  domain: string
  slots: string
  status: ConfigStatus
  prompt_version: string
  prompt_content: string
  hit_rate: number
}

export interface QueueSlaItem {
  id: string
  name: string
  skill_group: string
  agents: number
  sla_minutes: number
  priority: number
  max_wait: number
  alert_threshold: number
  status: 'active' | 'disabled'
}

export interface BadCaseItem {
  id: string
  title: string
  category: string
  domain: string
  intent: string
  severity: 'high' | 'medium' | 'low'
  status: BadCaseStatus
  description: string
  root_cause: string
  suggestion: string
  session_id?: string | null
  created_at: string
  updated_at: string
}

export interface AuditLogItem {
  id: string
  operator: string
  role: string
  action: string
  target: string
  ip: string
  result: 'success' | 'denied'
  created_at: string
}

export interface MetricsSummary {
  sessions_today: number
  ai_resolve_rate: number
  handoff_rate: number
  avg_satisfaction: number
  knowledge_published: number
  tasks_open: number
  tickets_waiting: number
  badcases_open: number
  trend_sessions: number[]
  trend_labels: string[]
}

export interface RbacMatrix {
  roles: string[]
  permissions: { key: string; label: string }[]
  matrix: Record<string, Record<string, boolean>>
}

export async function listIntents(): Promise<IntentItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<IntentItem[]>>('/ops/intents')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载意图失败')
  }
}

export async function updateIntent(
  id: string,
  body: Partial<Pick<IntentItem, 'prompt_content' | 'name' | 'slots' | 'domain' | 'prompt_version'>>,
): Promise<IntentItem> {
  try {
    const { data } = await api.patch<ApiEnvelope<IntentItem>>(`/ops/intents/${id}`, body)
    if (!data.success) throw new Error(data.error || '更新失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '更新意图失败')
  }
}

export async function publishIntent(id: string): Promise<IntentItem> {
  try {
    const { data } = await api.post<ApiEnvelope<IntentItem>>(`/ops/intents/${id}/publish`)
    if (!data.success) throw new Error(data.error || '发布失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '发布意图失败')
  }
}

export async function offlineIntent(id: string): Promise<IntentItem> {
  try {
    const { data } = await api.post<ApiEnvelope<IntentItem>>(`/ops/intents/${id}/offline`)
    if (!data.success) throw new Error(data.error || '下线失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '下线意图失败')
  }
}

export async function listQueues(): Promise<QueueSlaItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<QueueSlaItem[]>>('/ops/queues')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载队列失败')
  }
}

export async function updateQueue(
  id: string,
  body: Partial<
    Pick<
      QueueSlaItem,
      | 'name'
      | 'skill_group'
      | 'agents'
      | 'sla_minutes'
      | 'priority'
      | 'max_wait'
      | 'alert_threshold'
      | 'status'
    >
  >,
): Promise<QueueSlaItem> {
  try {
    const { data } = await api.patch<ApiEnvelope<QueueSlaItem>>(`/ops/queues/${id}`, body)
    if (!data.success) throw new Error(data.error || '保存失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '保存 SLA 失败')
  }
}

export async function listBadCases(domain?: string): Promise<BadCaseItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<BadCaseItem[]>>('/ops/badcases', {
      params: domain && domain !== '全部' ? { domain } : undefined,
    })
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载 Bad Case 失败')
  }
}

export async function updateBadCase(
  id: string,
  body: Partial<Pick<BadCaseItem, 'status' | 'root_cause' | 'suggestion'>>,
): Promise<BadCaseItem> {
  try {
    const { data } = await api.patch<ApiEnvelope<BadCaseItem>>(`/ops/badcases/${id}`, body)
    if (!data.success) throw new Error(data.error || '更新失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '更新 Bad Case 失败')
  }
}

export async function getMetrics(): Promise<MetricsSummary> {
  try {
    const { data } = await api.get<ApiEnvelope<MetricsSummary>>('/ops/metrics')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载指标失败')
  }
}

export async function listAudits(params?: {
  operator?: string
  action?: string
}): Promise<AuditLogItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<AuditLogItem[]>>('/ops/audits', { params })
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载审计日志失败')
  }
}

export async function getRbac(): Promise<RbacMatrix> {
  try {
    const { data } = await api.get<ApiEnvelope<RbacMatrix>>('/ops/rbac')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载权限矩阵失败')
  }
}
