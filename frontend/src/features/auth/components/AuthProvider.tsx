import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setTokenProvider, setUnauthorizedHandler } from '../../../shared/api/client'
import * as authApi from '../api/authApi'
import { AuthContext, SignInAfterRegisterError, type AuthContextValue } from '../hooks/AuthContext'
import type { LoginInput, RegisterInput } from '../schemas/authSchemas'
import { decodeToken, isUsable } from '../session'
import { clearStoredToken, readStoredToken, storeToken } from '../tokenStorage'

// Registered at import time so queries fired by the first render already carry the token.
setTokenProvider(readStoredToken)

function initialUserId(): string | null {
  const token = readStoredToken()
  if (!token) return null
  const claims = decodeToken(token)
  if (isUsable(claims)) return claims.sub
  clearStoredToken()
  return null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [userId, setUserId] = useState<string | null>(initialUserId)

  const signIn = useCallback((token: string) => {
    const claims = decodeToken(token)
    if (!isUsable(claims)) throw new Error('The API issued a token that cannot be used')
    storeToken(token)
    setUserId(claims.sub)
  }, [])

  const logout = useCallback(() => {
    clearStoredToken()
    setUserId(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  const value = useMemo<AuthContextValue>(
    () => ({
      userId,
      login: async (input: LoginInput) => signIn(await authApi.login(input)),
      register: async (input: RegisterInput) => {
        await authApi.register(input)
        try {
          signIn(await authApi.login({ email: input.email, password: input.password }))
        } catch {
          throw new SignInAfterRegisterError()
        }
      },
      logout,
    }),
    [userId, signIn, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
