import api from './api'

export type ContentKind = 'rewrite' | 'report' | 'export'
export type ExportDataset =
  | 'my_tasks'
  | 'my_tickets'
  | 'agent_tickets'
  | 'qa_followups'
  | 'knowledge'
  | 'bad_cases'
  | 'audit_logs'

export interface ContentArtifact {
  id: string
  kind: ContentKind
  title: string
  summary: string
  body: string
  mime: string
  download_name: string
  task_id?: string | null
  owner_role: string
  created_at: string
  has_pptx?: boolean
  pptx_name?: string | null
}

export interface ContentCapabilities {
  can_rewrite: boolean
  can_report: boolean
  can_pptx: boolean
  export_datasets: ExportDataset[]
  notes: string[]
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

export const datasetLabel: Record<ExportDataset, string> = {
  my_tasks: '我的任务',
  my_tickets: '我的工单',
  agent_tickets: '本人经办工单',
  qa_followups: '质检回访',
  knowledge: '知识清单',
  bad_cases: 'Bad Case',
  audit_logs: '审计日志',
}

export async function getContentCapabilities(): Promise<ContentCapabilities> {
  try {
    const { data } = await api.get<ApiEnvelope<ContentCapabilities>>('/content/capabilities')
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载能力失败')
  }
}

export async function listContentArtifacts(): Promise<ContentArtifact[]> {
  try {
    const { data } = await api.get<ApiEnvelope<ContentArtifact[]>>('/content/artifacts')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载产出列表失败')
  }
}

export async function rewriteContent(payload: {
  text: string
  tone?: 'formal' | 'concise' | 'friendly'
  title?: string
}): Promise<ContentArtifact> {
  try {
    const { data } = await api.post<ApiEnvelope<ContentArtifact>>('/content/rewrite', payload)
    if (!data.success || !data.data) throw new Error(data.error || '改写失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '改写失败')
  }
}

export async function generateReport(payload: {
  topic: string
  points?: string
  title?: string
}): Promise<ContentArtifact> {
  try {
    const { data } = await api.post<ApiEnvelope<ContentArtifact>>('/content/report', payload)
    if (!data.success || !data.data) throw new Error(data.error || '生成失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '生成报告失败')
  }
}

export async function exportContentData(payload: {
  dataset: ExportDataset
  title?: string
}): Promise<ContentArtifact> {
  try {
    const { data } = await api.post<ApiEnvelope<ContentArtifact>>('/content/export', payload)
    if (!data.success || !data.data) throw new Error(data.error || '导出失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '导出失败')
  }
}

export function downloadArtifact(item: ContentArtifact) {
  const type = item.mime || 'text/plain;charset=utf-8'
  const blob = new Blob([item.body], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = item.download_name || 'artifact.txt'
  a.click()
  URL.revokeObjectURL(url)
}

export async function downloadArtifactPptx(item: ContentArtifact): Promise<void> {
  try {
    const { data } = await api.get(`/content/artifacts/${item.id}/pptx`, {
      responseType: 'blob',
    })
    const blob = data as Blob
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = item.pptx_name || `${item.title || 'report'}.pptx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    throw unwrapError(err, '下载 PPTX 失败')
  }
}
