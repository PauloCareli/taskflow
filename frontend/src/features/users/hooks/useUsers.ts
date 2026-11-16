import { useQuery } from '@tanstack/react-query'
import { listUsers } from '../api/usersApi'

export const userKeys = { all: ['users'] as const }

export function useUsers({ enabled = true }: { enabled?: boolean } = {}) {
  return useQuery({ queryKey: userKeys.all, queryFn: listUsers, staleTime: 60_000, enabled })
}
