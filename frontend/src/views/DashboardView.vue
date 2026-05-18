<script setup lang="ts">
import { computed, watch } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import LastUpdated from '@/components/LastUpdated.vue'
import MilestoneSelector from '@/components/MilestoneSelector.vue'
import ScoreBoard from '@/components/ScoreBoard.vue'
import StatsCards from '@/components/StatsCards.vue'
import { useMatrix } from '@/composables/useMatrix'
import { useCurrentMilestone, useMilestones } from '@/composables/useMilestones'
import { refreshDashboard } from '@/lib/api'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const queryClient = useQueryClient()
const milestones = useMilestones()
const currentMilestone = useCurrentMilestone()

watch(
  () => currentMilestone.data.value?.id,
  (id) => {
    if (id && store.selectedMilestoneId === null) {
      store.selectMilestone(id)
    }
  },
  { immediate: true },
)

const selectedMilestoneId = computed({
  get: () => store.selectedMilestoneId,
  set: (value) => store.selectMilestone(value),
})

const matrix = useMatrix(selectedMilestoneId)
const refreshMutation = useMutation({
  mutationFn: refreshDashboard,
  onSuccess: async () => {
    await queryClient.invalidateQueries()
  },
})
</script>

<template>
  <main class="min-h-screen bg-panel">
    <div class="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <header class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p class="text-sm font-semibold text-sky-700">SSAFY 15th Data Track</p>
          <h1 class="mt-1 text-2xl font-bold text-ink md:text-3xl">PS Study Dashboard</h1>
        </div>
        <div class="flex flex-col items-start gap-2 sm:flex-row sm:items-center">
          <MilestoneSelector
            v-model="selectedMilestoneId"
            :milestones="milestones.data.value ?? []"
          />
          <button
            class="h-10 rounded bg-ink px-4 text-sm font-semibold text-white shadow-sm hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="refreshMutation.isPending.value"
            @click="refreshMutation.mutate()"
          >
            {{ refreshMutation.isPending.value ? '갱신 중' : '수동 갱신' }}
          </button>
        </div>
      </header>

      <div v-if="matrix.isLoading.value" class="rounded-lg border border-slate-200 bg-white p-8 text-slate-500">
        데이터를 불러오는 중입니다.
      </div>
      <div v-else-if="matrix.error.value" class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-700">
        데이터를 불러오지 못했습니다.
      </div>
      <template v-else-if="matrix.data.value">
        <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <h2 class="text-lg font-semibold text-ink">{{ matrix.data.value.milestone.title }}</h2>
          <LastUpdated :value="matrix.data.value.last_refresh" />
        </div>
        <StatsCards :data="matrix.data.value" />
        <ScoreBoard :data="matrix.data.value" />
      </template>
      <div v-else class="rounded-lg border border-slate-200 bg-white p-8 text-slate-500">
        선택 가능한 회차가 없습니다.
      </div>
    </div>
  </main>
</template>

