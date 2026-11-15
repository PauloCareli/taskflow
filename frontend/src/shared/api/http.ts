import { z } from 'zod'
import { ApiError } from './ApiError'

const errorBodySchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z
      .array(z.unknown())
      .nullish()
      .transform((details) => details ?? []),
  }),
})

export type TokenProvider = () => string | null | undefined

export type HttpClientOptions = {
  baseUrl: string
  timeoutMs?: number
  getToken?: TokenProvider | undefined
  /** Called when a request that carried a token is answered with 401. */
  onUnauthorized?: (() => void) | undefined
}

export type QueryValue = string | number | readonly string[] | undefined | null
export type RequestOptions = { query?: Record<string, QueryValue> | undefined; body?: unknown }

function queryString(query: Record<string, QueryValue> | undefined): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') continue
    if (typeof value === 'object') {
      for (const item of value) params.append(key, item)
    } else {
      params.append(key, String(value))
    }
  }
  const text = params.toString()
  return text ? `?${text}` : ''
}

const DEFAULT_TIMEOUT_MS = 10_000

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return undefined
  }
}

function httpError(response: Response, body: unknown): ApiError {
  const parsed = errorBodySchema.safeParse(body)
  if (parsed.success) {
    const { code, message, details } = parsed.data.error
    return new ApiError({ kind: 'http', status: response.status, code, message, details })
  }
  return new ApiError({
    kind: 'http',
    status: response.status,
    code: 'http_error',
    message: `Request failed with status ${response.status}`,
  })
}

export function createHttpClient({
  baseUrl,
  timeoutMs = DEFAULT_TIMEOUT_MS,
  getToken,
  onUnauthorized,
}: HttpClientOptions) {
  const base = baseUrl.replace(/\/+$/, '')

  async function request(
    method: string,
    path: string,
    { query, body: payload }: RequestOptions = {},
  ): Promise<unknown> {
    const headers = new Headers({ Accept: 'application/json' })
    const token = getToken?.()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    if (payload !== undefined) headers.set('Content-Type', 'application/json')

    const controller = new AbortController()
    let timedOut = false
    const timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, timeoutMs)

    try {
      const response = await fetch(`${base}${path}${queryString(query)}`, {
        method,
        headers,
        signal: controller.signal,
        ...(payload !== undefined && { body: JSON.stringify(payload) }),
      })
      if (response.status === 204) return undefined
      const body = await readJson(response)
      if (!response.ok) {
        if (response.status === 401 && token) onUnauthorized?.()
        throw httpError(response, body)
      }
      if (body === undefined) {
        throw new ApiError({
          kind: 'invalid_response',
          status: response.status,
          code: 'invalid_response',
          message: 'The API returned a response that is not valid JSON',
        })
      }
      return body
    } catch (error) {
      if (error instanceof ApiError) throw error
      if (timedOut) {
        throw new ApiError({
          kind: 'timeout',
          code: 'timeout',
          message: 'The API did not respond in time',
          cause: error,
        })
      }
      throw new ApiError({
        kind: 'network',
        code: 'network_error',
        message: 'Could not reach the API',
        cause: error,
      })
    } finally {
      clearTimeout(timer)
    }
  }

  return {
    get: (path: string, options?: Pick<RequestOptions, 'query'>) => request('GET', path, options),
    post: (path: string, body?: unknown) => request('POST', path, { body }),
    patch: (path: string, body?: unknown) => request('PATCH', path, { body }),
    delete: (path: string) => request('DELETE', path),
  }
}

export type HttpClient = ReturnType<typeof createHttpClient>
