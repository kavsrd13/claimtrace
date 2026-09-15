import React, { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { Citation } from '../api'

/* ============================================================
   CitationBadge – a single keyboard-accessible citation button
   ============================================================ */
interface CitationBadgeProps {
  citation: Citation
  index: number
}

export function CitationBadge({ citation, index }: CitationBadgeProps) {
  const [isOpen, setIsOpen] = useState(false)
  const badgeRef = useRef<HTMLButtonElement>(null)
  const panelId = useId()
  const labelId = useId()

  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => {
    setIsOpen(false)
    // Return focus to badge on close
    badgeRef.current?.focus()
  }, [])

  // Close on Escape key from anywhere while open
  useEffect(() => {
    if (!isOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        close()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, close])

  // Close when clicking outside
  useEffect(() => {
    if (!isOpen) return
    const handlePointerDown = (e: PointerEvent) => {
      const el = badgeRef.current
      if (el && !el.parentElement?.contains(e.target as Node)) {
        close()
      }
    }
    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [isOpen, close])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      if (isOpen) {
        close()
      } else {
        open()
      }
    }
    if (e.key === 'Escape' && isOpen) {
      e.preventDefault()
      close()
    }
  }

  const scorePercent = Math.round(citation.score * 100)

  return (
    <span className="citation-wrapper">
      <button
        ref={badgeRef}
        className={`citation-badge${isOpen ? ' is-open' : ''}`}
        onClick={() => (isOpen ? close() : open())}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        aria-label={`Citation ${index}: ${citation.source_label}`}
        aria-expanded={isOpen}
        aria-controls={isOpen ? panelId : undefined}
        aria-haspopup="dialog"
        title={`Citation [${index}]: ${citation.source_label}`}
        type="button"
      >
        {index}
      </button>

      {isOpen && (
        <div
          id={panelId}
          role="dialog"
          aria-modal="true"
          aria-labelledby={labelId}
          className="citation-panel"
        >
          <div className="citation-panel-label">
            <span id={labelId}>{citation.source_label}</span>
            <button
              className="citation-panel-close"
              onClick={close}
              aria-label="Close citation"
              type="button"
            >
              ✕
            </button>
          </div>
          <p className="citation-panel-text">{citation.text}</p>
          <p className="citation-panel-score">Relevance score: {scorePercent}%</p>
        </div>
      )}
    </span>
  )
}

/* ============================================================
   CitationList – renders all citations below an AI message
   ============================================================ */
interface CitationListProps {
  citations: Citation[]
}

export function CitationList({ citations }: CitationListProps) {
  if (!citations || citations.length === 0) return null

  return (
    <div className="citation-list" aria-label="Citations">
      <p className="citation-list-title">Sources</p>
      {citations.map((citation, i) => (
        <div key={i} className="citation-list-item">
          <span className="citation-list-badge">
            <CitationBadge citation={citation} index={i + 1} />
          </span>
          <span>
            <span className="citation-list-source">{citation.source_label}</span>
            <span className="citation-list-text">{citation.text}</span>
          </span>
        </div>
      ))}
    </div>
  )
}
