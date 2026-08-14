import { useCallback, useEffect, useRef, useState } from 'react'
import { Menu, Plus, RefreshCw, Sparkles } from 'lucide-react'
import { Composer } from './components/Composer'
import { ConfirmDialog } from './components/ConfirmDialog'
import { EmptyState } from './components/EmptyState'
import { MessageBubble } from './components/MessageBubble'
import { Sidebar } from './components/Sidebar'
import { ToastRegion } from './components/ToastRegion'
import { useTheme } from './hooks/useTheme'
import {
  ApiError,
  createConversation,
  deleteConversation,
  getConversation,
  getHealth,
  listConversations,
  renameConversation,
  streamMessage,
} from './lib/api'
import { readStoredValue, removeStoredValue, writeStoredValue } from './lib/storage'
import {
  asRecord,
  asString,
  deriveTitle,
  normalizeConversationSummary,
  normalizeMessage,
  normalizeSource,
  temporaryId,
} from './lib/utils'
import type {
  Conversation,
  ConversationSummary,
  HealthStatus,
  Message,
  ResponseState,
  SearchMode,
  StreamEvent,
  ToastMessage,
} from './types'

const DEFAULT_HEALTH: HealthStatus = {
  status: 'loading',
  model: 'Local model',
  modelBackend: 'llama_cpp',
  localModel: true,
  offlineMode: true,
  search: { ready: false, provider: 'disabled' },
}

const SEARCH_MODE_STORAGE_KEY = 'ibuddy-search-mode'
const ACTIVE_CONVERSATION_STORAGE_KEY = 'ibuddy-active-conversation'
const MAX_MESSAGE_CHARS = 12_000

interface InterruptedTurn {
  userId: string
  assistantId: string
  content: string
  createdAt: string
  responseState: ResponseState
}

function findTurnUserIndex(
  messages: Message[],
  canonicalUserId: string | null,
  content?: string,
  createdAt?: string,
): number {
  if (canonicalUserId) {
    const canonicalIndex = messages.findIndex((message) => message.id === canonicalUserId)
    if (canonicalIndex >= 0) return canonicalIndex
  }
  if (!content) return -1
  const earliestTimestamp = createdAt ? Date.parse(createdAt) : Number.NaN
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index]
    const messageTimestamp = Date.parse(message.created_at)
    const isCurrentTurn =
      Number.isNaN(earliestTimestamp) ||
      (!Number.isNaN(messageTimestamp) && messageTimestamp >= earliestTimestamp)
    if (isCurrentTurn && message.role === 'user' && message.content === content) return index
  }
  return -1
}

function findAssistantIndexAfter(messages: Message[], userIndex: number): number {
  if (userIndex < 0) return -1
  for (let index = messages.length - 1; index > userIndex; index -= 1) {
    if (messages[index].role === 'assistant') return index
  }
  return -1
}

function loadSearchModePreference(): SearchMode | null {
  const value = readStoredValue(SEARCH_MODE_STORAGE_KEY)
  return value === 'auto' || value === 'web' || value === 'off' ? value : null
}

function saveSearchModePreference(mode: SearchMode): void {
  writeStoredValue(SEARCH_MODE_STORAGE_KEY, mode)
}

function healthLabel(health: HealthStatus): string {
  if (health.localModel) {
    if (health.state === 'installing' || health.state === 'downloading') {
      return 'Installing local model'
    }
    if (health.state === 'starting' || health.state === 'loading') {
      return 'Loading local model'
    }
    if (health.state === 'idle' || health.state === 'configured') {
      return 'Local model installed'
    }
    if (health.state === 'ready' || health.state === 'operational' || health.status === 'online') {
      return 'Local model ready'
    }
    if (
      health.state === 'missing' ||
      health.state === 'missing_assets' ||
      health.state === 'not_installed' ||
      health.state === 'unconfigured'
    ) return 'Local assets missing'
    if (health.state === 'error') return 'Local model error'
    if (health.state === 'closed') return 'Local model stopped'
    if (health.status === 'loading') return 'Loading local model'
    return 'Local model unavailable'
  }
  if (health.state === 'configured' || health.state === 'idle') return 'Model configured'
  if (health.status === 'online') return 'Model ready'
  if (health.status === 'loading') return 'Connecting'
  return 'Reconnect'
}

