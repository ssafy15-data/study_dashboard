<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value: string | null }>()

const formatted = computed(() => {
  if (!props.value) return '아직 갱신 전'
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(props.value))
})
</script>

<template>
  <span class="text-sm text-slate-500">마지막 갱신: {{ formatted }}</span>
</template>

