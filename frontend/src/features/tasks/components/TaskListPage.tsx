import { useTasks } from '../hooks/useTasks'

export function TaskListPage() {
  useTasks({ statuses: [], dueAfter: '', dueBefore: '', page: 1, size: 25 })
  return (
    <section aria-labelledby="tasks-title" className="flex flex-col gap-4">
      <h1 id="tasks-title" className="text-2xl font-semibold">
        Tasks
      </h1>
    </section>
  )
}
