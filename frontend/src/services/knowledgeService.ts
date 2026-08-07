import api from './api'

export type KnowledgeType = 'faq' | 'doc'
export type KnowledgeStatus = 'draft' | 'review' | 'published' | 'offline'

export interface KnowledgeItem {
  id: string
  title: string
  type: KnowledgeType
  category: string
  status: KnowledgeStatus
  version: string
  author: string
  updated_at: string
  permission_tags?: string | null
  effective_from?: string | null
  effective_to?: string | null
  source_filename?: string | null
  content?: string | null
  chunk_count: number
  low_confidence_count: number
}

export interface KnowledgeChunk {
  id: string
  index: number
  text: string
  confidence: number
  needs_review: boolean
}

export interface KnowledgeDetail extends KnowledgeItem {
  chunks: KnowledgeChunk[]
}

export interface SearchHit {
  document_id: string
  chunk_id: string
  title: string
  category: string
  text: string
  score: number
  version: string
}

interface ApiEnvelope<T> {
  success: boolean
  data: T
  message?: string
  error?: string
}

function unwrapError(err: unknown, fallback: string): Error {
  const axiosErr = err as { response?: { data?: { detail?: string; error?: string } }; message?: string }
  const detail = axiosErr.response?.data?.detail || axiosErr.response?.data?.error
  return new Error(typeof detail === 'string' ? detail : fallback)
}

export async function listKnowledge(params?: {
  type?: KnowledgeType
  status?: KnowledgeStatus
}): Promise<KnowledgeItem[]> {
  try {
    const { data } = await api.get<ApiEnvelope<KnowledgeItem[]>>('/knowledge', { params })
    if (!data.success) throw new Error(data.error || '加载失败')
    return data.data || []
  } catch (err) {
    throw unwrapError(err, '加载知识列表失败')
  }
}

export async function getKnowledge(id: string): Promise<KnowledgeDetail> {
  try {
    const { data } = await api.get<ApiEnvelope<KnowledgeDetail>>(`/knowledge/${id}`)
    if (!data.success || !data.data) throw new Error(data.error || '加载失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '加载知识详情失败')
  }
}

export async function createKnowledge(payload: {
  title: string
  type: KnowledgeType
  category: string
  content: string
  version?: string
}): Promise<KnowledgeDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<KnowledgeDetail>>('/knowledge', payload)
    if (!data.success || !data.data) throw new Error(data.error || '创建失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '创建失败')
  }
}

export async function submitKnowledge(id: string): Promise<KnowledgeDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<KnowledgeDetail>>(`/knowledge/${id}/submit`)
    if (!data.success || !data.data) throw new Error(data.error || '提交失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '提交审核失败')
  }
}

export async function publishKnowledge(id: string): Promise<KnowledgeDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<KnowledgeDetail>>(`/knowledge/${id}/publish`)
    if (!data.success || !data.data) throw new Error(data.error || '发布失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '发布失败')
  }
}

export async function offlineKnowledge(id: string): Promise<KnowledgeDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<KnowledgeDetail>>(`/knowledge/${id}/offline`)
    if (!data.success || !data.data) throw new Error(data.error || '下线失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '下线失败')
  }
}

export async function reindexKnowledge(id: string): Promise<KnowledgeDetail> {
  try {
    const { data } = await api.post<ApiEnvelope<KnowledgeDetail>>(`/knowledge/${id}/reindex`)
    if (!data.success || !data.data) throw new Error(data.error || '重建失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, '重建索引失败')
  }
}

export async function updateChunk(
  docId: string,
  chunkId: string,
  text: string,
): Promise<KnowledgeChunk> {
  try {
    const { data } = await api.patch<ApiEnvelope<KnowledgeChunk>>(
      `/knowledge/${docId}/chunks/${chunkId}`,
      { text },
    )
    if (!data.success || !data.data) throw new Error(data.error || '校对失败')
    return data.data
  } catch (err) {
    throw unwrapError(err, 'Chunk 校对失败')
  }
}

export async function searchKnowledge(query: string, topK = 5): Promise<SearchHit[]> {
  try {
    const { data } = await api.post<ApiEnvelope<{ hits: SearchHit[]; mode: string }>>(
      '/knowledge/search',
      { query, top_k: topK },
    )
    if (!data.success || !data.data) throw new Error(data.error || '检索失败')
    return data.data.hits || []
  } catch (err) {
    throw unwrapError(err, '检索失败')
  }
}
