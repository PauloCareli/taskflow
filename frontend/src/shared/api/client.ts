import { createHttpClient, type TokenProvider } from './http'
import { parseEnv } from './env'

const env = parseEnv(import.meta.env)

let unauthorizedHandler: (() => void) | null = null
let tokenProvider: TokenProvider | null = null

/** Hook point for the auth feature: register a function that returns the current bearer token. */
export function setTokenProvider(provider: TokenProvider | null): void {
  tokenProvider = provider
}

/** Hook point for the auth feature: called when a signed-in request is answered with 401. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

export const api = createHttpClient({
  baseUrl: env.apiBaseUrl,
  getToken: () => tokenProvider?.(),
  onUnauthorized: () => unauthorizedHandler?.(),
})
