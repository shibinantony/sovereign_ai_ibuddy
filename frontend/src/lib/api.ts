import type {
  Conversation,
  ConversationSummary,
  HealthStatus,
  SearchMode,
  StreamEvent,
  StreamEventName,
} from '../types'
import {
  asRecord,
  asString,
  normalizeConversationSummary,
  normalizeMessage,
} from './utils'

const API_ROOT = '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function apiErrorMessage(payload: unknown, status: number): string {
  const record = asRecord(payload)
  if (typeof record.detail === 'string') return record.detail
  if (typeof record.message === 'string') return record.message
  if (Array.isArray(record.detail)) {
    const messages = record.detail
      .map((item) => asString(asRecord(item).msg))
      .filter(Boolean)
    if (messages.length) return messages.join(' ')
  }
  return `Request failed (${status}).`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body) headers.set('Content-Type', 'application/json')
  headers.set('Accept', 'application/json')

  let response: Response
  try {
    response = await fetch(`${API_ROOT}${path}`, { ...init, headers })
  } catch {
    throw new ApiError('Could not reach the iBuddy service.')
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new ApiError(apiErrorMessage(payload, response.status), response.status)
  }

  if (response.status === 204) return undefined as T
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new ApiError('The service returned an invalid response.', response.status)
  }
  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError('The service returned invalid JSON.', response.status)
  }
}

export async function getHealth(): Promise<HealthStatus> {
  try {
    const raw = asRecord(await request<unknown>('/health'))
    const rawStatus = asString(raw.status, 'online').toLowerCase()
    const modelRecord = asRecord(raw.model)
    const searchRecord = asRecord(raw.search)
    const modelBackend = asString(
      modelRecord.backend,
      asString(raw.model_backend, 'unknown'),
    ).toLowerCase()
    const localModel =
      modelBackend === 'local' ||
      modelBackend === 'llama_cpp' ||
      modelBackend === 'llama.cpp' ||
      modelBackend === 'transformers'
    const offlineMode =
      typeof raw.offline_mode === 'boolean' ? raw.offline_mode : localModel
    const searchReady =
      typeof searchRecord.ready === 'boolean'
        ? searchRecord.ready && !offlineMode
        : !offlineMode
    const modelReady = modelRecord.ready !== false
    const modelState = asString(modelRecord.state).toLowerCase()
    const modelOperational = modelRecord.operational
    const loadingStates = new Set([
      'configured',
      'downloading',
      'idle',
      'installing',
      'loading',
      'starting',
    ])
    const missingStates = new Set([
      'closed',
      'error',
      'missing',
      'missing_assets',
      'not_installed',
      'unconfigured',
    ])
    const awaitingModel = loadingStates.has(modelState)
    const modelMissing = missingStates.has(modelState)
    return {
      status:
        awaitingModel || rawStatus === 'loading' || rawStatus === 'starting'
          ? 'loading'
          : !modelMissing && modelOperational !== false && modelReady &&
              (rawStatus === 'ok' ||
                rawStatus === 'healthy' ||
                rawStatus === 'ready' ||
                rawStatus === 'online')
            ? 'online'
            : 'offline',
      model: asString(
        raw.model,
        asString(
          raw.model_name,
          asString(modelRecord.id, asString(modelRecord.name, asString(modelRecord.backend, 'Search LM'))),
        ),
      ),
      modelBackend,
      localModel,
      offlineMode,
      search: {
        ready: searchReady,
        provider: asString(searchRecord.provider, offlineMode ? 'disabled' : 'web'),
      },
      state: modelState || undefined,
      detail: asString(raw.detail, asString(raw.message)) || undefined,
    }
  } catch (error) {
    return {
      status: 'offline',
      model: 'Local model',
      modelBackend: 'llama_cpp',
      localModel: true,
      offlineMode: true,
      search: { ready: false, provider: 'disabled' },
      detail: error instanceof Error ? error.message : 'Service unavailable',
    }
  }
}

