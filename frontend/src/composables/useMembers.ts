import { useQuery } from '@tanstack/vue-query'
import { fetchMembers } from '@/lib/api'

export function useMembers() {
  return useQuery({
    queryKey: ['members'],
    queryFn: fetchMembers,
    refetchInterval: 60_000,
  })
}

