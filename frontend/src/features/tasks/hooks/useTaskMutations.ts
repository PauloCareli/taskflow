import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  assignTask,
  completeTask,
  createTask,
  deleteTask,
  listUsers,
  updateTask,
  type TaskChanges,
} from '../api/tasksApi'
import { taskKeys } from './useTasks'

export const userKeys = { all: ['users'] as const }

export function useUsers() {
  return useQuery({ queryKey: userKeys.all, queryFn: listUsers, staleTime: 60_000 })
}

/** Every mutation refreshes the lists afterwards, also on failure, so the UI shows the truth. */
function useListInvalidation() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: taskKeys.lists() })
}

export function useCreateTask() {
  const invalidate = useListInvalidation()
  return useMutation({ mutationFn: createTask, onSettled: invalidate })
}

export function useUpdateTask() {
  const invalidate = useListInvalidation()
  return useMutation({
    mutationFn: ({ id, changes }: { id: string; changes: TaskChanges }) => updateTask(id, changes),
    onSettled: invalidate,
  })
}

export function useAssignTask() {
  const invalidate = useListInvalidation()
  return useMutation({
    mutationFn: ({ id, assigneeId }: { id: string; assigneeId: string | null }) =>
      assignTask(id, assigneeId),
    onSettled: invalidate,
  })
}

export function useCompleteTask() {
  const invalidate = useListInvalidation()
  return useMutation({ mutationFn: completeTask, onSettled: invalidate })
}

export function useDeleteTask() {
  const invalidate = useListInvalidation()
  return useMutation({ mutationFn: deleteTask, onSettled: invalidate })
}
