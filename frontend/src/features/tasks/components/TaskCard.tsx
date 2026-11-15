import { formatDate } from '../../../shared/lib/dates'
import { Button } from '../../../shared/ui/Button'
import { useAuth } from '../../auth/hooks/AuthContext'
import { useCompleteTask, useUpdateTask } from '../hooks/useTaskMutations'
import { TASK_STATUSES, type Task, type TaskStatus } from '../schemas/taskSchemas'
import { isOverdue, isTerminal, STATUS_LABELS } from '../schemas/taskStatus'
import { StatusBadge } from './StatusBadge'

type Props = {
  task: Task
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
  onError: (message: string) => void
}

const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : 'Something went wrong'
const CHOICES = TASK_STATUSES.filter((status) => status !== 'completed')

export function TaskCard({ task, onEdit, onDelete, onError }: Props) {
  const { userId } = useAuth()
  const update = useUpdateTask()
  const complete = useCompleteTask()
  const isCreator = task.creator.id === userId
  const canChangeStatus = (isCreator || task.assignee?.id === userId) && !isTerminal(task.status)
  const busy = update.isPending || complete.isPending
  const overdue = isOverdue(task)

  function changeStatus(status: TaskStatus) {
    update.mutate({ id: task.id, changes: { status } }, { onError: (e) => onError(messageOf(e)) })
  }

  return (
    <li
      aria-label={task.title}
      className="flex flex-col gap-3 rounded-md border border-border bg-surface p-4"
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
      <div className="flex flex-wrap items-center gap-2">
        {canChangeStatus ? (
          <>
            <select
              aria-label="Change status"
              value={task.status}
              disabled={busy}
              onChange={(event) => changeStatus(event.target.value as TaskStatus)}
              className="min-h-9 rounded-md border border-border bg-surface px-2 text-sm text-fg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              {CHOICES.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABELS[status]}
                </option>
              ))}
            </select>
            <Button
              disabled={busy}
              onClick={() => complete.mutate(task.id, { onError: (e) => onError(messageOf(e)) })}
              aria-label={`Complete “${task.title}”`}
            >
              Complete
            </Button>
          </>
        ) : null}
        {isCreator ? (
          <>
            <Button
              variant="secondary"
              onClick={() => onEdit(task)}
              aria-label={`Edit “${task.title}”`}
            >
              Edit
            </Button>
            <Button
              variant="danger"
              onClick={() => onDelete(task)}
              aria-label={`Delete “${task.title}”`}
            >
              Delete
            </Button>
          </>
        ) : null}
      </div>
    </li>
  )
}