function toSummary(conversation: Conversation): ConversationSummary {
  return {
    id: conversation.id,
    title: conversation.title,
    created_at: conversation.created_at,
    updated_at: conversation.updated_at,
    message_count: conversation.message_count,
  }
}

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}

function waitFor(milliseconds: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }

    const timer = window.setTimeout(() => {
      signal.removeEventListener('abort', onAbort)
      resolve()
    }, milliseconds)
    const onAbort = () => {
      window.clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    }
    signal.addEventListener('abort', onAbort, { once: true })
  })
}

export default function App() {
  const { theme, toggleTheme } = useTheme()
  const [initialSearchModePreference] = useState<SearchMode | null>(loadSearchModePreference)
  const preferredSearchMode = useRef<SearchMode | null>(initialSearchModePreference)
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [activeTitle, setActiveTitle] = useState('New conversation')
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const [searchMode, setSearchMode] = useState<SearchMode>('off')
  const [health, setHealth] = useState<HealthStatus>(DEFAULT_HEALTH)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [conversationLoading, setConversationLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const streamController = useRef<AbortController | null>(null)
  const navigationController = useRef<AbortController | null>(null)
  const selectionVersion = useRef(0)
  const historyVersion = useRef(0)
  const creatingRef = useRef(false)
  const toastCounter = useRef(0)
  const messagesEnd = useRef<HTMLDivElement>(null)
  const deleteReturnFocus = useRef<HTMLElement | null>(null)

  const pushToast = useCallback((message: string, tone: ToastMessage['tone'] = 'neutral') => {
    const id = ++toastCounter.current
    setToasts((current) => [...current, { id, message, tone }])
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id))
    }, 4200)
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const upsertSummary = useCallback((summary: ConversationSummary) => {
    if (!summary.id) return
    historyVersion.current += 1
    setConversations((current) => {
      const rest = current.filter((conversation) => conversation.id !== summary.id)
      return [summary, ...rest].sort(
        (left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at),
      )
    })
  }, [])

  const refreshHistory = useCallback(async (quiet = false) => {
    const version = ++historyVersion.current
    if (!quiet) setHistoryLoading(true)
    try {
      const nextConversations = await listConversations()
      if (version === historyVersion.current) setConversations(nextConversations)
    } catch (error) {
      if (!quiet && version === historyVersion.current) {
        pushToast(getErrorMessage(error), 'danger')
      }
    } finally {
      if (!quiet && version === historyVersion.current) setHistoryLoading(false)
    }
  }, [pushToast])

  const selectConversation = useCallback(async (id: string) => {
    if (creatingRef.current) return
    const version = ++selectionVersion.current
    navigationController.current?.abort()
    const navigation = new AbortController()
    navigationController.current = navigation
    streamController.current?.abort()
    streamController.current = null
    setStreaming(false)
    creatingRef.current = false
    setCreating(false)
    setActiveId(id)
    setConversationLoading(true)
    setSidebarOpen(false)
    writeStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY, id)

    try {
      const conversation = await getConversation(id, navigation.signal)
      if (version !== selectionVersion.current) return
      setActiveTitle(conversation.title || 'New conversation')
      setMessages(conversation.messages)
      upsertSummary(toSummary(conversation))
    } catch (error) {
      if (version !== selectionVersion.current || navigation.signal.aborted) return
      pushToast(getErrorMessage(error), 'danger')
      setActiveId(null)
      setActiveTitle('New conversation')
      setMessages([])
      removeStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY)
    } finally {
      if (version === selectionVersion.current) setConversationLoading(false)
      if (navigationController.current === navigation) navigationController.current = null
    }
  }, [pushToast, upsertSummary])

  const reconcileConversationAfterAbort = useCallback(async (
    conversationId: string,
    operationVersion: number,
    streamedContent: string,
    canonicalUserId: string | null,
    interruptedTurn?: InterruptedTurn,
  ) => {
    const navigation = new AbortController()
    navigationController.current?.abort()
    navigationController.current = navigation
    const targetContent = streamedContent.trim()
    const retryDelays = targetContent ? [250, 500, 1_000, 1_500, 2_000] : [120]
    let latestConversation: Conversation | null = null
    let previousAssistantContent: string | null = null

    try {
      for (const delay of retryDelays) {
        await waitFor(delay, navigation.signal)
        const conversation = await getConversation(conversationId, navigation.signal)
        if (operationVersion !== selectionVersion.current || navigation.signal.aborted) return
        latestConversation = conversation

        if (!targetContent) break
        const userIndex = findTurnUserIndex(
          conversation.messages,
          canonicalUserId,
          interruptedTurn?.content,
          interruptedTurn?.createdAt,
        )
        const assistantIndex = findAssistantIndexAfter(conversation.messages, userIndex)
        const canonicalAssistant = assistantIndex >= 0
          ? conversation.messages[assistantIndex]
          : undefined
        const canonicalContent = canonicalAssistant?.content.trim() ?? ''
        const caughtUp = canonicalContent.length >= targetContent.length
        if (caughtUp && canonicalContent === previousAssistantContent) break
        previousAssistantContent = caughtUp ? canonicalContent : null
      }

      if (
        latestConversation &&
        operationVersion === selectionVersion.current &&
        !navigation.signal.aborted
      ) {
        const reconciledConversation = latestConversation
        setActiveId(reconciledConversation.id)
        setActiveTitle(reconciledConversation.title || 'New conversation')
        setMessages((current) => {
          if (!interruptedTurn) return reconciledConversation.messages

          const reconciled = [...reconciledConversation.messages]
          const optimisticUser = current.find((message) => message.id === interruptedTurn.userId)
          let userIndex = findTurnUserIndex(
            reconciled,
            canonicalUserId,
            interruptedTurn.content,
            interruptedTurn.createdAt,
          )
          if (userIndex < 0) {
            reconciled.push(optimisticUser ?? {
              id: interruptedTurn.userId,
              role: 'user',
              content: interruptedTurn.content,
              created_at: interruptedTurn.createdAt,
              sources: [],
            })
            userIndex = reconciled.length - 1
          }

          const assistantIndex = findAssistantIndexAfter(reconciled, userIndex)
          if (assistantIndex >= 0) {
            reconciled[assistantIndex] = {
              ...reconciled[assistantIndex],
              pending: false,
              responseState: interruptedTurn.responseState,
            }
          } else {
            const optimisticAssistant = current.find(
              (message) => message.id === interruptedTurn.assistantId,
            )
            reconciled.push({
              ...(optimisticAssistant ?? {
                id: interruptedTurn.assistantId,
                role: 'assistant' as const,
                content: streamedContent,
                created_at: interruptedTurn.createdAt,
                sources: [],
              }),
              pending: false,
              responseState: interruptedTurn.responseState,
            })
          }
          return reconciled
        })
        upsertSummary(toSummary(reconciledConversation))
        writeStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY, reconciledConversation.id)
      }
    } catch (error) {
      if (operationVersion === selectionVersion.current && !navigation.signal.aborted) {
        pushToast(getErrorMessage(error), 'danger')
      }
    } finally {
      if (navigationController.current === navigation) navigationController.current = null
    }
  }, [pushToast, upsertSummary])

  useEffect(() => {
    let active = true
    const initialize = async () => {
      const historyRequestVersion = ++historyVersion.current
      const initialSelectionVersion = selectionVersion.current
      const [nextHealth, historyResult] = await Promise.all([
        getHealth(),
        listConversations().catch(() => null),
      ])
      if (!active) return
      setHealth(nextHealth)
      setHistoryLoading(false)
      if (!historyResult) {
        if (historyRequestVersion === historyVersion.current) {
          pushToast('Conversation history is unavailable.', 'danger')
        }
        return
      }
      if (historyRequestVersion !== historyVersion.current) return
      setConversations(historyResult)
      const savedId = readStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY)
      if (
        initialSelectionVersion === selectionVersion.current &&
        savedId
      ) {
        void selectConversation(savedId)
      }
    }
    void initialize()

    const healthTimer = window.setInterval(() => {
      void getHealth().then((nextHealth) => {
        if (active) setHealth(nextHealth)
      })
    }, 5_000)

    return () => {
      active = false
      window.clearInterval(healthTimer)
      navigationController.current?.abort()
      streamController.current?.abort()
    }
  }, [pushToast, selectConversation])

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: streaming ? 'auto' : 'smooth', block: 'end' })
  }, [messages, streaming])

  useEffect(() => {
    const webSearchAvailable = !health.offlineMode && health.search.ready
    const nextMode = webSearchAvailable ? preferredSearchMode.current ?? 'auto' : 'off'
    setSearchMode((current) => current === nextMode ? current : nextMode)
  }, [health.offlineMode, health.search.ready])

  const changeSearchMode = useCallback((mode: SearchMode) => {
    const webSearchAvailable = !health.offlineMode && health.search.ready
    if (mode !== 'off' && !webSearchAvailable) return
    preferredSearchMode.current = mode
    saveSearchModePreference(mode)
    setSearchMode(mode)
  }, [health.offlineMode, health.search.ready])

  const startNewConversation = useCallback(async () => {
    if (creatingRef.current) return
    creatingRef.current = true
    historyVersion.current += 1
    const version = ++selectionVersion.current
    navigationController.current?.abort()
    const navigation = new AbortController()
    navigationController.current = navigation
    streamController.current?.abort()
    streamController.current = null
    setStreaming(false)
    setSidebarOpen(false)
    setCreating(true)
    try {
      const conversation = await createConversation(undefined, navigation.signal)
      if (version !== selectionVersion.current) return
      setActiveId(conversation.id)
      setActiveTitle(conversation.title || 'New conversation')
      setMessages(conversation.messages)
      setDraft('')
      upsertSummary(toSummary(conversation))
      writeStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY, conversation.id)
    } catch (error) {
      if (version !== selectionVersion.current || navigation.signal.aborted) return
      pushToast(getErrorMessage(error), 'danger')
    } finally {
      if (version === selectionVersion.current) {
        creatingRef.current = false
        setCreating(false)
      }
      if (navigationController.current === navigation) navigationController.current = null
    }
  }, [pushToast, upsertSummary])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        const target = event.target
        if (
          target instanceof HTMLElement &&
          (target.isContentEditable || target.matches('input, textarea, select'))
        ) return
        event.preventDefault()
        if (!creating) void startNewConversation()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [creating, startNewConversation])

  const handleRename = useCallback(async (id: string, title: string) => {
    historyVersion.current += 1
    const previous = conversations.find((conversation) => conversation.id === id)
    setConversations((current) =>
      current.map((conversation) => (conversation.id === id ? { ...conversation, title } : conversation)),
    )
    if (activeId === id) setActiveTitle(title)
    try {
      const updated = await renameConversation(id, title)
      upsertSummary(updated)
    } catch (error) {
      if (previous) upsertSummary(previous)
      if (activeId === id && previous) setActiveTitle(previous.title)
      pushToast(getErrorMessage(error), 'danger')
      throw error
    }
  }, [activeId, conversations, pushToast, upsertSummary])

  const confirmDelete = useCallback(async () => {
    if (!deleteTarget) return
    const target = deleteTarget
    const deletingActiveConversation = activeId === target.id
    const deleteOperationVersion = deletingActiveConversation
      ? ++selectionVersion.current
      : selectionVersion.current
    setDeleting(true)
    historyVersion.current += 1
    if (deletingActiveConversation) {
      navigationController.current?.abort()
      streamController.current?.abort()
    }
    try {
      await deleteConversation(target.id)
      historyVersion.current += 1
      setConversations((current) => current.filter((conversation) => conversation.id !== target.id))
      if (deletingActiveConversation && deleteOperationVersion === selectionVersion.current) {
        streamController.current = null
        setStreaming(false)
        setActiveId(null)
        setActiveTitle('New conversation')
        setMessages([])
        removeStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY)
      }
      setDeleteTarget(null)
      pushToast('Conversation deleted.')
    } catch (error) {
      pushToast(getErrorMessage(error), 'danger')
      if (deletingActiveConversation && deleteOperationVersion === selectionVersion.current) {
        await reconcileConversationAfterAbort(target.id, deleteOperationVersion, '', null)
      }
    } finally {
      setDeleting(false)
    }
  }, [activeId, deleteTarget, pushToast, reconcileConversationAfterAbort])

  const updateAssistant = useCallback((id: string, transform: (message: Message) => Message) => {
    setMessages((current) =>
      current.map((message) => (message.id === id ? transform(message) : message)),
    )
  }, [])

  const send = useCallback(async (prompt?: string) => {
    const content = (prompt ?? draft).trim()
    if (!content || streaming || creating || creatingRef.current || streamController.current) return
    if (content.length > MAX_MESSAGE_CHARS) {
      pushToast(`Messages can contain at most ${MAX_MESSAGE_CHARS.toLocaleString()} characters.`, 'danger')
      return
    }

    const operationVersion = ++selectionVersion.current
    let conversationId = activeId
    let title = activeTitle
    if (!conversationId) {
      historyVersion.current += 1
      navigationController.current?.abort()
      const navigation = new AbortController()
      navigationController.current = navigation
      creatingRef.current = true
      setCreating(true)
      try {
        const created = await createConversation(deriveTitle(content), navigation.signal)
        if (operationVersion !== selectionVersion.current) return
        conversationId = created.id
        title = created.title || deriveTitle(content)
        setActiveId(created.id)
        setActiveTitle(title)
        setMessages(created.messages)
        upsertSummary(toSummary(created))
        writeStoredValue(ACTIVE_CONVERSATION_STORAGE_KEY, created.id)
      } catch (error) {
        if (operationVersion !== selectionVersion.current || navigation.signal.aborted) return
        pushToast(getErrorMessage(error), 'danger')
        return
      } finally {
        if (operationVersion === selectionVersion.current) {
          creatingRef.current = false
          setCreating(false)
        }
        if (navigationController.current === navigation) navigationController.current = null
      }
    }

    if (operationVersion !== selectionVersion.current) return

    const now = new Date().toISOString()
    const userId = temporaryId('user')
    const assistantId = temporaryId('assistant')
    const userMessage: Message = {
      id: userId,
      role: 'user',
      content,
      created_at: now,
      sources: [],
    }
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      created_at: now,
      sources: [],
      pending: true,
    }

    setMessages((current) => [...current, userMessage, assistantMessage])
    setDraft('')
    setStreaming(true)
    const controller = new AbortController()
    streamController.current = controller
    let canonicalUserId: string | null = null
    let streamedContent = ''

    const handleEvent = (streamEvent: StreamEvent) => {
      if (operationVersion !== selectionVersion.current) return
      const data = asRecord(streamEvent.data)
      if (streamEvent.event === 'meta') {
        if (data.user_message) {
          const canonicalUser = normalizeMessage(data.user_message)
          canonicalUserId = canonicalUser.id
          setMessages((current) =>
            current.map((message) => (message.id === userId ? canonicalUser : message)),
          )
        }
        if (data.conversation) {
          const summary = normalizeConversationSummary(data.conversation)
          if (summary.id) {
            upsertSummary(summary)
            setActiveTitle(summary.title || title)
          }
        }
      }

      if (streamEvent.event === 'sources') {
        const values = Array.isArray(data.sources)
          ? data.sources
          : Array.isArray(streamEvent.data)
            ? streamEvent.data
            : []
        const searchError = asString(data.search_error)
        if (searchError) pushToast(searchError, 'danger')
        updateAssistant(assistantId, (message) => ({
          ...message,
          sources: values.map(normalizeSource),
        }))
      }

      if (streamEvent.event === 'delta') {
        const text = asString(data.text, asString(data.delta, asString(data.content, asString(streamEvent.data))))
        if (text) {
          streamedContent += text
          updateAssistant(assistantId, (message) => ({
            ...message,
            content: message.content + text,
          }))
        }
      }

      if (streamEvent.event === 'done') {
        if (data.message) {
          const finalMessage = normalizeMessage(data.message)
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? { ...finalMessage, pending: false } : message,
            ),
          )
        } else {
          updateAssistant(assistantId, (message) => ({ ...message, pending: false }))
        }
        if (data.conversation) {
          const summary = normalizeConversationSummary(data.conversation)
          if (summary.id) {
            upsertSummary(summary)
            setActiveTitle(summary.title || title)
          }
        }
      }

      if (streamEvent.event === 'error') {
        throw new ApiError(asString(data.message, 'The response could not be completed.'))
      }
    }

    try {
      const effectiveSearchMode = health.offlineMode || !health.search.ready ? 'off' : searchMode
      await streamMessage(conversationId, content, effectiveSearchMode, controller.signal, handleEvent)
      if (operationVersion === selectionVersion.current) {
        updateAssistant(assistantId, (message) => ({ ...message, pending: false }))
      }
    } catch (error) {
      if (operationVersion === selectionVersion.current) {
        updateAssistant(assistantId, (message) => ({
          ...message,
          pending: false,
          responseState: controller.signal.aborted ? 'stopped' : 'error',
        }))
        if (!controller.signal.aborted) pushToast(getErrorMessage(error), 'danger')
      }
    } finally {
      if (controller.signal.aborted && operationVersion === selectionVersion.current) {
        await reconcileConversationAfterAbort(
          conversationId,
          operationVersion,
          streamedContent,
          canonicalUserId,
          {
            userId,
            assistantId,
            content,
            createdAt: now,
            responseState: 'stopped',
          },
        )
      }
      if (streamController.current === controller) {
        streamController.current = null
        setStreaming(false)
      }
      void getHealth().then(setHealth)
      void refreshHistory(true)
    }
  }, [activeId, activeTitle, creating, draft, health.offlineMode, health.search.ready, pushToast, reconcileConversationAfterAbort, refreshHistory, searchMode, streaming, updateAssistant, upsertSummary])

  const stopStreaming = useCallback(() => {
    const controller = streamController.current
    if (!controller) return
    streamController.current = null
    setStreaming(false)
    controller.abort()
  }, [])

  const closeDeleteDialog = useCallback(() => {
    setDeleteTarget(null)
  }, [])

  const openDeleteDialog = useCallback((
    conversation: ConversationSummary,
    returnFocus: HTMLElement | null,
  ) => {
    deleteReturnFocus.current = returnFocus
    setDeleteTarget(conversation)
  }, [])

  const closeSidebar = useCallback(() => {
    setSidebarOpen(false)
  }, [])

  const retryHealth = useCallback(async () => {
    setHealth((current) => ({ ...current, status: 'loading' }))
    setHealth(await getHealth())
  }, [])

  return (
    <div className="app-shell">
      <Sidebar
        open={sidebarOpen}
        activeId={activeId}
        conversations={conversations}
        loading={historyLoading}
        creating={creating}
        health={health}
        theme={theme}
        onClose={closeSidebar}
        onNew={() => void startNewConversation()}
        onSelect={(id) => {
          if (id === activeId) {
            setSidebarOpen(false)
            return
          }
          void selectConversation(id)
        }}
        onRename={handleRename}
        onDelete={openDeleteDialog}
        onToggleTheme={toggleTheme}
      />

      <main className="chat-workspace">
        <header className="chat-header">
          <div className="chat-header-left">
            <button className="mobile-menu icon-button" type="button" onClick={() => setSidebarOpen(true)} aria-label="Open conversation history">
              <Menu size={20} />
            </button>
            <div className="chat-title">
              <strong>{activeId ? activeTitle : 'Sovereign AI iBuddy'}</strong>
              <span>{activeId ? 'Private conversation' : 'Private by default. Evidence before scale.'}</span>
            </div>
          </div>
          <div className="chat-header-actions">
            <button
              className={`header-status status-${health.status}`}
              type="button"
              onClick={() => void retryHealth()}
              title={health.detail || 'Refresh model status'}
              aria-label={`${healthLabel(health)}. Refresh model status.`}
            >
              <span className="status-dot" />
              <span>{healthLabel(health)}</span>
              {health.status !== 'online' && <RefreshCw size={13} />}
            </button>
            <button
              className="header-new-button"
              type="button"
              onClick={() => void startNewConversation()}
              disabled={creating}
              aria-keyshortcuts="Control+K Meta+K"
            >
              <Plus size={17} /> <span>New</span>
            </button>
          </div>
        </header>

        <div className={`conversation-scroll ${messages.length ? 'has-messages' : ''}`}>
          {conversationLoading ? (
            <div className="conversation-loading" aria-label="Loading conversation">
              <span className="loading-orb"><Sparkles size={18} /></span>
              <div><i /><i /><i /></div>
            </div>
          ) : messages.length ? (
            <div className="message-list" aria-live="polite" aria-busy={streaming}>
              {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
              <div ref={messagesEnd} />
            </div>
          ) : (
            <EmptyState onPrompt={(prompt) => void send(prompt)} disabled={creating || streaming} />
          )}
        </div>

        <Composer
          value={draft}
          mode={searchMode}
          streaming={streaming}
          offlineMode={health.offlineMode}
          webSearchReady={health.search.ready}
          searchProvider={health.search.provider}
          maxLength={MAX_MESSAGE_CHARS}
          disabled={conversationLoading || creating}
          onChange={setDraft}
          onModeChange={changeSearchMode}
          onSubmit={() => void send()}
          onStop={stopStreaming}
        />
      </main>

      <ConfirmDialog
        conversation={deleteTarget}
        deleting={deleting}
        onCancel={closeDeleteDialog}
        onConfirm={() => void confirmDelete()}
        returnFocus={deleteReturnFocus.current}
      />
      <ToastRegion toasts={toasts} dismiss={dismissToast} />
    </div>
  )
}
