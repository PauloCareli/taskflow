import type { Task, TaskStatus } from './taskSchemas'

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  blocked: 'Blocked',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export function isTerminal(status: TaskStatus): boolean {
  return status === 'completed' || status === 'cancelled'
}

export function isOverdue(task: Pick<Task, 'status' | 'due_date'>, now = Date.now()): boolean {
  return task.due_date !== null && !isTerminal(task.status) && Date.parse(task.due_date) < now
}
