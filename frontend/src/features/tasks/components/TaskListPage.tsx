import { useState } from 'react'
import { Button } from '../../../shared/ui/Button'
import { useTasks } from '../hooks/useTasks'
import type { TaskFilters as Filters } from '../schemas/taskSchemas'
import { Pagination } from './Pagination'
import { TaskCard } from './TaskCard'
import { TaskFilters } from './TaskFilters'

const NO_FILTERS: Filters = { statuses: [], dueAfter: '', dueBefore: '' }

export function TaskListPage() {
  const [filters, setFilters] = useState<Filters>(NO_FILTERS)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(25)
  const tasks = useTasks({ ...filters, page, size })

  const filtered =
    filters.statuses.length > 0 || filters.dueAfter !== '' || filters.dueBefore !== ''

  return (
    <section aria-labelledby="tasks-title" className="flex flex-col gap-4">
      <h1 id="tasks-title" className="text-2xl font-semibold">
        Tasks
      </h1>
      <TaskFilters
        filters={filters}
        onChange={(next) => {
          setFilters(next)
          setPage(1)
        }}
      />
      {tasks.isPending ? (
        <p role="status" className="text-fg-muted">
          Loading tasks…
        </p>
      ) : tasks.isError ? (
        <div role="alert" className="flex flex-col items-start gap-2 text-danger">
          <p>Could not load tasks.</p>
          <Button variant="secondary" onClick={() => void tasks.refetch()}>
            Retry
          </Button>
        </div>
      ) : tasks.data.items.length === 0 ? (
        <p className="text-fg-muted">
          {filtered ? 'No tasks match these filters.' : 'No tasks yet.'}
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {tasks.data.items.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </ul>
      )}
      {tasks.data ? (
        <Pagination
          page={page}
          size={size}
          total={tasks.data.total}
          onPage={setPage}
          onSize={(next) => {
            setSize(next)
            setPage(1)
          }}
        />
      ) : null}
    </section>
  )
}
