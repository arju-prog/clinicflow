import { useEffect } from 'react';
import { STATUS_LABELS, initials } from '../format.js';

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{STATUS_LABELS[status] ?? status}</span>;
}

export function Avatar({ name, tone = 'teal' }) {
  return (
    <span className={`avatar avatar-${tone}`} aria-hidden="true">
      {initials(name)}
    </span>
  );
}

export function Modal({ title, onClose, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <header className="modal-header">
          <h2 id="modal-title">{title}</h2>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

export function EmptyState({ title, hint, action }) {
  return (
    <div className="empty-state">
      <p className="empty-title">{title}</p>
      {hint && <p className="muted">{hint}</p>}
      {action}
    </div>
  );
}

export function Toasts({ toasts, onDismiss }) {
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.kind}`} onClick={() => onDismiss(t.id)}>
          {t.message}
        </div>
      ))}
    </div>
  );
}

export function Field({ label, children, wide }) {
  return (
    <label className={`field ${wide ? 'field-wide' : ''}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}
