import { useId } from 'react'
import { Button } from '../../../shared/ui/Button'
import { TextField } from '../../../shared/ui/TextField'
import { TASK_STATUSES, type TaskFilters as Filters, type TaskStatus } from '../schemas/taskSchemas'
import { STATUS_LABELS } from '../schemas/taskStatus'

type Props = {
  filters: Filters
  onChange: (filters: Filters) => void
  onClear: () => void
}

export function TaskFilters({ filters, onChange, onClear }: Props) {
  const titleId = useId()
  const active = filters.statuses.length > 0 || filters.dueAfter !== '' || filters.dueBefore !== ''

  function toggle(status: TaskStatus) {
    const statuses = filters.statuses.includes(status)
      ? filters.statuses.filter((current) => current !== status)
      : TASK_STATUSES.filter((s) => s === status || filters.statuses.includes(s))
    onChange({ ...filters, statuses })
  }

  return (
    <section
      aria-labelledby={titleId}
      className="flex flex-col gap-4 rounded-md border border-border bg-surface p-4"
    >
      <div className="flex items-center justify-between gap-2">
        <h2 id={titleId} className="text-base font-semibold">
          Filters
        </h2>
        <Button variant="secondary" disabled={!active} onClick={onClear}>
          Clear filters
        </Button>
      </div>
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
    </section>
  )
}
