/* eslint-disable react-refresh/only-export-components */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { api, ApiError, Session } from '../api'

export interface SessionContextValue {
  sessionId: string | null
  session: Session | null
  setSessionId: (id: string) => void
  clearSession: () => void
  refreshSession: () => Promise<void>
}

const SessionContext = createContext<SessionContextValue>({
  sessionId: null,
  session: null,
  setSessionId: () => undefined,
  clearSession: () => undefined,
  refreshSession: async () => undefined,
})

export function useSession() {
  return useContext(SessionContext)
}

const SESSION_STORAGE_KEY = 'claimtrace_session_id'

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionIdState] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem(SESSION_STORAGE_KEY)
    } catch {
      return null
    }
  })
  const [session, setSession] = useState<Session | null>(null)

  const setSessionId = useCallback((id: string) => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, id)
    setSessionIdState(id)
  }, [])

  const clearSession = useCallback(() => {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
    setSessionIdState(null)
    setSession(null)
  }, [])

  const refreshSession = useCallback(async () => {
    if (!sessionId) return
    try {
      const s = await api.sessions.get(sessionId)
      setSession(s)
    } catch (err) {
      if (err instanceof ApiError && (err.status === 404 || err.status === 410)) {
        clearSession()
      }
    }
  }, [sessionId, clearSession])

  useEffect(() => {
    if (sessionId) {
      refreshSession()
    } else {
      setSession(null)
    }
  }, [sessionId, refreshSession])

  return (
    <SessionContext.Provider
      value={{ sessionId, session, setSessionId, clearSession, refreshSession }}
    >
      {children}
    </SessionContext.Provider>
  )
}
