import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError, ClaimItem, CompareResult, DocumentInfo } from '../api'
import { CitationBadge } from '../components/ClaimTrace'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'

/* ============================================================
   Verdict Badge
   ============================================================ */
const VERDICT_LABELS: Record<ClaimItem['verdict'], string> = {
  agree: '✅ Agree',
  disagree: '❌ Disagree',
  only_in_a: '📘 Only in A',
  only_in_b: '📙 Only in B',
}

function VerdictBadge({ verdict }: { verdict: ClaimItem['verdict'] }) {
  return (
    <span className={`verdict-badge verdict-${verdict}`} aria-label={`Verdict: ${verdict}`}>
      {VERDICT_LABELS[verdict]}
    </span>
  )
}

/* ============================================================
   Compare Page
   ============================================================ */
type PageState =
  | { kind: 'loading-docs' }
  | { kind: 'no-docs' }
  | { kind: 'one-doc' }
  | { kind: 'comparing' }
  | { kind: 'done'; result: CompareResult }
  | { kind: 'error'; error: ApiError | Error }

export default function Compare() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [state, setState] = useState<PageState>({ kind: 'loading-docs' })
  const [docs, setDocs] = useState<DocumentInfo[]>([])

  const loadAndCompare = async (sid: string) => {
    setState({ kind: 'loading-docs' })
    try {
      const documents = await api.documents.list(sid)
      setDocs(documents)

      if (documents.length === 0) {
        setState({ kind: 'no-docs' })
        return
      }

      if (documents.length < 2) {
        setState({ kind: 'one-doc' })
        return
      }

      // Both docs present — run comparison
      setState({ kind: 'comparing' })
      const result = await api.compare.run(sid)
      setState({ kind: 'done', result })
    } catch (err) {
      setState({
        kind: 'error',
        error: err instanceof Error ? err : new Error(String(err)),
      })
    }
  }

  useEffect(() => {
    if (sessionId) {
      loadAndCompare(sessionId)
    }
  }, [sessionId])

  const handleRetry = () => {
    if (sessionId) loadAndCompare(sessionId)
  }

  /* ---- render states ---- */
  if (state.kind === 'loading-docs') {
    return (
      <div className="container page-content">
        <LoadingState message="Loading documents…" />
      </div>
    )
  }

  if (state.kind === 'comparing') {
    return (
      <div className="container page-content">
        <LoadingState size="lg" message="AI is comparing your documents. This may take a moment…" />
      </div>
    )
  }

  if (state.kind === 'no-docs') {
    return (
      <div className="container page-content">
        <EmptyState
          icon="📂"
          title="No Documents Uploaded"
          description="Upload two documents to run a comparison."
          action={{ label: 'Upload Documents', onClick: () => window.history.back() }}
        />
      </div>
    )
  }

  if (state.kind === 'one-doc') {
    return (
      <div className="container page-content">
        <EmptyState
          icon="📄"
          title="Only One Document Found"
          description="You need two documents to compare. Please upload a second document."
          action={{ label: '← Back to Upload', onClick: () => window.history.back() }}
        />
      </div>
    )
  }

  if (state.kind === 'error') {
    const err = state.error
    const status = err instanceof ApiError ? err.status : undefined
    return (
      <div className="container page-content">
        <ErrorState
          title="Comparison Failed"
          message={err.message}
          statusCode={status}
          onRetry={handleRetry}
        />
      </div>
    )
  }

  /* ---- done ---- */
  const { result } = state as { kind: 'done'; result: CompareResult }

  return (
    <div className="container page-content">
      {/* Header */}
      <div className="page-header">
        <div>
          <Link to="/" className="back-link">← Upload New</Link>
          <h1 className="page-title" style={{ marginTop: '0.25rem' }}>
            Comparison Results
          </h1>
        </div>
        <div className="page-actions">
          {sessionId && (
            <Link to={`/session/${sessionId}/qa`} className="btn btn-primary">
              💬 Ask Questions
            </Link>
          )}
          <button
            className="btn btn-ghost"
            onClick={handleRetry}
            type="button"
          >
            ↺ Re-run
          </button>
        </div>
      </div>

      {/* Summary */}
      {result.summary && (
        <div className="card mb-3">
          <div className="card-header">
            <span className="card-title">🗒️ Summary</span>
          </div>
          <div className="card-body">
            <p className="summary-text">{result.summary}</p>
          </div>
        </div>
      )}

      {/* Side-by-side panels */}
      <div className="diff-viewer mb-3">
        {/* Doc A panel */}
        <div className="diff-panel diff-panel-a">
          <div className="diff-panel-header">📘 {result.doc_a_name || 'Document A'}</div>
          <div className="diff-panel-body">
            {result.similarities && result.similarities.length > 0 ? (
              <>
                <p className="diff-section-title">Similarities with Doc B</p>
                <ul className="similarities-list">
                  {result.similarities.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="text-muted text-sm">No similarities identified.</p>
            )}
          </div>
        </div>

        {/* Doc B panel */}
        <div className="diff-panel diff-panel-b">
          <div className="diff-panel-header">📗 {result.doc_b_name || 'Document B'}</div>
          <div className="diff-panel-body">
            <p className="diff-section-title">Compared against Doc A</p>
            {docs.find((d) => d.slot === 1) ? (
              <p className="text-secondary text-sm">
                Filename: <strong>{docs.find((d) => d.slot === 1)?.filename}</strong>
              </p>
            ) : (
              <p className="text-muted text-sm">Document B details</p>
            )}
          </div>
        </div>
      </div>

      {/* Differences table */}
      <div className="differences-section">
        <h2 className="section-heading">
          <span className="section-heading-icon">🔄</span>
          Differences
        </h2>
        {result.differences && result.differences.length > 0 ? (
          <div className="differences-table-wrap">
            <table className="differences-table" aria-label="Document differences">
              <thead>
                <tr>
                  <th className="col-aspect" scope="col">Aspect</th>
                  <th className="col-doc" scope="col">
                    {result.doc_a_name || 'Document A'}
                  </th>
                  <th className="col-doc" scope="col">
                    {result.doc_b_name || 'Document B'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {result.differences.map((diff, i) => (
                  <tr key={i}>
                    <td className="col-aspect">{diff.aspect}</td>
                    <td className="col-doc">{diff.doc_a}</td>
                    <td className="col-doc">{diff.doc_b}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon="🤝"
            title="No Differences Found"
            description="The AI found no notable differences between the two documents."
          />
        )}
      </div>

      {/* Claims table */}
      <div className="claims-section">
        <h2 className="section-heading">
          <span className="section-heading-icon">🔬</span>
          Claim Analysis
        </h2>
        {result.claims && result.claims.length > 0 ? (
          <div className="claims-table-wrap">
            <table className="claims-table" aria-label="Claim analysis">
              <thead>
                <tr>
                  <th scope="col">Claim</th>
                  <th scope="col">Verdict</th>
                  <th scope="col">Source A</th>
                  <th scope="col">Source B</th>
                </tr>
              </thead>
              <tbody>
                {result.claims.map((claim, i) => {
                  // Build synthetic citations for source_a / source_b
                  const citationsForClaim = [
                    claim.source_a
                      ? { source_label: result.doc_a_name || 'Doc A', text: claim.source_a, score: 1 }
                      : null,
                    claim.source_b
                      ? { source_label: result.doc_b_name || 'Doc B', text: claim.source_b, score: 1 }
                      : null,
                  ].filter(Boolean) as { source_label: string; text: string; score: number }[]

                  return (
                    <tr key={claim.id ?? i}>
                      <td>{claim.claim}</td>
                      <td>
                        <VerdictBadge verdict={claim.verdict} />
                      </td>
                      <td>
                        {claim.source_a ? (
                          <span>
                            {claim.source_a.slice(0, 80)}
                            {claim.source_a.length > 80 ? '…' : ''}
                            {' '}
                            <CitationBadge
                              citation={citationsForClaim[0]}
                              index={i * 2 + 1}
                            />
                          </span>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td>
                        {claim.source_b ? (
                          <span>
                            {claim.source_b.slice(0, 80)}
                            {claim.source_b.length > 80 ? '…' : ''}
                            {' '}
                            <CitationBadge
                              citation={citationsForClaim[citationsForClaim.length - 1]}
                              index={i * 2 + 2}
                            />
                          </span>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon="📋"
            title="No Claims Identified"
            description="The AI did not identify any specific claims to compare in these documents."
          />
        )}
      </div>
    </div>
  )
}
