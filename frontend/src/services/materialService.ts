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

export type MaterialStatus = 'pending' | 'parsing' | 'success' | 'failed'

export interface MaterialItem {
  id: string
  filename: string
  content_type: string
  size: number
  size_label: string
  file_kind: string
  status: MaterialStatus
  parse_text?: string | null
  error?: string | null
  task_id?: string | null
  created_at: string
  updated_at: string
}

export async function listMaterials(): Promise<MaterialItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<MaterialItem[]>>('/materials')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载材料失败')
  }
}

export async function uploadMaterial(file: File, taskId?: string): Promise<MaterialItem> {
  const form = new FormData()
  form.append('file', file)
  if (taskId) form.append('task_id', taskId)
  try {
    const { data } = await api.post<ApiEnvelope<MaterialItem>>('/materials', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (!data.success) throw new Error(data.error || '上传失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '上传材料失败')
  }
}

export async function retryMaterial(id: string): Promise<MaterialItem> {
  try {
    const { data } = await api.post<ApiEnvelope<MaterialItem>>(`/materials/${id}/retry`)
    if (!data.success) throw new Error(data.error || '重试失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '重新解析失败')
  }
}

export async function linkMaterialTask(id: string, taskId: string | null): Promise<MaterialItem> {
  try {
    const { data } = await api.patch<ApiEnvelope<MaterialItem>>(`/materials/${id}`, {
      task_id: taskId,
    })
    if (!data.success) throw new Error(data.error || '关联失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '关联任务失败')
  }
}
