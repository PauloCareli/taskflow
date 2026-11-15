import { ApiError } from '../../../shared/api/ApiError'
import { api } from '../../../shared/api/client'
import {
  registeredUserSchema,
  tokenResponseSchema,
  type LoginInput,
  type RegisterInput,
} from '../schemas/authSchemas'

function invalid(message: string, cause: unknown): ApiError {
  return new ApiError({ kind: 'invalid_response', code: 'invalid_response', message, cause })
}

export async function login(input: LoginInput): Promise<string> {
  const parsed = tokenResponseSchema.safeParse(await api.post('/auth/login', input))
  if (!parsed.success) throw invalid('The login response has an unexpected shape', parsed.error)
  return parsed.data.access_token
}

export async function register(input: RegisterInput): Promise<void> {
  const parsed = registeredUserSchema.safeParse(await api.post('/auth/register', input))
  if (!parsed.success) throw invalid('The register response has an unexpected shape', parsed.error)
}
