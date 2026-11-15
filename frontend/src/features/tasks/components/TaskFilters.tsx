import { TextField } from '../../../shared/ui/TextField'
import { TASK_STATUSES, type TaskFilters as Filters, type TaskStatus } from '../schemas/taskSchemas'
import { STATUS_LABELS } from '../schemas/taskStatus'

type Props = { filters: Filters; onChange: (filters: Filters) => void }

export function TaskFilters({ filters, onChange }: Props) {
  function toggle(status: TaskStatus) {
    const statuses = filters.statuses.includes(status)
      ? filters.statuses.filter((current) => current !== status)
      : TASK_STATUSES.filter((s) => s === status || filters.statuses.includes(s))
    onChange({ ...filters, statuses })
  }

  return (
    <form
      aria-label="Filter tasks"
      onSubmit={(event) => event.preventDefault()}
      className="flex flex-col gap-4 md:flex-row md:items-end"
    >
      <fieldset className="flex flex-wrap gap-x-4 gap-y-2">
        <legend className="mb-1 text-sm font-medium">Status</legend>
        {TASK_STATUSES.map((status) => (
          <label key={status} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={filters.statuses.includes(status)}
              onChange={() => toggle(status)}
              className="size-4 accent-accent"
            />
            {STATUS_LABELS[status]}
          </label>
        ))}
      </fieldset>
      <TextField
        label="Due after"
        type="date"
        value={filters.dueAfter}
        onChange={(event) => onChange({ ...filters, dueAfter: event.target.value })}
      />
      <TextField
        label="Due before"
        type="date"
        value={filters.dueBefore}
        onChange={(event) => onChange({ ...filters, dueBefore: event.target.value })}
      />
    </form>
  )
}
