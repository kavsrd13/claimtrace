import React, {
  useEffect,
  useState,
} from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { api, ApiError } from './api'
import ErrorState from './components/ErrorState'
import LoadingState from './components/LoadingState'
import { SessionProvider, useSession } from './context/SessionContext'
import Compare from './pages/Compare'
import QA from './pages/QA'
import Upload from './pages/Upload'

/* ============================================================
   Navbar
   ============================================================ */
function Navbar() {
  const { session, sessionId, clearSession } = useSession()

  const handleDeleteSession = async () => {
    if (!sessionId) return
    if (!window.confirm('Delete this session? All uploaded documents will be removed.')) return
    try {
      await api.sessions.delete(sessionId)
    } catch {
      // best-effort
    } finally {
      clearSession()
    }
  }

  return (
    <nav className="navbar" aria-label="Main navigation">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand">
          🔍 ClaimTrace
        </Link>

        <div className="navbar-session">
          {session && !session.is_expired && (
            <>
              <span className="text-sm text-secondary">
                {session.document_count} doc{session.document_count !== 1 ? 's' : ''}
              </span>
              <span className="navbar-session-id" title={session.id}>
                {session.id.slice(0, 8)}…
              </span>
            </>
          )}
          {session?.is_expired && (
            <span className="tag" style={{ color: 'var(--color-danger)' }}>
              ⏰ Expired
            </span>
          )}
        </div>

        <div className="navbar-nav">
          {sessionId && session && !session.is_expired && (
            <>
              <Link to={`/session/${sessionId}/compare`} className="btn btn-ghost btn-sm">
                Compare
              </Link>
              <Link to={`/session/${sessionId}/qa`} className="btn btn-ghost btn-sm">
                Q&amp;A
              </Link>
              <button
                className="btn btn-danger btn-sm"
                onClick={handleDeleteSession}
                title="Delete session"
              >
                Delete
              </button>
            </>
          )}
          {!sessionId && (
            <Link to="/" className="btn btn-primary btn-sm">
              New Session
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}

/* ============================================================
   Session Guard — wraps routes that require a valid session
   ============================================================ */
function SessionRoute({ children }: { children: React.ReactNode }) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>()
  const { sessionId, setSessionId, session } = useSession()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  // Sync URL session ID into context if different
  useEffect(() => {
    if (paramSessionId && paramSessionId !== sessionId) {
      setLoading(true)
      api.sessions
        .get(paramSessionId)
        .then(() => {
          setSessionId(paramSessionId)
          setLoading(false)
        })
        .catch((err) => {
          setError(err instanceof ApiError ? err : new ApiError(500, String(err)))
          setLoading(false)
        })
    }
  }, [paramSessionId, sessionId, setSessionId])

  if (loading) return <LoadingState message="Loading session…" />

  if (error) {
    if (error.status === 404) {
      return (
        <div className="container page-content">
          <ErrorState
            statusCode={404}
            title="Session Not Found"
            message="This session does not exist or has been deleted."
            onRetry={undefined}
          />
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <Link to="/" className="btn btn-primary">
              Start New Session
            </Link>
          </div>
        </div>
      )
    }
    if (error.status === 410) {
      return (
        <div className="container page-content">
          <ErrorState
            statusCode={410}
            title="Session Expired"
            message="This session has expired. Sessions are automatically removed after 24 hours."
            onRetry={undefined}
          />
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <Link to="/" className="btn btn-primary">
              Start New Session
            </Link>
          </div>
        </div>
      )
    }
    return (
      <div className="container page-content">
        <ErrorState message={error.message} onRetry={() => window.location.reload()} />
      </div>
    )
  }

  if (session?.is_expired) {
    return (
      <div className="container page-content">
        <ErrorState
          statusCode={410}
          title="Session Expired"
          message="This session has expired. Start a new one to continue."
        />
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <Link to="/" className="btn btn-primary">
            Start New Session
          </Link>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

/* ============================================================
   App
   ============================================================ */
export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <div role="status" aria-live="polite" className="sr-only" id="a11y-announcer">
          ClaimTrace active
        </div>
        <Navbar />
        <main id="main-content" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route
              path="/session/:sessionId/compare"
              element={
                <SessionRoute>
                  <Compare />
                </SessionRoute>
              }
            />
            <Route
              path="/session/:sessionId/qa"
              element={
                <SessionRoute>
                  <QA />
                </SessionRoute>
              }
            />
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </SessionProvider>
    </BrowserRouter>
  )
}
