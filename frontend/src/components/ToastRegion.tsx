import { AlertCircle, CheckCircle2, X } from 'lucide-react'
import type { ToastMessage } from '../types'

interface ToastRegionProps {
  toasts: ToastMessage[]
  dismiss: (id: number) => void
}

export function ToastRegion({ toasts, dismiss }: ToastRegionProps) {
  return (
    <div className="toast-region" role="status" aria-live="polite" aria-atomic="false">
      {toasts.map((toast) => (
        <div className={`toast ${toast.tone === 'danger' ? 'toast-danger' : ''}`} key={toast.id}>
          {toast.tone === 'danger' ? (
            <AlertCircle size={17} aria-hidden="true" />
          ) : (
            <CheckCircle2 size={17} aria-hidden="true" />
          )}
          <span>{toast.message}</span>
          <button type="button" onClick={() => dismiss(toast.id)} aria-label="Dismiss notification">
            <X size={15} />
          </button>
        </div>
      ))}
    </div>
  )
}
