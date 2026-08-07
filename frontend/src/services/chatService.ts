import api, { resolveWsBase } from './api'

export interface Citation {
  document_id: string
  title: string
  text: string
  score: number
  version: string
}

export interface ConfirmCard {
  run_id: string
  skill_id: string
  skill_name: string
  summary: string
  slots: Record<string, unknown>
  mock_tool: boolean
  tool_name?: string | null
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  citations: Citation[]
  route?: string | null
  created_at: string
  confirm_card?: ConfirmCard | null
}

export interface ChatSession {
  id: string
  title: string
  updated_at: string
  created_at: string
  preview?: string | null
}

export interface SessionDetail extends ChatSession {
  messages: ChatMessage[]
}

export interface ChatReply {
  session: ChatSession
  user_message: ChatMessage
  assistant_message: ChatMessage
  confirm_card?: ConfirmCard | null
}

interface ApiEnvelope<T> {
  success: boolean
  data: T
  message?: string
  error?: string
}

function unwrapError(err: unknown, fallback: string): Error {
  const axiosErr = err as { response?: { data?: { detail?: string; error?: string } } }
  const detail = axiosErr.response?.data?.detail || axiosErr.response?.data?.error
  return new Error(typeof detail === 'string' ? detail : fallback)
}

export async function listSessions(): Promise<ChatSession[]> {
  try {
    const { data } = await api.get<ApiEnvelope<ChatSession[]>>('/chat/sessions')
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载会话失败')
  }
}

export async function createSession(title?: string): Promise<ChatSession> {
  try {
    const { data } = await api.post<ApiEnvelope<ChatSession>>('/chat/sessions', { title })
    if (!data.success || !data.data) throw new Error(data.error || '创建失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '创建会话失败')
  }
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  try {
    const { data } = await api.get<ApiEnvelope<SessionDetail>>(`/chat/sessions/${sessionId}`)
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载会话详情失败')
  }
}

export async function sendMessage(content: string, sessionId?: string | null): Promise<ChatReply> {
  try {
    const { data } = await api.post<ApiEnvelope<ChatReply>>('/chat/messages', {
      content,
      session_id: sessionId || undefined,
    })
    if (!data.success || !data.data) throw new Error(data.error || '发送失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '发送失败')
  }
}

export function connectChatSocket(
  sessionId: string,
  handlers: {
    onMessage?: (msg: ChatMessage) => void
    onStatus?: (status: string) => void
    onError?: () => void
  },
): WebSocket | null {
  const token = localStorage.getItem('token')
  if (!token || !sessionId) return null

  const url = `${resolveWsBase()}/chat/ws?token=${encodeURIComponent(token)}&session_id=${encodeURIComponent(sessionId)}`
  const ws = new WebSocket(url)

  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data as string) as {
        type: string
        status?: string
        message?: ChatMessage
      }
      if (data.type === 'status' && data.status) handlers.onStatus?.(data.status)
      if (data.type === 'message' && data.message) handlers.onMessage?.(data.message)
    } catch {
      /* ignore */
    }
  }
  ws.onerror = () => handlers.onError?.()
  return ws
}

export function formatSessionTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatMsgTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

export function citeLabel(msg: ChatMessage): string | undefined {
  if (!msg.citations?.length) return undefined
  const c = msg.citations[0]
  return `来源：${c.title}${c.version ? ` · ${c.version}` : ''}`
}
