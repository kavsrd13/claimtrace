import React from 'react'

interface LoadingStateProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export default function LoadingState({
  message,
  size = 'md',
}: LoadingStateProps) {
  const spinnerClass = `spinner${
    size === 'sm' ? ' spinner-sm' : size === 'lg' ? ' spinner-lg' : ''
  }`

  return (
    <div
      className="loading-container"
      role="status"
      aria-live="polite"
      aria-label={message ?? 'Loading…'}
    >
      <div className={spinnerClass} aria-hidden="true" />
      {message && <p className="loading-message">{message}</p>}
    </div>
  )
}
