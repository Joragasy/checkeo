<script setup lang="ts">
import type { Cause } from '../../api'
import { pct } from '../../format'

defineProps<{ cause: Cause }>()
</script>

<template>
  <div class="cause">
    <div class="cause-label text-body-2">{{ cause.label }}</div>
    <div class="cause-track">
      <div class="cause-bar" :style="{ width: `${Math.max(cause.percent, 0.5)}%` }" />
    </div>
    <div class="cause-value text-body-2">{{ pct(cause.percent, 0) }}</div>
  </div>
</template>

<style scoped>
.cause {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(60px, 30%) 3.2em;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}
.cause-label {
  line-height: 1.25;
}
.cause-track {
  height: 10px;
}
.cause-bar {
  height: 100%;
  background: rgb(var(--v-theme-series));
  border-radius: 0 4px 4px 0;
}
.cause-value {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
</style>
