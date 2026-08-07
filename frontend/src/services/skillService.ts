import api from './api'

export interface ConfirmCard {
  run_id: string
  skill_id: string
  skill_name: string
  summary: string
  slots: Record<string, unknown>
  mock_tool: boolean
  tool_name?: string | null
}

export interface SkillItem {
  id: string
  name: string
  intent: string
  domain: string
  status: 'published' | 'draft' | 'offline'
  description: string
  tool_id?: string | null
  service_id?: string | null
  priority: string
}

export interface FlowNode {
  id: string
  type: string
  label: string
  config: string
}

export interface ToolItem {
  id: string
  name: string
  method: string
  endpoint: string
  timeout_ms: number
  retries: number
  status: 'active' | 'disabled'
  mock_enabled: boolean
  schema_json: string
  mock_response: string
}

export interface SkillRun {
  id: string
  skill_id: string
  skill_name: string
  status: string
  slots: Record<string, unknown>
  confirm_summary: string
  task_id?: string | null
  tool_result?: Record<string, unknown> | null
  confirm_card?: ConfirmCard | null
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

export async function listSkills(): Promise<SkillItem[]> {
  const { data } = await api.get<ApiEnvelope<SkillItem[]>>('/skills')
  if (!data.success) throw new Error(data.error || '加载失败')
  return data.data || []
}

export async function getSkillDetail(
  id: string,
): Promise<{ skill: SkillItem; nodes: FlowNode[] }> {
  const { data } = await api.get<ApiEnvelope<{ skill: SkillItem; nodes: FlowNode[] }>>(
    `/skills/${id}`,
  )
  if (!data.success || !data.data) throw new Error(data.error || '加载失败')
  return data.data
}

export async function listTools(): Promise<ToolItem[]> {
  const { data } = await api.get<ApiEnvelope<ToolItem[]>>('/tools')
  if (!data.success) throw new Error(data.error || '加载失败')
  return data.data || []
}

export async function confirmSkillRun(runId: string): Promise<SkillRun> {
  try {
    const { data } = await api.post<ApiEnvelope<SkillRun>>(`/skills/runs/${runId}/confirm`, {})
    if (!data.success || !data.data) throw new Error(data.error || '确认失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '确认失败')
  }
}

export async function cancelSkillRun(runId: string, reason?: string): Promise<SkillRun> {
  try {
    const { data } = await api.post<ApiEnvelope<SkillRun>>(`/skills/runs/${runId}/cancel`, {
      reason,
    })
    if (!data.success || !data.data) throw new Error(data.error || '取消失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '取消失败')
  }
}
