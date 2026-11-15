import { z } from 'zod'

const EXPECTED = 'an absolute http(s) URL or an absolute path such as /api'

function isValidBaseUrl(value: string): boolean {
  if (value.startsWith('/')) {
    return !value.startsWith('//')
  }
  try {
    const { protocol } = new URL(value)
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}

const envSchema = z.object({
  VITE_API_BASE_URL: z
    .string({ error: `VITE_API_BASE_URL is not set; expected ${EXPECTED}.` })
    .trim()
    .refine(isValidBaseUrl, { error: `VITE_API_BASE_URL is invalid; expected ${EXPECTED}.` }),
})

export type Env = { apiBaseUrl: string }

export function parseEnv(raw: Record<string, string | undefined>): Env {
  const result = envSchema.safeParse(raw)
  if (!result.success) {
    const issue = result.error.issues[0]
    throw new Error(issue?.message ?? `VITE_API_BASE_URL is invalid; expected ${EXPECTED}.`)
  }
  return { apiBaseUrl: result.data.VITE_API_BASE_URL.replace(/\/+$/, '') }
}
