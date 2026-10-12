import { useEffect, useRef } from 'react'
import Icon from './Icon.jsx'

function useEscape(onClose) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
}

export function Drawer({ title, kicker, onClose, children }) {
  useEscape(onClose)
  const panel = useRef(null)
  useEffect(() => {
    panel.current?.querySelector('input, select, textarea')?.focus()
  }, [])
  return (
    <div className="scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={title} ref={panel}>
        <header className="drawer__head">
          <div>
            {kicker && <p className="kicker">{kicker}</p>}
            <h2>{title}</h2>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="close" />
          </button>
        </header>
        <div className="drawer__body">{children}</div>
      </aside>
    </div>
  )
}

export function ConfirmDialog({ title, message, confirmLabel = 'Delete', onConfirm, onCancel, busy }) {
  useEscape(onCancel)
  return (
    <div className="scrim scrim--center" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <div className="confirm" role="alertdialog" aria-modal="true" aria-label={title}>
        <h2>{title}</h2>
        <p>{message}</p>
        <div className="confirm__actions">
          <button className="btn btn--ghost" onClick={onCancel} disabled={busy}>
            Keep it
          </button>
          <button className="btn btn--danger" onClick={onConfirm} disabled={busy}>
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Toasts({ toasts, onDismiss }) {
  return (
    <div className="toasts" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast--${t.kind}`}>
          <Icon name={t.kind === 'error' ? 'alert' : 'check'} size={18} />
          <span>{t.message}</span>
          <button className="icon-btn icon-btn--sm" onClick={() => onDismiss(t.id)} aria-label="Dismiss">
            <Icon name="close" size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
