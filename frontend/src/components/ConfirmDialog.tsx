import { useEffect, useRef } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import type { ConversationSummary } from '../types'

interface ConfirmDialogProps {
  conversation: ConversationSummary | null
  deleting: boolean
  onCancel: () => void
  onConfirm: () => void
  returnFocus: HTMLElement | null
}

function canReceiveFocus(element: HTMLElement | null): element is HTMLElement {
  return Boolean(element?.isConnected && !element.closest('[inert]'))
}

export function ConfirmDialog({
  conversation,
  deleting,
  onCancel,
  onConfirm,
  returnFocus,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const deletingRef = useRef(deleting)

  useEffect(() => {
    deletingRef.current = deleting
  }, [deleting])

  useEffect(() => {
    if (!conversation) return
    const previousFocus = canReceiveFocus(returnFocus)
      ? returnFocus
      : document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null
    cancelRef.current?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !deletingRef.current) onCancel()
      if (event.key !== 'Tab') return
      const focusable = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), [href], input:not(:disabled), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      )
      if (!focusable.length) {
        event.preventDefault()
        dialogRef.current?.focus()
        return
      }
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (!dialogRef.current?.contains(document.activeElement)) {
        event.preventDefault()
        first.focus()
      } else if (event.shiftKey && document.activeElement === first) {
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
      window.requestAnimationFrame(() => {
        const fallback = document.querySelector<HTMLElement>(
          '.history-more:not(:disabled), .new-chat-button:not(:disabled), .header-new-button:not(:disabled)',
        )
        const target = canReceiveFocus(previousFocus) ? previousFocus : fallback
        if (canReceiveFocus(target)) target.focus()
      })
    }
  }, [conversation, onCancel, returnFocus])

  useEffect(() => {
    if (deleting) dialogRef.current?.focus()
  }, [deleting])

  if (!conversation) return null

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.currentTarget === event.target && !deleting) onCancel()
    }}>
      <div
        ref={dialogRef}
        className="confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-title"
        aria-describedby="delete-description"
        aria-busy={deleting}
        tabIndex={-1}
      >
        <button className="dialog-close" type="button" onClick={onCancel} disabled={deleting} aria-label="Close dialog">
          <X size={18} />
        </button>
        <span className="dialog-icon"><AlertTriangle size={20} /></span>
        <h2 id="delete-title">Delete conversation?</h2>
        <p id="delete-description">
          “{conversation.title}” and its messages will be permanently removed.
        </p>
        <div className="dialog-actions">
          <button ref={cancelRef} className="button-secondary" type="button" onClick={onCancel} disabled={deleting}>Cancel</button>
          <button className="button-danger" type="button" onClick={onConfirm} disabled={deleting}>
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
        <span className="sr-only" role="status" aria-live="polite">
          {deleting ? 'Deleting conversation' : ''}
        </span>
      </div>
    </div>
  )
}
