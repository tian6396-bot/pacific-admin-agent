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

export interface QaItemScore {
  label: string
  score: number
  max: number
}

export interface QaRecord {
  id: string
  ticket_id?: string | null
  session_label: string
  agent_name: string
  score: number
  items: QaItemScore[]
  reviewer: string
  created_at: string
}

export interface FollowupItem {
  id: string
  employee_name: string
  type: string
  due_date: string
  status: 'pending' | 'done' | 'overdue'
  assignee: string
  ticket_id?: string | null
  created_at: string
  updated_at: string
}

export async function listQaRecords(): Promise<QaRecord[]> {
  try {
    const { data } = await api.get<ApiEnvelope<QaRecord[]>>('/qa/records')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载质检记录失败')
  }
}

export async function listFollowups(): Promise<FollowupItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<FollowupItem[]>>('/qa/followups')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载回访任务失败')
  }
}

export async function updateFollowup(
  id: string,
  body: { status?: FollowupItem['status']; assignee?: string },
): Promise<FollowupItem> {
  try {
    const { data } = await api.patch<ApiEnvelope<FollowupItem>>(`/qa/followups/${id}`, body)
    if (!data.success) throw new Error(data.error || '更新失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '更新回访失败')
  }
}
