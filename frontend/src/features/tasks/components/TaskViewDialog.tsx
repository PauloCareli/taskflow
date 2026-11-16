import { useState } from 'react'
import { formatDate } from '../../../shared/lib/dates'
import { Button } from '../../../shared/ui/Button'
import { Dialog } from '../../../shared/ui/Dialog'
import { useTaskActions } from '../hooks/useTaskActions'
import type { Task } from '../schemas/taskSchemas'
import { isOverdue } from '../schemas/taskStatus'
import { OverdueTag } from './OverdueTag'
import { StatusControl } from './StatusControl'

type Props = { task: Task; onClose: () => void }

/** Read-only view of a task; only the status can be changed from here. */
export function TaskViewDialog({ task, onClose }: Props) {
  const [error, setError] = useState<string | null>(null)
  const actions = useTaskActions(task, setError)

  return (
    <Dialog title={task.title} onClose={onClose} dismissible>
      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-2">
        <StatusControl
          task={task}
          canChange={actions.canChangeStatus}
          onChange={(status) => {
            setError(null)
            actions.changeStatus(status)
          }}
        />
        {isOverdue(task) ? <OverdueTag /> : null}
        {actions.canChangeStatus ? (
          <Button
            disabled={actions.busy}
            onClick={() => {
              setError(null)
              actions.complete()
            }}
            aria-label={`Complete “${task.title}”`}
          >
            Complete
          </Button>
        ) : null}
      </div>
      {task.description ? (
        <p className="whitespace-pre-wrap break-words text-sm">{task.description}</p>
      ) : (
        <p className="text-sm text-fg-muted">No description</p>
      )}
      <ul className="flex flex-col gap-1 text-sm text-fg-muted">
        <li>{task.due_date ? `Due ${formatDate(task.due_date)}` : 'No due date'}</li>
        <li>Created by {task.creator.name}</li>
        <li>{task.assignee ? `Assigned to ${task.assignee.name}` : 'Unassigned'}</li>
        <li>Created {formatDate(task.created_at)}</li>
        <li>Updated {formatDate(task.updated_at)}</li>
      </ul>
    </Dialog>
  )
}
