<script setup lang="ts">
import LegendDot from '../atoms/LegendDot.vue'
import { BUCKETS, OCCASIONAL, radiusOf } from '../../constants/connectionsScale'
import { useConnectionTone } from '../../composables/useConnectionTone'

const { ramp, tone } = useConnectionTone()
</script>

<template>
  <span>Trains directs / jour :</span>
  <span v-for="(b, i) in BUCKETS" :key="b.label" class="legend-item">
    <LegendDot :color="ramp[i]" :size="`${2 * radiusOf(b.min)}px`" />
    {{ b.label }}
  </span>
  <span class="legend-item">
    <LegendDot :color="tone(OCCASIONAL)" :opacity="0.6" size="7px" />
    occasionnel
  </span>
</template>

<style scoped>
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>
