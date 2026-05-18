import { defineStore } from 'pinia'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    selectedMilestoneId: null as number | null,
  }),
  actions: {
    selectMilestone(id: number | null) {
      this.selectedMilestoneId = id
    },
  },
})

