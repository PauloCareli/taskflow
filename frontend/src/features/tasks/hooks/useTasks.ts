import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { getTask, listTasks } from '../api/tasksApi'
import type { TaskQuery } from '../schemas/taskSchemas'

export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (query: TaskQuery) => [...taskKeys.lists(), query] as const,
  detail: (id: string) => [...taskKeys.all, 'detail', id] as const,
}

export function useTasks(query: TaskQuery) {
  return useQuery({
    queryKey: taskKeys.list(query),
    queryFn: () => listTasks(query),
    placeholderData: keepPreviousData,
    retry: false,
  })
}

/** One task by id, independent of the list's filters and page. */
export function useTask(id: string | null) {
  return useQuery({
    queryKey: taskKeys.detail(id ?? ''),
    queryFn: () => getTask(id ?? ''),
    enabled: id !== null,
    retry: false,
  })
}
