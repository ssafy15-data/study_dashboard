<script setup lang="ts">
const props = defineProps<{ platform: string }>()

const palette: Record<string, string> = {
  BOJ: 'bg-sky-100 text-sky-800 ring-sky-200',
  LeetCode: 'bg-amber-100 text-amber-900 ring-amber-200',
  SWEA: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  Programmers: 'bg-violet-100 text-violet-800 ring-violet-200',
  Unknown: 'bg-slate-100 text-slate-700 ring-slate-200',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded px-2 py-0.5 text-[11px] font-semibold ring-1"
    :class="palette[props.platform] ?? palette.Unknown"
  >
    {{ props.platform }}
  </span>
</template>

