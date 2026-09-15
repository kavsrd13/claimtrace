import React from 'react'

interface EmptyStateProps {
  icon?: string // emoji
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
}

export default function EmptyState({
  icon = '📂',
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true">
        {icon}
      </div>
      <h2 className="empty-state-title">{title}</h2>
      {description && (
        <p className="empty-state-description">{description}</p>
      )}
      {action && (
        <div className="empty-state-action">
          <button
            className="btn btn-primary"
            onClick={action.onClick}
            type="button"
          >
            {action.label}
          </button>
        </div>
      )}
    </div>
  )
}
