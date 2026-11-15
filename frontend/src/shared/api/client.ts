import { createHttpClient, type TokenProvider } from './http'
import { parseEnv } from './env'

const env = parseEnv(import.meta.env)

let tokenProvider: TokenProvider | null = null

/** Hook point for the auth feature: register a function that returns the current bearer token. */
export function setTokenProvider(provider: TokenProvider | null): void {
  tokenProvider = provider
}

export const api = createHttpClient({
  baseUrl: env.apiBaseUrl,
  getToken: () => tokenProvider?.(),
})
