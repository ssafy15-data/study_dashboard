<script setup lang="ts">
import type { CellStatus } from '@/types'

const props = defineProps<{
  cell: CellStatus
  isOverdue: boolean
}>()
</script>

<template>
  <a
    v-if="props.cell.status !== 'not_submitted' && props.cell.pr_url"
    :href="props.cell.pr_url"
    target="_blank"
    rel="noreferrer"
    class="inline-flex h-9 w-9 items-center justify-center rounded text-lg font-bold ring-1"
    :class="
      props.cell.status === 'merged'
        ? 'bg-emerald-100 text-emerald-700 ring-emerald-200'
        : 'bg-amber-100 text-amber-700 ring-amber-200'
    "
    :title="`PR #${props.cell.pr_number}`"
  >
    {{ props.cell.status === 'merged' ? '✓' : '⏳' }}
  </a>
  <span
    v-else
    class="inline-flex h-9 w-9 items-center justify-center rounded text-lg font-bold ring-1"
    :class="
      props.isOverdue
        ? 'bg-slate-100 text-slate-500 ring-slate-200'
        : 'bg-rose-100 text-rose-700 ring-rose-200'
    "
    title="미제출"
  >
    ✕
  </span>
</template>

