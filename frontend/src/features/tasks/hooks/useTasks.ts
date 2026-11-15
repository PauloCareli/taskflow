import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { listTasks } from '../api/tasksApi'
import type { TaskQuery } from '../schemas/taskSchemas'

export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (query: TaskQuery) => [...taskKeys.lists(), query] as const,
}

export function useTasks(query: TaskQuery) {
  return useQuery({
    queryKey: taskKeys.list(query),
    queryFn: () => listTasks(query),
    placeholderData: keepPreviousData,
    retry: false,
  })
}
