import type { z } from 'zod'
import { ApiError } from '../../../shared/api/ApiError'
import { api } from '../../../shared/api/client'
import {
  taskPageSchema,
  taskSchema,
  type Task,
  type TaskPage,
  type TaskQuery,
  type TaskStatus,
} from '../schemas/taskSchemas'

function parse<T>(schema: z.ZodType<T>, body: unknown, what: string): T {
  const result = schema.safeParse(body)
  if (!result.success) {
    throw new ApiError({
      kind: 'invalid_response',
      code: 'invalid_response',
      message: `The ${what} response has an unexpected shape`,
      cause: result.error,
    })
  }
  return result.data
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

export type NewTask = {
  title: string
  description?: string
  due_date?: string
  assignee_id?: string
}
export type TaskChanges = {
  title?: string
  description?: string
  due_date?: string | null
  status?: TaskStatus
}

export async function createTask(input: NewTask): Promise<Task> {
  return parse(taskSchema, await api.post('/tasks', input), 'task')
}

export async function updateTask(id: string, changes: TaskChanges): Promise<Task> {
  return parse(taskSchema, await api.patch(`/tasks/${id}`, changes), 'task')
}

export async function assignTask(id: string, assigneeId: string | null): Promise<Task> {
  return parse(
    taskSchema,
    await api.post(`/tasks/${id}/assign`, { assignee_id: assigneeId }),
    'task',
  )
}

export async function completeTask(id: string): Promise<Task> {
  return parse(taskSchema, await api.post(`/tasks/${id}/complete`), 'task')
}

export async function deleteTask(id: string): Promise<void> {
  await api.delete(`/tasks/${id}`)
}
