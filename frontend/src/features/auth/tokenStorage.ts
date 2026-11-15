export const TOKEN_STORAGE_KEY = 'taskflow.token'

export function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export function storeToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } catch {
    // Storage can be unavailable (private mode); the session then lasts until reload.
  }
}

export function clearStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  } catch {
    // Nothing to clear when storage is unavailable.
  }
}
