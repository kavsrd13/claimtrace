import React, { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError, DocumentInfo } from '../api'
import LoadingState from '../components/LoadingState'
import { useSession } from '../context/SessionContext'

/* ============================================================
   Helpers
   ============================================================ */
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const ACCEPTED_TYPES = '.txt,.pdf,.docx'
const ACCEPTED_MIME = [
  'text/plain',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

function isAccepted(file: File): boolean {
  return ACCEPTED_MIME.includes(file.type) || /\.(txt|pdf|docx)$/i.test(file.name)
}

/* ============================================================
   DropZone component
   ============================================================ */
interface DropZoneProps {
  label: string
  slot: number
  sessionId: string | null
  onUploaded: (doc: DocumentInfo) => void
  onNeedSession: () => Promise<string>
  existingDoc: DocumentInfo | null
}

type DropZoneStatus = 'idle' | 'uploading' | 'done' | 'error'

function DropZone({
  label,
  slot,
  sessionId,
  onUploaded,
  onNeedSession,
  existingDoc,
}: DropZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<DropZoneStatus>(existingDoc ? 'done' : 'idle')
  const [dragOver, setDragOver] = useState(false)
  const [uploadedDoc, setUploadedDoc] = useState<DocumentInfo | null>(existingDoc)
  const [error, setError] = useState<string | null>(null)
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  const uploadFile = useCallback(
    async (file: File, sid: string) => {
      setStatus('uploading')
      setError(null)
      setPendingFile(file)
      try {
        const doc = await api.documents.upload(sid, slot, file)
        setUploadedDoc(doc)
        setStatus('done')
        onUploaded(doc)
      } catch (err) {
        const msg =
          err instanceof ApiError
            ? err.message
            : 'Upload failed. Please try again.'
        setError(msg)
        setStatus('error')
        setPendingFile(null)
      }
    },
    [slot, onUploaded],
  )

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return
      const file = files[0]
      if (!isAccepted(file)) {
        setError('Unsupported file type. Please use .txt, .pdf, or .docx.')
        setStatus('error')
        return
      }
      let sid = sessionId
      if (!sid) {
        try {
          sid = await onNeedSession()
        } catch {
          setError('Failed to create session. Please try again.')
          setStatus('error')
          return
        }
      }
      await uploadFile(file, sid)
    },
    [sessionId, onNeedSession, uploadFile],
  )

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    await handleFiles(e.dataTransfer.files)
  }

  const handleInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    await handleFiles(e.target.files)
    // reset so same file can be re-selected
    e.target.value = ''
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      fileInputRef.current?.click()
    }
  }

  const handleReplace = (e: React.MouseEvent) => {
    e.stopPropagation()
    setStatus('idle')
    setUploadedDoc(null)
    setError(null)
    setPendingFile(null)
    fileInputRef.current?.click()
  }

  // Derive className
  let zoneClass = 'drop-zone'
  if (dragOver) zoneClass += ' drag-over'
  else if (status === 'done') zoneClass += ' has-file'
  else if (status === 'uploading') zoneClass += ' uploading'
  else if (status === 'error') zoneClass += ' error'

  return (
    <div className="upload-slot">
      <p className="upload-slot-label">{label}</p>

      <div
        className={zoneClass}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        aria-label={`Upload ${label}. ${
          uploadedDoc ? `Current file: ${uploadedDoc.filename}` : 'Click or drag a file here'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          className="file-input-hidden"
          onChange={handleInputChange}
          aria-hidden="true"
          tabIndex={-1}
        />

        {status === 'uploading' && (
          <>
            <div className="spinner" aria-hidden="true" />
            <p className="drop-zone-text">
              Uploading {pendingFile?.name}…
            </p>
          </>
        )}

        {status === 'done' && uploadedDoc && (
          <>
            <div className="drop-zone-icon" aria-hidden="true">✅</div>
            <div className="drop-zone-file">
              <span className="drop-zone-filename">{uploadedDoc.filename}</span>
              <span className="drop-zone-filesize">{formatBytes(uploadedDoc.size_bytes)}</span>
              <span
                className="drop-zone-replace"
                onClick={handleReplace}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') handleReplace(e as any)
                }}
                aria-label="Replace file"
              >
                Replace file
              </span>
            </div>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="drop-zone-icon" aria-hidden="true">❌</div>
            <p className="drop-zone-text">{error}</p>
            <p className="drop-zone-hint">Click to try again</p>
          </>
        )}

        {status === 'idle' && (
          <>
            <div className="drop-zone-icon" aria-hidden="true">📄</div>
            <p className="drop-zone-text">Drag & drop a file here</p>
            <p className="drop-zone-hint">or click to browse (.txt, .pdf, .docx)</p>
          </>
        )}
      </div>
    </div>
  )
}

/* ============================================================
   Upload Page
   ============================================================ */
export default function Upload() {
  const navigate = useNavigate()
  const { sessionId, setSessionId, refreshSession } = useSession()

  const [docA, setDocA] = useState<DocumentInfo | null>(null)
  const [docB, setDocB] = useState<DocumentInfo | null>(null)
  const [sessionError, setSessionError] = useState<string | null>(null)
  const [creatingSession, setCreatingSession] = useState(false)

  // Create a session on demand (called when first file is dropped)
  const ensureSession = useCallback(async (): Promise<string> => {
    if (sessionId) return sessionId
    setCreatingSession(true)
    try {
      const session = await api.sessions.create()
      setSessionId(session.id)
      return session.id
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : 'Failed to create session.'
      setSessionError(msg)
      throw err
    } finally {
      setCreatingSession(false)
    }
  }, [sessionId, setSessionId])

  const handleDocAUploaded = (doc: DocumentInfo) => {
    setDocA(doc)
    refreshSession()
  }

  const handleDocBUploaded = (doc: DocumentInfo) => {
    setDocB(doc)
    refreshSession()
  }

  const handleCompare = () => {
    if (!sessionId) return
    navigate(`/session/${sessionId}/compare`)
  }

  const handleAskQuestions = () => {
    if (!sessionId) return
    navigate(`/session/${sessionId}/qa`)
  }

  if (creatingSession) {
    return (
      <div className="container page-content">
        <LoadingState message="Creating session…" />
      </div>
    )
  }

  return (
    <div className="container page-content">
      <div className="page-header">
        <div>
          <h1 className="page-title">Upload Documents</h1>
          <p className="text-secondary text-sm mt-1" style={{ marginTop: '0.25rem' }}>
            Upload two documents to compare them side-by-side with AI analysis.
          </p>
        </div>
      </div>

      {sessionError && (
        <div className="alert alert-danger" role="alert">
          <span className="alert-icon" aria-hidden="true">⚠️</span>
          <span>{sessionError}</span>
        </div>
      )}

      <div className="card mb-3">
        <div className="card-body">
          <div className="upload-grid">
            <DropZone
              label="Document A"
              slot={0}
              sessionId={sessionId}
              onUploaded={handleDocAUploaded}
              onNeedSession={ensureSession}
              existingDoc={docA}
            />
            <DropZone
              label="Document B"
              slot={1}
              sessionId={sessionId}
              onUploaded={handleDocBUploaded}
              onNeedSession={ensureSession}
              existingDoc={docB}
            />
          </div>

          <div className="upload-actions">
            <button
              className="btn btn-primary btn-lg"
              onClick={handleCompare}
              disabled={!docA || !docB}
              aria-disabled={!docA || !docB}
              title={!docA || !docB ? 'Upload both documents first' : undefined}
            >
              ⚡ Start Comparison
            </button>

            <button
              className="btn btn-outline-primary btn-lg"
              onClick={handleAskQuestions}
              disabled={!docA && !docB}
              aria-disabled={!docA && !docB}
              title={!docA && !docB ? 'Upload at least one document first' : undefined}
            >
              💬 Ask Questions
            </button>
          </div>

          {(!docA || !docB) && (
            <p className="text-muted text-sm" style={{ marginTop: '0.75rem' }}>
              {!docA && !docB
                ? 'Upload both Document A and Document B to start a comparison.'
                : !docA
                ? 'Upload Document A to complete the pair.'
                : 'Upload Document B to complete the pair.'}
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h2 className="section-heading">
            <span className="section-heading-icon">ℹ️</span>
            How it works
          </h2>
          <ol style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <li className="text-secondary" style={{ fontSize: '0.9375rem', lineHeight: '1.6' }}>
              <strong>Upload</strong> two text documents (.txt, .pdf, or .docx).
            </li>
            <li className="text-secondary" style={{ fontSize: '0.9375rem', lineHeight: '1.6' }}>
              <strong>Compare</strong> — see similarities, differences, and AI-generated claim analysis side by side.
            </li>
            <li className="text-secondary" style={{ fontSize: '0.9375rem', lineHeight: '1.6' }}>
              <strong>Ask questions</strong> — chat with an AI grounded in your uploaded documents.
            </li>
          </ol>
        </div>
      </div>
    </div>
  )
}
