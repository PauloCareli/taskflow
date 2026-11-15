import { z } from 'zod'

export const TASK_STATUSES = ['todo', 'in_progress', 'blocked', 'completed', 'cancelled'] as const
export const taskStatusSchema = z.enum(TASK_STATUSES)
export type TaskStatus = z.infer<typeof taskStatusSchema>

const userRefSchema = z.object({ id: z.string(), name: z.string() })

export const taskSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  status: taskStatusSchema,
  due_date: z.iso.datetime({ offset: true }).nullable(),
  created_at: z.string(),
  updated_at: z.string(),
  completed_at: z.string().nullable(),
  creator: userRefSchema,
  assignee: userRefSchema.nullable(),
})
export type Task = z.infer<typeof taskSchema>

export const taskPageSchema = z.object({
  items: z.array(taskSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  size: z.number().int().positive(),
})
export type TaskPage = z.infer<typeof taskPageSchema>

export const userSchema = z.object({ id: z.string(), email: z.string(), name: z.string() })
export const userListSchema = z.array(userSchema)
export type User = z.infer<typeof userSchema>

export type TaskFilters = {
  statuses: TaskStatus[]
  /** Date-only values (YYYY-MM-DD), read as UTC. */
  dueAfter: string
  dueBefore: string
}
export type TaskQuery = TaskFilters & { page: number; size: number }
