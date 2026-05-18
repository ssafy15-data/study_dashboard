<script setup lang="ts">
import type { Milestone } from '@/types'

defineProps<{
  milestones: Milestone[]
  modelValue: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

function onChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  emit('update:modelValue', value ? Number(value) : null)
}
</script>

<template>
  <label class="flex items-center gap-2 text-sm font-medium text-slate-700">
    회차
    <select
      class="h-10 min-w-48 rounded border border-slate-300 bg-white px-3 text-sm shadow-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
      :value="modelValue ?? ''"
      @change="onChange"
    >
      <option value="" disabled>회차 선택</option>
      <option v-for="milestone in milestones" :key="milestone.id" :value="milestone.id">
        {{ milestone.title }}
      </option>
    </select>
  </label>
</template>
