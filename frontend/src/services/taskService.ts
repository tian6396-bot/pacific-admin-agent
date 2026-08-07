import api from './api'

export type TaskTab = 'active' | 'approve' | 'history' | 'planner'
export type TaskStatus =
  | 'pending_approve'
  | 'processing'
  | 'need_materials'
  | 'done'
  | 'rejected'
  | 'cancelled'

export interface TaskEvent {
  id: string
  time: string
  title: string
  desc: string
  done: boolean
}

export interface TaskItem {
  id: string
  title: string
  service_id: string
  service_name: string
  domain_label: string
  kind: string
  status: TaskStatus
  tab: TaskTab
  applicant_name: string
  approver_name?: string | null
  form: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface TaskDetail extends TaskItem {
  events: TaskEvent[]
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

export async function listTasks(tab?: TaskTab): Promise<TaskItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<TaskItem[]>>('/tasks', {
      params: tab ? { tab } : undefined,
    })
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载任务失败')
  }
}

export async function getTask(id: string): Promise<TaskDetail> {
  try {
    const { data } = await api.get<ApiEnvelope<TaskDetail>>(`/tasks/${id}`)
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载任务详情失败')
  }
}

export async function applyTask(payload: {
  service_id: string
  title: string
  form: Record<string, unknown>
}): Promise<TaskDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TaskDetail>>('/tasks', payload)
    if (!data.success || !data.data) throw new Error(data.error || '提交失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '提交申请失败')
  }
}

export async function approveTask(id: string, comment?: string): Promise<TaskDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TaskDetail>>(`/tasks/${id}/approve`, { comment })
    if (!data.success || !data.data) throw new Error(data.error || '审批失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '审批失败')
  }
}

export async function rejectTask(id: string, comment?: string): Promise<TaskDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TaskDetail>>(`/tasks/${id}/reject`, { comment })
    if (!data.success || !data.data) throw new Error(data.error || '驳回失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '驳回失败')
  }
}

export async function requestMaterials(id: string): Promise<TaskDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TaskDetail>>(`/tasks/${id}/request-materials`)
    if (!data.success || !data.data) throw new Error(data.error || '操作失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '标记材料失败')
  }
}

export const statusMap: Record<TaskStatus, { label: string; tag: string }> = {
  pending_approve: { label: '待审批', tag: 'tag-warning' },
  processing: { label: '进行中', tag: 'tag-primary' },
  need_materials: { label: '待补充材料', tag: 'tag-danger' },
  done: { label: '已完成', tag: 'tag-success' },
  rejected: { label: '已驳回', tag: 'tag-danger' },
  cancelled: { label: '已取消', tag: 'tag-muted' },
}
