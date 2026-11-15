import { createContext, useContext } from 'react'
import type { LoginInput, RegisterInput } from '../schemas/authSchemas'

export type AuthContextValue = {
  /** Id of the signed-in user (the `sub` claim), or null when signed out. */
  userId: string | null
  login: (input: LoginInput) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => void
}

/** The account exists, but the automatic sign-in that followed did not succeed. */
export class SignInAfterRegisterError extends Error {
  constructor() {
    super('Your account was created, but signing in failed. Please sign in.')
    this.name = 'SignInAfterRegisterError'
  }
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
