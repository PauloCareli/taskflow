import { ApiError } from '../../../shared/api/ApiError'
import { api } from '../../../shared/api/client'
import { userListSchema, type User } from '../schemas/userSchemas'

export async function listUsers(): Promise<User[]> {
  const parsed = userListSchema.safeParse(await api.get('/users'))
  if (!parsed.success) {
    throw new ApiError({
      kind: 'invalid_response',
      code: 'invalid_response',
      message: 'The user list response has an unexpected shape',
      cause: parsed.error,
    })
  }
  return parsed.data
}
