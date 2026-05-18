<script setup lang="ts">
import { computed } from 'vue'
import PlatformBadge from './PlatformBadge.vue'
import StatusCell from './StatusCell.vue'
import type { MatrixResponse } from '@/types'

const props = defineProps<{ data: MatrixResponse }>()

const sortedMembers = computed(() => {
  return [...props.data.members].sort((a, b) => {
    const countA = Object.values(props.data.matrix[a] || {}).filter(
      (cell) => cell.status === 'merged',
    ).length
    const countB = Object.values(props.data.matrix[b] || {}).filter(
      (cell) => cell.status === 'merged',
    ).length
    return countB - countA || a.localeCompare(b)
  })
})

function mergedCount(member: string) {
  return Object.values(props.data.matrix[member] || {}).filter((cell) => cell.status === 'merged')
    .length
}
</script>

<template>
  <div class="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
    <table class="min-w-full border-collapse text-sm">
      <thead>
        <tr class="border-b border-slate-200 bg-slate-50">
          <th class="sticky left-0 z-10 bg-slate-50 px-4 py-3 text-left font-semibold text-slate-700">
            멤버
          </th>
          <th
            v-for="problem in data.problems"
            :key="problem.issue_number"
            class="min-w-40 px-3 py-3 text-center align-top font-semibold text-slate-700"
          >
            <a :href="problem.url" target="_blank" rel="noreferrer" class="block hover:text-sky-700">
              <PlatformBadge :platform="problem.platform" />
              <span class="mt-1 block text-xs text-slate-500">
                #{{ problem.platform_number }} · {{ problem.difficulty || '난이도 없음' }}
              </span>
              <span class="mt-1 block truncate" :title="problem.title">{{ problem.title }}</span>
            </a>
          </th>
          <th class="w-24 px-3 py-3 text-center font-semibold text-slate-700">제출</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in sortedMembers" :key="member" class="border-b border-slate-100 hover:bg-slate-50">
          <td class="sticky left-0 z-10 bg-white px-4 py-3 font-semibold text-slate-800">
            <RouterLink :to="`/member/${member}`" class="hover:text-sky-700">{{ member }}</RouterLink>
          </td>
          <td v-for="problem in data.problems" :key="problem.issue_number" class="px-3 py-3 text-center">
            <StatusCell
              :cell="
                data.matrix[member]?.[String(problem.issue_number)] ?? {
                  status: 'not_submitted',
                }
              "
              :is-overdue="data.milestone.is_overdue"
            />
          </td>
          <td class="px-3 py-3 text-center font-mono text-sm text-slate-700">
            {{ mergedCount(member) }} / {{ data.problems.length }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