export async function listConversations(signal?: AbortSignal): Promise<ConversationSummary[]> {
  const raw = await request<unknown>('/conversations?limit=500', { signal })
  const record = asRecord(raw)
  const values = Array.isArray(raw)
    ? raw
    : Array.isArray(record.conversations)
      ? record.conversations
      : Array.isArray(record.items)
        ? record.items
        : []

  return values
    .map(normalizeConversationSummary)
    .filter((conversation) => conversation.id)
    .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
}

export async function createConversation(title?: string, signal?: AbortSignal): Promise<Conversation> {
  const raw = await request<unknown>('/conversations', {
    method: 'POST',
    body: JSON.stringify(title ? { title } : {}),
    signal,
  })
  return normalizeConversation(raw)
}

export async function getConversation(id: string, signal?: AbortSignal): Promise<Conversation> {
  const raw = await request<unknown>(`/conversations/${encodeURIComponent(id)}`, { signal })
  return normalizeConversation(raw)
}

export async function renameConversation(
  id: string,
  title: string,
): Promise<ConversationSummary> {
  const raw = await request<unknown>(`/conversations/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
  const record = asRecord(raw)
  return normalizeConversationSummary(record.conversation ?? raw)
}

export async function deleteConversation(id: string): Promise<void> {
  await request<void>(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

function normalizeConversation(raw: unknown): Conversation {
  const root = asRecord(raw)
  const value = asRecord(root.conversation ?? raw)
  const summary = normalizeConversationSummary(value)
  const messages = Array.isArray(value.messages)
    ? value.messages.map((message, index) => normalizeMessage(message, index))
    : []

  return { ...summary, messages }
}

function parseSseBlock(block: string): StreamEvent | null {
  let event = 'delta'
  const dataLines: string[] = []

  for (const rawLine of block.split(/\r?\n/)) {
    const line = rawLine.trimEnd()
    if (!line || line.startsWith(':')) continue
    if (line.startsWith('event:')) event = line.slice(6).trim()
    if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
  }

  if (!dataLines.length) return null
  const rawData = dataLines.join('\n')
  let data: unknown = rawData
  try {
    data = JSON.parse(rawData)
  } catch {
    data = { delta: rawData }
  }

  const embeddedType = asString(asRecord(data).type)
  const resolvedEvent = (embeddedType || event) as StreamEventName
  if (!['meta', 'sources', 'delta', 'done', 'error'].includes(resolvedEvent)) return null
  return { event: resolvedEvent, data }
}

export async function streamMessage(
  conversationId: string,
  content: string,
  searchMode: SearchMode,
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(
      `${API_ROOT}/conversations/${encodeURIComponent(conversationId)}/messages/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({ content, search_mode: searchMode }),
        signal,
      },
    )
  } catch (error) {
    if (signal.aborted) throw error
    throw new ApiError('The response stream could not be started.')
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new ApiError(apiErrorMessage(payload, response.status), response.status)
  }

  if (!response.headers.get('content-type')?.startsWith('text/event-stream')) {
    throw new ApiError('The service returned an invalid response stream.', response.status)
  }
  if (!response.body) throw new ApiError('The service returned an empty response stream.')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let terminalEventReceived = false

  const dispatchBlock = (block: string) => {
    const parsed = parseSseBlock(block)
    if (!parsed) return
    if (parsed.event === 'done' || parsed.event === 'error') terminalEventReceived = true
    onEvent(parsed)
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n')

      let boundary = buffer.indexOf('\n\n')
      while (boundary !== -1) {
        const block = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        dispatchBlock(block)
        boundary = buffer.indexOf('\n\n')
      }

      if (done) break
    }

    if (buffer.trim()) {
      dispatchBlock(buffer)
    }

    if (!terminalEventReceived) {
      throw new ApiError('The response stream ended before completion.')
    }
  } finally {
    reader.releaseLock()
  }
}
