<script setup lang="ts">
import { computed } from 'vue'
import type { MatrixResponse } from '@/types'

const props = defineProps<{ data: MatrixResponse }>()

const rate = computed(() => Math.round(props.data.summary.submission_rate * 100))
const deadline = computed(() => {
  const days = props.data.milestone.days_left
  if (days === null) return '마감일 없음'
  if (days === 0) return 'D-day'
  if (days > 0) return `D-${days}`
  return `Overdue +${Math.abs(days)}일`
})
</script>

<template>
  <section class="grid gap-3 md:grid-cols-3">
    <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p class="text-sm font-medium text-slate-500">이번 회차 제출률</p>
      <p class="mt-2 text-3xl font-bold text-ink">{{ rate }}%</p>
      <p class="mt-1 text-xs text-slate-500">
        {{ data.summary.total_submissions }} / {{ data.summary.total_possible }}
      </p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p class="text-sm font-medium text-slate-500">미제출 인원</p>
      <p class="mt-2 text-3xl font-bold text-ink">
        {{ data.summary.missing_members }} / {{ data.summary.total_members }}
      </p>
      <p class="mt-1 text-xs text-slate-500">문제별 제출 누락 기준</p>
    </div>
    <div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p class="text-sm font-medium text-slate-500">마감까지 남은 시간</p>
      <p class="mt-2 text-3xl font-bold text-ink">{{ deadline }}</p>
      <p class="mt-1 text-xs text-slate-500">{{ data.milestone.due_on ?? '미설정' }}</p>
    </div>
  </section>
</template>

