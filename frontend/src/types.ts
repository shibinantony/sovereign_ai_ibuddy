export type SearchMode = 'auto' | 'web' | 'off'

export type MessageRole = 'user' | 'assistant' | 'system'

export type ResponseState = 'stopped' | 'error'

export interface Source {
  title: string
  url: string
  snippet: string
  domain: string
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  created_at: string
  sources: Source[]
  pending?: boolean
  responseState?: ResponseState
}

export interface ConversationSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export interface Conversation extends ConversationSummary {
  messages: Message[]
}

export interface HealthStatus {
  status: 'online' | 'loading' | 'offline'
  model: string
  modelBackend: string
  localModel: boolean
  offlineMode: boolean
  search: {
    ready: boolean
    provider: string
  }
  state?: string
  detail?: string
}

export type StreamEventName = 'meta' | 'sources' | 'delta' | 'done' | 'error'

export interface StreamEvent {
  event: StreamEventName
  data: unknown
}

export interface ToastMessage {
  id: number
  message: string
  tone?: 'neutral' | 'danger'
}
