import { FormEvent, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import {
  Check,
  MessageSquareText,
  Moon,
  MoreHorizontal,
  Pencil,
  Plus,
  Search,
  Sun,
  Trash2,
  X,
} from 'lucide-react'
import type { ConversationSummary, HealthStatus } from '../types'
import type { Theme } from '../hooks/useTheme'
import { formatRelativeTime, groupLabel } from '../lib/utils'
import { Brand } from './Brand'

interface SidebarProps {
  open: boolean
  activeId: string | null
  conversations: ConversationSummary[]
  loading: boolean
  creating: boolean
  health: HealthStatus
  theme: Theme
  onClose: () => void
  onNew: () => void
  onSelect: (id: string) => void
  onRename: (id: string, title: string) => Promise<void>
  onDelete: (conversation: ConversationSummary, returnFocus: HTMLElement | null) => void
  onToggleTheme: () => void
}

interface HistoryRowProps {
  conversation: ConversationSummary
  active: boolean
  disabled: boolean
  menuOpen: boolean
  onMenuToggle: () => void
  onSelect: () => void
  onRename: (title: string) => Promise<void>
  onDelete: (returnFocus: HTMLElement | null) => void
}

function modelStatusLabel(health: HealthStatus): string {
  if (health.localModel) {
    if (health.state === 'installing' || health.state === 'downloading') return 'Installing'
    if (health.state === 'starting' || health.state === 'loading') return 'Loading into memory'
    if (health.state === 'idle' || health.state === 'configured') {
      return 'Installed · loads on first message'
    }
    if (health.state === 'ready' || health.state === 'operational' || health.status === 'online') {
      return 'Ready offline'
    }
    if (
      health.state === 'missing' ||
      health.state === 'missing_assets' ||
      health.state === 'not_installed' ||
      health.state === 'unconfigured'
    ) return 'Model assets missing'
    if (health.state === 'error') return 'Could not start'
    if (health.state === 'closed') return 'Stopped'
    return health.status === 'loading' ? 'Loading' : 'Unavailable'
  }
  if (health.state === 'configured' || health.state === 'idle') return 'Loads on first message'
  if (health.status === 'online') return 'Ready'
  if (health.status === 'loading') return 'Connecting'
  return 'Unavailable'
}

function HistoryRow({
  conversation,
  active,
  disabled,
  menuOpen,
  onMenuToggle,
  onSelect,
  onRename,
  onDelete,
}: HistoryRowProps) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(conversation.title)
  const [saving, setSaving] = useState(false)
  const actionsButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!editing) setTitle(conversation.title)
  }, [conversation.title, editing])

  useEffect(() => {
    if (disabled && editing) {
      setTitle(conversation.title)
      setEditing(false)
    }
  }, [conversation.title, disabled, editing])

  const saveTitle = async (event: FormEvent) => {
    event.preventDefault()
    const nextTitle = title.trim()
    if (!nextTitle || nextTitle === conversation.title) {
      setTitle(conversation.title)
      setEditing(false)
      return
    }
    setSaving(true)
    try {
      await onRename(nextTitle)
      setEditing(false)
    } catch {
      setTitle(conversation.title)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={`history-row ${active ? 'is-active' : ''}`}>
      {editing ? (
        <form className="history-edit" onSubmit={saveTitle}>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            aria-label="Conversation title"
            maxLength={100}
            autoFocus
            onKeyDown={(event) => {
              if (event.key === 'Escape') {
                setTitle(conversation.title)
                setEditing(false)
              }
            }}
          />
          <button type="submit" aria-label="Save title" disabled={saving || !title.trim()}>
            <Check size={15} />
          </button>
          <button
            type="button"
            aria-label="Cancel rename"
            onClick={() => {
              setTitle(conversation.title)
              setEditing(false)
            }}
          >
            <X size={15} />
          </button>
        </form>
      ) : (
        <>
          <button
            className="history-main"
            type="button"
            onClick={onSelect}
            disabled={disabled}
            aria-current={active ? 'page' : undefined}
          >
            <MessageSquareText size={16} aria-hidden="true" />
            <span className="history-copy">
              <span className="history-title">{conversation.title || 'New conversation'}</span>
              <span className="history-meta">
                {conversation.message_count !== undefined && `${conversation.message_count} messages · `}
                {formatRelativeTime(conversation.updated_at)}
              </span>
            </span>
          </button>
          <button
            ref={actionsButtonRef}
            className="history-more"
            type="button"
            aria-label={`Actions for ${conversation.title}`}
            aria-expanded={menuOpen}
            disabled={disabled}
            onClick={(event) => {
              event.stopPropagation()
              onMenuToggle()
            }}
          >
            <MoreHorizontal size={17} />
          </button>
          {menuOpen && (
            <div className="history-menu">
              <button
                type="button"
                disabled={disabled}
                onClick={() => {
                  setTitle(conversation.title)
                  setEditing(true)
                  onMenuToggle()
                }}
              >
                <Pencil size={14} /> Rename
              </button>
              <button
                className="danger-action"
                type="button"
                onClick={() => onDelete(actionsButtonRef.current)}
                disabled={disabled}
              >
                <Trash2 size={14} /> Delete
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export function Sidebar({
  open,
  activeId,
  conversations,
  loading,
  creating,
  health,
  theme,
  onClose,
  onNew,
  onSelect,
  onRename,
  onDelete,
  onToggleTheme,
}: SidebarProps) {
  const [query, setQuery] = useState('')
  const [openMenu, setOpenMenu] = useState<string | null>(null)
  const [mobile, setMobile] = useState(() => window.matchMedia('(max-width: 800px)').matches)
  const sidebarRef = useRef<HTMLElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const modelStatus = modelStatusLabel(health)

  useEffect(() => {
    const media = window.matchMedia('(max-width: 800px)')
    const update = () => setMobile(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useLayoutEffect(() => {
    const sidebar = sidebarRef.current
    if (!sidebar) return
    if (mobile && !open) sidebar.setAttribute('inert', '')
    else sidebar.removeAttribute('inert')
  }, [mobile, open])

  useEffect(() => {
    if (!mobile || !open) return
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
    closeButtonRef.current?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (!sidebarRef.current?.contains(document.activeElement)) return
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab') return
      const focusable = Array.from(
        sidebarRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), [href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      )
      if (!focusable.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      previousFocus?.focus()
    }
  }, [mobile, onClose, open])

  useEffect(() => {
    if (creating) setOpenMenu(null)
  }, [creating])

  const grouped = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase()
    const filtered = conversations.filter((conversation) =>
      conversation.title.toLocaleLowerCase().includes(normalizedQuery),
    )
    const groups = new Map<string, ConversationSummary[]>()
    for (const conversation of filtered) {
      const label = groupLabel(conversation.updated_at)
      groups.set(label, [...(groups.get(label) ?? []), conversation])
    }
    return [...groups.entries()]
  }, [conversations, query])

  return (
    <>
      <button
        className={`sidebar-scrim ${open ? 'is-visible' : ''}`}
        type="button"
        tabIndex={open ? 0 : -1}
        aria-label="Close conversation sidebar"
        onClick={onClose}
      />
      <aside
        ref={sidebarRef}
        className={`sidebar ${open ? 'is-open' : ''}`}
        aria-label="Conversation history"
        aria-hidden={mobile && !open ? true : undefined}
        aria-modal={mobile && open ? true : undefined}
        role={mobile ? 'dialog' : undefined}
      >
        <div className="sidebar-header">
          <Brand />
          <button ref={closeButtonRef} className="mobile-only icon-button" type="button" onClick={onClose} aria-label="Close sidebar">
            <X size={19} />
          </button>
        </div>

        <button
          className="new-chat-button"
          type="button"
          onClick={onNew}
          disabled={creating}
          aria-keyshortcuts="Control+K Meta+K"
        >
          <span><Plus size={18} /> New conversation</span>
          <kbd>Ctrl K</kbd>
        </button>

        <label className="history-search">
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Search conversation history</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search history"
          />
          {query && (
            <button type="button" onClick={() => setQuery('')} aria-label="Clear history search">
              <X size={14} />
            </button>
          )}
        </label>

        <div className="history-list" onScroll={() => setOpenMenu(null)}>
          {loading ? (
            <div className="history-skeletons" aria-label="Loading conversation history">
              {Array.from({ length: 5 }, (_, index) => <span key={index} />)}
            </div>
          ) : grouped.length ? (
            grouped.map(([label, items]) => (
              <section className="history-group" key={label}>
                <h2>{label}</h2>
                {items.map((conversation) => (
                  <HistoryRow
                    key={conversation.id}
                    conversation={conversation}
                    active={conversation.id === activeId}
                    disabled={creating}
                    menuOpen={openMenu === conversation.id}
                    onMenuToggle={() =>
                      setOpenMenu((current) => (current === conversation.id ? null : conversation.id))
                    }
                    onSelect={() => {
                      setOpenMenu(null)
                      onSelect(conversation.id)
                    }}
                    onRename={(title) => onRename(conversation.id, title)}
                    onDelete={(returnFocus) => {
                      setOpenMenu(null)
                      onDelete(conversation, returnFocus)
                    }}
                  />
                ))}
              </section>
            ))
          ) : (
            <div className="history-empty">
              <MessageSquareText size={22} />
              <p>{query ? 'No matching conversations' : 'Your conversations will appear here'}</p>
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          <div
            className="model-status"
            title={health.detail || health.model}
            role="status"
            aria-live="polite"
            aria-label={`${health.localModel ? 'Local model' : health.model}: ${modelStatus}`}
          >
            <span className={`status-dot status-${health.status}`} />
            <span>
              <strong>{health.localModel ? 'Local model' : health.model}</strong>
              <small>{modelStatus}</small>
            </span>
          </div>
          <button className="theme-button" type="button" onClick={onToggleTheme} aria-label={`Use ${theme === 'light' ? 'dark' : 'light'} theme`}>
            {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
          </button>
        </div>
      </aside>
    </>
  )
}
