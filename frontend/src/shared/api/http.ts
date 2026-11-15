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
}: HttpClientOptions) {
  const base = baseUrl.replace(/\/+$/, '')

  async function get(path: string): Promise<unknown> {
    const headers = new Headers({ Accept: 'application/json' })
    const token = getToken?.()
    if (token) headers.set('Authorization', `Bearer ${token}`)

    const controller = new AbortController()
    let timedOut = false
    const timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, timeoutMs)

    try {
      const response = await fetch(`${base}${path}`, { headers, signal: controller.signal })
      const body = await readJson(response)
      if (!response.ok) throw httpError(response, body)
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

  return { get }
}

export type HttpClient = ReturnType<typeof createHttpClient>
