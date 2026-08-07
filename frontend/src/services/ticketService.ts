import api, { resolveWsBase } from './api'

export type TicketStatus =
  | 'waiting'
  | 'active'
  | 'need_info'
  | 'need_expert'
  | 'resolved'
  | 'closed'

export type TicketPriority = 'normal' | 'high' | 'urgent'

export interface HandoffPackage {
  intent: string
  confidence: number
  summary: string
  evidence: string[]
  chat_session_id?: string | null
}

export interface TicketMessage {
  id: string
  ticket_id: string
  role: 'employee' | 'agent' | 'system' | 'ai'
  content: string
  sender_name: string
  created_at: string
}

export interface TicketItem {
  id: string
  subject: string
  channel: string
  status: TicketStatus
  priority: TicketPriority
  employee_id: string
  employee_name: string
  employee_dept?: string | null
  agent_id?: string | null
  agent_name?: string | null
  chat_session_id?: string | null
  wait_minutes: number
  sla_deadline?: string | null
  sla_overdue: boolean
  handoff: HandoffPackage
  created_at: string
  updated_at: string
}

export interface TicketDetail extends TicketItem {
  messages: TicketMessage[]
}

export interface QueueBoard {
  kpi: {
    waiting: number
    today_claimed: number
    avg_wait_minutes: number
    sla_ok_rate: number
  }
  items: TicketItem[]
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

export async function listMyTickets(): Promise<TicketItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<TicketItem[]>>('/tickets')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载工单失败')
  }
}

export async function createHandoff(payload: {
  session_id?: string
  reason?: string
  priority?: TicketPriority
  topic?: string
}): Promise<TicketDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TicketDetail>>('/tickets/handoff', payload)
    if (!data.success || !data.data) throw new Error(data.error || '转人工失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '转人工失败')
  }
}

export async function getTicket(id: string): Promise<TicketDetail> {
  try {
    const { data } = await api.get<ApiEnvelope<TicketDetail>>(`/tickets/${id}`)
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载工单失败')
  }
}

export async function sendTicketMessage(id: string, content: string): Promise<TicketMessage> {
  try {
    const { data } = await api.post<ApiEnvelope<TicketMessage>>(`/tickets/${id}/messages`, {
      content,
    })
    if (!data.success || !data.data) throw new Error(data.error || '发送失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '发送失败')
  }
}

export async function getQueueBoard(): Promise<QueueBoard> {
  try {
    const { data } = await api.get<ApiEnvelope<QueueBoard>>('/agent/queue')
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载队列失败')
  }
}

export async function claimTicket(id: string): Promise<TicketDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TicketDetail>>(`/agent/tickets/${id}/claim`)
    if (!data.success || !data.data) throw new Error(data.error || '接管失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '接管失败')
  }
}

export async function resolveTicket(id: string, comment?: string): Promise<TicketDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<TicketDetail>>(`/agent/tickets/${id}/resolve`, {
      comment,
    })
    if (!data.success || !data.data) throw new Error(data.error || '结案失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '结案失败')
  }
}

export async function agentSendMessage(id: string, content: string): Promise<TicketMessage> {
  try {
    const { data } = await api.post<ApiEnvelope<TicketMessage>>(
      `/agent/tickets/${id}/messages`,
      { content },
    )
    if (!data.success || !data.data) throw new Error(data.error || '发送失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '发送失败')
  }
}

export async function agentGetTicket(id: string): Promise<TicketDetail> {
  try {
    const { data } = await api.get<ApiEnvelope<TicketDetail>>(`/agent/tickets/${id}`)
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载工单失败')
  }
}

export function connectTicketSocket(
  room: string,
  handlers: {
    onEvent?: (data: Record<string, unknown>) => void
    onError?: () => void
  },
): WebSocket | null {
  const token = localStorage.getItem('token')
  if (!token) return null
  const url = `${resolveWsBase()}/chat/ws?token=${encodeURIComponent(token)}&room=${encodeURIComponent(room)}`
  const ws = new WebSocket(url)
  ws.onmessage = (ev) => {
    try {
      handlers.onEvent?.(JSON.parse(ev.data as string))
    } catch {
      /* ignore */
    }
  }
  ws.onerror = () => handlers.onError?.()
  return ws
}

export const ticketStatusMap: Record<TicketStatus, { label: string; tag: string }> = {
  waiting: { label: '待接入', tag: 'tag-danger' },
  active: { label: '处理中', tag: 'tag-primary' },
  need_info: { label: '待补充', tag: 'tag-warning' },
  need_expert: { label: '待专家', tag: 'tag-warning' },
  resolved: { label: '已解决', tag: 'tag-success' },
  closed: { label: '已关闭', tag: 'tag-muted' },
}

export const priorityMap = {
  normal: { label: '普通', tag: 'tag-muted' },
  high: { label: '优先', tag: 'tag-primary' },
  urgent: { label: '紧急', tag: 'tag-danger' },
} as const
