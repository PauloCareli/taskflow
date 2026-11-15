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

export const TITLE_MAX = 120
export const DESCRIPTION_MAX = 2000

/** Form shape; `dueDate` is a date-only string (YYYY-MM-DD) or empty. */
export function taskFormSchema(options: { rejectPastDueDate: boolean; today: string }) {
  return z.object({
    title: z
      .string()
      .trim()
      .min(1, { error: 'Title is required' })
      .max(TITLE_MAX, { error: `Title must be ${TITLE_MAX} characters or fewer` }),
    description: z.string().max(DESCRIPTION_MAX, {
      error: `Description must be ${DESCRIPTION_MAX} characters or fewer`,
    }),
    dueDate: z
      .string()
      .refine((value) => !options.rejectPastDueDate || value === '' || value >= options.today, {
        error: 'Due date cannot be in the past',
      }),
    assigneeId: z.string(),
  })
}
export type TaskFormValues = z.infer<ReturnType<typeof taskFormSchema>>
