import { useQuery } from '@tanstack/vue-query'
import { fetchCurrentMilestone, fetchMilestones } from '@/lib/api'

export function useMilestones() {
  return useQuery({
    queryKey: ['milestones'],
    queryFn: fetchMilestones,
    refetchInterval: 60_000,
  })
}

export function useCurrentMilestone() {
  return useQuery({
    queryKey: ['milestones', 'current'],
    queryFn: fetchCurrentMilestone,
    refetchInterval: 60_000,
  })
}

