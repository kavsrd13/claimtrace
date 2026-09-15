// Types
export interface Session {
  id: string
  title: string | null
  created_at: string
  expires_at: string
  is_expired: boolean
  document_count: number
}

export interface DocumentInfo {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  uploaded_at: string
  slot: number
  has_text: boolean
}

export interface DifferenceItem {
  aspect: string
  doc_a: string
  doc_b: string
}

export interface ClaimItem {
  id: string
  claim: string
  source_a: string | null
  source_b: string | null
  verdict: 'agree' | 'disagree' | 'only_in_a' | 'only_in_b'
}

export interface CompareResult {
  summary: string
  similarities: string[]
  differences: DifferenceItem[]
  claims: ClaimItem[]
  doc_a_name: string
  doc_b_name: string
}

export interface Citation {
  source_label: string
  text: string
  score: number
}

export interface AskResult {
  answer: string
  citations: Citation[]
  is_supported: boolean
}

export class ApiError extends Error {
  constructor(public status: number, public detail: any) {
    super(typeof detail === 'string' ? detail : detail?.detail || detail?.message || 'API error')
    this.name = 'ApiError'
  }
}

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const defaultHeaders: Record<string, string> = {}

  // Only set Content-Type for non-FormData bodies
  if (options?.body && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options?.headers,
    },
  })

  if (!res.ok) {
    let detail: any
    try {
      detail = await res.json()
    } catch {
      detail = res.statusText
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  sessions: {
    create: (title?: string): Promise<Session> =>
      request('/sessions', {
        method: 'POST',
        body: JSON.stringify({ title: title ?? null }),
      }),
    get: (id: string): Promise<Session> => request(`/sessions/${id}`),
    delete: (id: string): Promise<void> =>
      request(`/sessions/${id}`, { method: 'DELETE' }),
  },
  documents: {
    upload: (sessionId: string, slot: number, file: File): Promise<DocumentInfo> => {
      const form = new FormData()
      form.append('slot', String(slot))
      form.append('file', file)
      return request(`/sessions/${sessionId}/documents`, {
        method: 'POST',
        body: form,
      })
    },
    list: (sessionId: string): Promise<DocumentInfo[]> =>
      request(`/sessions/${sessionId}/documents`),
  },
  compare: {
    run: (sessionId: string): Promise<CompareResult> =>
      request(`/sessions/${sessionId}/compare`, { method: 'POST' }),
  },
  qa: {
    ask: (sessionId: string, question: string): Promise<AskResult> =>
      request(`/sessions/${sessionId}/ask`, {
        method: 'POST',
        body: JSON.stringify({ question }),
      }),
  },
}
