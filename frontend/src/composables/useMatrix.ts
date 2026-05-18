import type { Ref } from 'vue'
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { fetchMatrix } from '@/lib/api'

export function useMatrix(milestoneId: Ref<number | null>) {
  return useQuery({
    queryKey: computed(() => ['matrix', milestoneId.value]),
    queryFn: () => fetchMatrix(milestoneId.value),
    enabled: computed(() => milestoneId.value !== null),
    refetchInterval: 60_000,
  })
}

