import { useAuth } from '../../auth/hooks/AuthContext'
import type { Task, TaskStatus } from '../schemas/taskSchemas'
import { isTerminal } from '../schemas/taskStatus'
import { useCompleteTask, useUpdateTask } from './useTaskMutations'

const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : 'Something went wrong'

/** What the signed-in user may do with a task, and the status mutations behind it. */
export function useTaskActions(task: Task, onError: (message: string) => void) {
  const { userId } = useAuth()
  const update = useUpdateTask()
  const complete = useCompleteTask()
  const isCreator = task.creator.id === userId
  const busy = update.isPending || complete.isPending
  const canChangeStatus = (isCreator || task.assignee?.id === userId) && !isTerminal(task.status)

  return {
    isCreator,
    canChangeStatus,
    busy,
    // The status trigger stays enabled (so it keeps focus); ignore choices while a change is in flight.
    changeStatus: (status: TaskStatus) => {
      if (busy) return
      update.mutate({ id: task.id, changes: { status } }, { onError: (e) => onError(messageOf(e)) })
    },
    complete: () => {
      if (busy) return
      complete.mutate(task.id, { onError: (e) => onError(messageOf(e)) })
    },
  }
}
