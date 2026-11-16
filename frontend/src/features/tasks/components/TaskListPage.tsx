import { useState } from 'react'
import { Button } from '../../../shared/ui/Button'
import { useDeleteTask } from '../hooks/useTaskMutations'
import { useTasks } from '../hooks/useTasks'
import type { Task, TaskFilters as Filters } from '../schemas/taskSchemas'
import { DeleteTaskDialog } from './DeleteTaskDialog'
import { TaskFormDialog } from './TaskFormDialog'
import { Pagination } from './Pagination'
import { TaskCard } from './TaskCard'
import { TaskFilters } from './TaskFilters'
import { TaskViewDialog } from './TaskViewDialog'

const NO_FILTERS: Filters = { statuses: [], dueAfter: '', dueBefore: '' }

export function TaskListPage() {
  const [filters, setFilters] = useState<Filters>(NO_FILTERS)
  const [page, setPage] = useState(1)
  const [size, setSize] = useState(25)
  const tasks = useTasks({ ...filters, page, size })
  const remove = useDeleteTask()
  const [notice, setNotice] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [viewingId, setViewingId] = useState<string | null>(null)
  const [editing, setEditing] = useState<Task | null>(null)
  const [deleting, setDeleting] = useState<Task | null>(null)
  const viewing = tasks.data?.items.find((task) => task.id === viewingId)
  const total = tasks.data?.total
  const lastPage = total === undefined ? undefined : Math.max(1, Math.ceil(total / size))

  // A page can disappear (last item deleted here or elsewhere); fall back to the last one.
  if (lastPage !== undefined && page > lastPage) setPage(lastPage)

  function confirmDelete(task: Task) {
    setNotice(null)
    remove.mutate(task.id, {
      onError: (error) =>
        setNotice(error instanceof Error ? error.message : 'Could not delete the task'),
      onSettled: () => setDeleting(null),
    })
  }

  const filtered =
    filters.statuses.length > 0 || filters.dueAfter !== '' || filters.dueBefore !== ''

  return (
    <section aria-labelledby="tasks-title" className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <h1 id="tasks-title" className="text-2xl font-semibold">
          Tasks
        </h1>
        <Button onClick={() => setCreating(true)}>New task</Button>
      </div>
      {notice ? (
        <p role="alert" className="text-sm text-danger">
          {notice}
        </p>
      ) : null}
      <TaskFilters
        filters={filters}
        onChange={(next) => {
          setFilters(next)
          setPage(1)
        }}
        onClear={() => {
          setFilters(NO_FILTERS)
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
            <TaskCard
              key={task.id}
              task={task}
              onView={(target) => setViewingId(target.id)}
              onEdit={setEditing}
              onDelete={setDeleting}
              onError={setNotice}
            />
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
      {viewing ? <TaskViewDialog task={viewing} onClose={() => setViewingId(null)} /> : null}
      {creating ? <TaskFormDialog onClose={() => setCreating(false)} /> : null}
      {editing ? <TaskFormDialog task={editing} onClose={() => setEditing(null)} /> : null}
      {deleting ? (
        <DeleteTaskDialog
          task={deleting}
          pending={remove.isPending}
          onConfirm={() => confirmDelete(deleting)}
          onCancel={() => setDeleting(null)}
        />
      ) : null}
    </section>
  )
}
