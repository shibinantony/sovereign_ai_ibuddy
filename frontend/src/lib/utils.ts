import type { ConversationSummary, Message, Source } from '../types'

const FALLBACK_DATE = new Date(0).toISOString()

export function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

export function asString(value: unknown, fallback = ''): string {
  if (typeof value === 'string') return value
  if (typeof value === 'number') return String(value)
  return fallback
}

export function normalizeSource(value: unknown): Source {
  const source = asRecord(value)
  const url = asString(source.url)
  let inferredDomain = ''
  try {
    inferredDomain = url ? new URL(url).hostname.replace(/^www\./, '') : ''
  } catch {
    inferredDomain = ''
  }

  return {
    title: asString(source.title, inferredDomain || 'Source'),
    url,
    snippet: asString(source.snippet, asString(source.description)),
    domain: asString(source.domain, inferredDomain),
  }
}

export function normalizeMessage(value: unknown, index = 0): Message {
  const message = asRecord(value)
  const role = asString(message.role, 'assistant')
  return {
    id: asString(message.id, `message-${index}`),
    role: role === 'user' || role === 'system' ? role : 'assistant',
    content: asString(message.content, asString(message.text)),
    created_at: asString(message.created_at, asString(message.createdAt, FALLBACK_DATE)),
    sources: Array.isArray(message.sources) ? message.sources.map(normalizeSource) : [],
  }
}

export function normalizeConversationSummary(value: unknown): ConversationSummary {
  const conversation = asRecord(value)
  return {
    id: asString(conversation.id),
    title: asString(conversation.title, 'New conversation'),
    created_at: asString(conversation.created_at, asString(conversation.createdAt, FALLBACK_DATE)),
    updated_at: asString(
      conversation.updated_at,
      asString(conversation.updatedAt, asString(conversation.created_at, FALLBACK_DATE)),
    ),
    message_count:
      typeof conversation.message_count === 'number'
        ? conversation.message_count
        : typeof conversation.messageCount === 'number'
          ? conversation.messageCount
          : undefined,
  }
}

export function formatRelativeTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime()) || date.getTime() === 0) return ''

  const delta = Date.now() - date.getTime()
  const minutes = Math.floor(delta / 60_000)
  if (minutes < 1) return 'Now'
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d`
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function groupLabel(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Older'

  const today = new Date()
  const startToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const startDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const days = Math.floor((startToday.getTime() - startDate.getTime()) / 86_400_000)
  if (days <= 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return 'Previous 7 days'
  if (days < 30) return 'Previous 30 days'
  return 'Older'
}

export function deriveTitle(content: string): string {
  const compact = content.replace(/\s+/g, ' ').trim()
  return compact.length > 48 ? `${compact.slice(0, 47).trimEnd()}…` : compact
}

export function temporaryId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}
