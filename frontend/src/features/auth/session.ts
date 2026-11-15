import { tokenClaimsSchema, type TokenClaims } from './schemas/authSchemas'

/** Reads the claims of a JWT without verifying it; the API is the authority. */
export function decodeToken(token: string): TokenClaims | null {
  const payload = token.split('.')[1]
  if (!payload) return null
  try {
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const parsed = tokenClaimsSchema.safeParse(JSON.parse(json))
    return parsed.success ? parsed.data : null
  } catch {
    return null
  }
}

export function isUsable(claims: TokenClaims | null, nowMs = Date.now()): claims is TokenClaims {
  return claims !== null && (claims.exp === undefined || claims.exp * 1000 > nowMs)
}
