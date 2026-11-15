import { STATUS_LABELS } from '../schemas/taskStatus'
import type { TaskStatus } from '../schemas/taskSchemas'

const STYLES: Record<TaskStatus, string> = {
  todo: 'border-border text-fg-muted',
  in_progress: 'border-accent text-accent-fg',
  blocked: 'border-attention text-attention',
  completed: 'border-success text-success',
  cancelled: 'border-border text-fg-muted',
}

export function StatusBadge({ status }: { status: TaskStatus }) {
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}
