import { formatDate } from '../../../shared/lib/dates'
import { isOverdue } from '../schemas/taskStatus'
import type { Task } from '../schemas/taskSchemas'
import { StatusBadge } from './StatusBadge'

export function TaskCard({ task }: { task: Task }) {
  const overdue = isOverdue(task)
  return (
    <li
      aria-label={task.title}
      className="flex flex-col gap-2 rounded-md border border-border bg-surface p-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <h2
          className={`min-w-0 break-words text-base font-semibold ${task.status === 'cancelled' ? 'line-through' : ''}`}
        >
          {task.title}
        </h2>
        <StatusBadge status={task.status} />
        {overdue ? (
          <span className="text-sm font-medium text-danger">
            <span aria-hidden="true">⚠ </span>Overdue
          </span>
        ) : null}
      </div>
      <p className="text-sm text-fg-muted">
        {task.due_date ? `Due ${formatDate(task.due_date)}` : 'No due date'}
        {' · '}
        {task.assignee ? `Assigned to ${task.assignee.name}` : 'Unassigned'}
      </p>
    </li>
  )
}
