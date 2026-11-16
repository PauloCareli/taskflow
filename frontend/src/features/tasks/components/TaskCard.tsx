import { formatDate } from '../../../shared/lib/dates'
import { Button } from '../../../shared/ui/Button'
import { Menu, type MenuItem } from '../../../shared/ui/Menu'
import { Tooltip } from '../../../shared/ui/Tooltip'
import { useTaskActions } from '../hooks/useTaskActions'
import type { Task } from '../schemas/taskSchemas'
import { isOverdue } from '../schemas/taskStatus'
import { OverdueTag } from './OverdueTag'
import { StatusControl } from './StatusControl'

type Props = {
  task: Task
  onView: (task: Task) => void
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
  onError: (message: string) => void
}

export function TaskCard({ task, onView, onEdit, onDelete, onError }: Props) {
  const actions = useTaskActions(task, onError)

  const items: MenuItem[] = [{ label: 'View', onSelect: () => onView(task) }]
  if (actions.isCreator) {
    items.push(
      { label: 'Edit', onSelect: () => onEdit(task) },
      { label: 'Delete', onSelect: () => onDelete(task), danger: true },
    )
  }

  return (
    <li
      aria-label={task.title}
      className="flex items-start gap-3 rounded-md border border-border bg-surface p-4"
    >
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <h2 className="min-w-0 text-base font-semibold">
          <button
            type="button"
            onClick={() => onView(task)}
            className={`max-w-full break-words text-left hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${task.status === 'cancelled' ? 'line-through' : ''}`}
          >
            {task.title}
          </button>
        </h2>
        <p className="text-sm text-fg-muted">
          {task.due_date ? `Due ${formatDate(task.due_date)}` : 'No due date'}
          {' · '}
          {task.assignee ? `Assigned to ${task.assignee.name}` : 'Unassigned'}
        </p>
        {task.description ? (
          <Tooltip content={task.description}>
            <p
              data-testid="task-description"
              // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- keyboard users must reach the truncated text to see the tooltip
              tabIndex={0}
              className="truncate text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              {task.description}
            </p>
          </Tooltip>
        ) : null}
        <div className="flex flex-wrap items-center gap-2">
          <StatusControl
            task={task}
            canChange={actions.canChangeStatus}
            onChange={actions.changeStatus}
          />
          {isOverdue(task) ? <OverdueTag /> : null}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {actions.canChangeStatus ? (
          <Button
            disabled={actions.busy}
            onClick={actions.complete}
            aria-label={`Complete “${task.title}”`}
          >
            Complete
          </Button>
        ) : null}
        <Menu
          label={`Actions for “${task.title}”`}
          items={items}
          triggerClassName="size-9 rounded-md border border-border bg-surface text-fg"
        >
          <span aria-hidden="true" className="text-lg leading-none">
            ⋮
          </span>
        </Menu>
      </div>
    </li>
  )
}
