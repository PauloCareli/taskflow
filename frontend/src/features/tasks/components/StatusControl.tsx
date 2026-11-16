import { Menu } from '../../../shared/ui/Menu'
import { TASK_STATUSES, type Task, type TaskStatus } from '../schemas/taskSchemas'
import { STATUS_LABELS } from '../schemas/taskStatus'
import { StatusBadge } from './StatusBadge'

type Props = {
  task: Task
  canChange: boolean
  onChange: (status: TaskStatus) => void
}

/** The status tag; when the user may change the status it is also the dropdown that does it. */
export function StatusControl({ task, canChange, onChange }: Props) {
  if (!canChange) return <StatusBadge status={task.status} />
  const items = TASK_STATUSES.filter(
    (status) => status !== 'completed' && status !== task.status,
  ).map((status) => ({ label: STATUS_LABELS[status], onSelect: () => onChange(status) }))
  return (
    <Menu
      label={`Change status, currently ${STATUS_LABELS[task.status]}`}
      items={items}
      triggerClassName="rounded-full"
    >
      <StatusBadge status={task.status} />
      <span aria-hidden="true" className="text-xs text-fg-muted">
        ▾
      </span>
    </Menu>
  )
}
