import { ApiError } from '../../../shared/api/ApiError'
import { api } from '../../../shared/api/client'
import { taskPageSchema, type TaskPage, type TaskQuery } from '../schemas/taskSchemas'

function parse<T>(
  schema: { safeParse: (value: unknown) => { success: boolean; data?: T; error?: unknown } },
  body: unknown,
  what: string,
): T {
  const result = schema.safeParse(body)
  if (!result.success) {
    throw new ApiError({
      kind: 'invalid_response',
      code: 'invalid_response',
      message: `The ${what} response has an unexpected shape`,
      cause: result.error,
    })
  }
  return result.data as T
}

export async function listTasks(query: TaskQuery): Promise<TaskPage> {
  const body = await api.get('/tasks', {
    query: {
      page: query.page,
      size: query.size,
      status: query.statuses,
      due_after: query.dueAfter ? `${query.dueAfter}T00:00:00Z` : undefined,
      due_before: query.dueBefore ? `${query.dueBefore}T23:59:59Z` : undefined,
    },
  })
  return parse(taskPageSchema, body, 'task list')
}
