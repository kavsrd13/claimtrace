import React from 'react'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  statusCode?: number
}

function getIcon(statusCode?: number): string {
  if (statusCode === 404) return '🔍'
  if (statusCode === 410) return '⏰'
  if (statusCode === 503) return '🔌'
  return '⚠️'
}

function getDefaultTitle(statusCode?: number): string {
  if (statusCode === 404) return 'Not Found'
  if (statusCode === 410) return 'Session Expired'
  if (statusCode === 503) return 'Service Unavailable'
  return 'Something went wrong'
}

export default function ErrorState({
  title,
  message,
  onRetry,
  statusCode,
}: ErrorStateProps) {
  const icon = getIcon(statusCode)
  const displayTitle = title ?? getDefaultTitle(statusCode)

  return (
    <div className="error-state" role="alert" aria-live="assertive">
      <div className="error-state-icon" aria-hidden="true">
        {icon}
      </div>
      <h2 className="error-state-title">{displayTitle}</h2>
      {statusCode && (
        <span className="error-state-code">HTTP {statusCode}</span>
      )}
      <p className="error-state-message">{message}</p>
      {onRetry && (
        <div className="error-state-action">
          <button
            className="btn btn-primary"
            onClick={onRetry}
            type="button"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  )
}
