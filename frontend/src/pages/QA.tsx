import React, {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, AskResult, Citation } from '../api'
import { CitationList } from '../components/ClaimTrace'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'

/* ============================================================
   Types
   ============================================================ */
interface UserMessage {
  role: 'user'
  id: string
  text: string
}

interface AIMessage {
  role: 'ai'
  id: string
  answer: string
  citations: Citation[]
  is_supported: boolean
}

interface ErrorMessage {
  role: 'error'
  id: string
  message: string
  statusCode?: number
}

type Message = UserMessage | AIMessage | ErrorMessage

let _msgId = 0
function nextId() {
  return String(++_msgId)
}

/* ============================================================
   QA Page
   ============================================================ */
export default function QA() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [initError, setInitError] = useState<ApiError | null>(null)
  const [initLoading, setInitLoading] = useState(true)

  const panelRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Validate session has documents
  useEffect(() => {
    if (!sessionId) return
    setInitLoading(true)
    api.documents
      .list(sessionId)
      .then((docs) => {
        if (docs.length === 0) {
          setInitError(new ApiError(400, 'No documents uploaded. Upload at least one document before asking questions.'))
        }
        setInitLoading(false)
      })
      .catch((err) => {
        setInitError(err instanceof ApiError ? err : new ApiError(500, String(err)))
        setInitLoading(false)
      })
  }, [sessionId])

  // Scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isAsking])

  const sendQuestion = async () => {
    const trimmed = question.trim()
    if (!trimmed || isAsking || !sessionId) return

    const userMsg: UserMessage = { role: 'user', id: nextId(), text: trimmed }
    setMessages((prev) => [...prev, userMsg])
    setQuestion('')
    setIsAsking(true)

    // Auto-resize textarea back to single line
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      const result: AskResult = await api.qa.ask(sessionId, trimmed)
      const aiMsg: AIMessage = {
        role: 'ai',
        id: nextId(),
        answer: result.answer,
        citations: result.citations,
        is_supported: result.is_supported,
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch (err) {
      let message = 'Failed to get a response. Please try again.'
      let statusCode: number | undefined

      if (err instanceof ApiError) {
        statusCode = err.status
        if (err.status === 422) {
          message = 'Your question was flagged for potential injection. Please rephrase it.'
        } else if (err.status === 503) {
          message = 'The AI service is not configured or unavailable. Please contact the administrator.'
        } else {
          message = err.message
        }
      }

      const errMsg: ErrorMessage = {
        role: 'error',
        id: nextId(),
        message,
        statusCode,
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setIsAsking(false)
      // Refocus textarea
      textareaRef.current?.focus()
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    sendQuestion()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendQuestion()
    }
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value)
    // Auto-resize
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  /* ---- Loading / error states for init ---- */
  if (initLoading) {
    return (
      <div className="container page-content">
        <LoadingState message="Loading session…" />
      </div>
    )
  }

  if (initError) {
    return (
      <div className="container page-content">
        <ErrorState
          title="Cannot Start Q&A"
          message={initError.message}
          statusCode={initError.status === 400 ? undefined : initError.status}
        />
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <Link to="/" className="btn btn-primary">
            Upload Documents
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="qa-page">
      {/* Header */}
      <div className="qa-header">
        <Link
          to={sessionId ? `/session/${sessionId}/compare` : '/'}
          className="back-link"
        >
          ← Back to Comparison
        </Link>
        <h1 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Document Q&A</h1>
        <span className="text-muted text-sm">
          Ask questions grounded in your uploaded documents.
        </span>
      </div>

      {/* Messages panel */}
      <div className="qa-panel" ref={panelRef} aria-live="polite" aria-label="Chat messages">
        <div className="qa-messages">
          {messages.length === 0 && !isAsking && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                flex: 1,
                minHeight: '200px',
                gap: '0.75rem',
                textAlign: 'center',
              }}
            >
              <span style={{ fontSize: '2.5rem' }} aria-hidden="true">💬</span>
              <p className="text-secondary">
                Ask a question about your uploaded documents.
              </p>
              <p className="text-muted text-sm">
                Press <kbd style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', padding: '0.125rem 0.375rem', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>Enter</kbd> to send. <kbd style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', padding: '0.125rem 0.375rem', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>Shift+Enter</kbd> for a new line.
              </p>
            </div>
          )}

          {messages.map((msg) => {
            if (msg.role === 'user') {
              return (
                <div key={msg.id} className="message message-user">
                  <div className="message-bubble">{msg.text}</div>
                </div>
              )
            }

            if (msg.role === 'ai') {
              return (
                <div
                  key={msg.id}
                  className={`message message-ai${!msg.is_supported ? ' unsupported' : ''}`}
                >
                  <div className="message-bubble">
                    <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                      {msg.answer}
                    </p>
                    {!msg.is_supported && (
                      <p className="message-unsupported-badge">
                        ⚠️ This answer may not be fully supported by the documents.
                      </p>
                    )}
                    {msg.citations.length > 0 && (
                      <CitationList citations={msg.citations} />
                    )}
                  </div>
                  <span className="message-meta">AI · Grounded in your documents</span>
                </div>
              )
            }

            if (msg.role === 'error') {
              return (
                <div key={msg.id} className="message message-ai">
                  <div
                    className="message-bubble"
                    style={{
                      borderColor: 'var(--color-danger)',
                      background: 'var(--color-danger-light)',
                    }}
                  >
                    <p style={{ margin: 0, color: 'var(--color-danger)', fontWeight: 600 }}>
                      ⚠️ Error
                    </p>
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem', color: 'var(--color-text)' }}>
                      {msg.message}
                    </p>
                    {msg.statusCode && (
                      <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        HTTP {msg.statusCode}
                      </p>
                    )}
                  </div>
                </div>
              )
            }

            return null
          })}

          {isAsking && (
            <div className="qa-thinking" aria-label="AI is thinking" role="status">
              <div className="typing-dots" aria-hidden="true">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
              <span>Thinking…</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="qa-input-area">
        <form onSubmit={handleSubmit} className="qa-input-row" noValidate>
          <label htmlFor="qa-input" className="sr-only">
            Ask a question about your documents
          </label>
          <textarea
            id="qa-input"
            ref={textareaRef}
            className="qa-textarea"
            value={question}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents…"
            disabled={isAsking}
            rows={1}
            aria-label="Question input"
            aria-describedby="qa-hint"
          />
          <button
            type="submit"
            className="btn btn-primary qa-send-btn"
            disabled={isAsking || !question.trim()}
            aria-label="Send question"
            title="Send (Enter)"
          >
            {isAsking ? (
              <div className="spinner spinner-sm" aria-hidden="true" />
            ) : (
              <span aria-hidden="true">↑</span>
            )}
          </button>
        </form>
        <p
          id="qa-hint"
          className="text-muted text-xs"
          style={{ textAlign: 'center', marginTop: '0.375rem' }}
        >
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
