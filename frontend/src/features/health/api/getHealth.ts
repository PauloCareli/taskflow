import { ApiError } from '../../../shared/api/ApiError'
import { api } from '../../../shared/api/client'
import { healthSchema, type Health } from '../schemas/healthSchema'

export async function getHealth(): Promise<Health> {
  const body = await api.get('/health')
  const parsed = healthSchema.safeParse(body)
  if (!parsed.success) {
    throw new ApiError({
      kind: 'invalid_response',
      code: 'invalid_response',
      message: 'The health response has an unexpected shape',
      cause: parsed.error,
    })
  }
  return parsed.data
}
