<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from 'vuetify'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, MarkAreaComponent, TooltipComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import type { Bin } from '../api'
import { hhmm, hLabel } from '../format'

use([BarChart, GridComponent, TooltipComponent, MarkAreaComponent, SVGRenderer])

const props = defineProps<{
  bins: Bin[]
  peak: [number, number]
  peakLabel: string
  description: string
}>()

const theme = useTheme()

// Plage affichée : de 4h à minuit, élargie si des trains circulent en dehors.
const shown = computed(() => {
  const nonEmpty = props.bins.filter((b) => b.count > 0)
  const first = Math.min(4 * 3600, ...nonEmpty.map((b) => b.start_s))
  const last = Math.max(24 * 3600, ...nonEmpty.map((b) => b.end_s))
  return props.bins.filter((b) => b.start_s >= first && b.end_s <= last)
})

const option = computed(() => {
  const c = theme.current.value.colors
  const dark = theme.current.value.dark
  const muted = dark ? '#a3a299' : '#6b6a66'
  const grid = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.07)'
  const bins = shown.value
  const peakIdx = bins
    .map((b, i) => (b.start_s >= props.peak[0] && b.end_s <= props.peak[1] ? i : -1))
    .filter((i) => i >= 0)
  const step = bins.length ? bins[0].end_s - bins[0].start_s : 3600
  return {
    animationDuration: 300,
    grid: { left: 4, right: 8, top: 30, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow', shadowStyle: { color: dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)' } },
      backgroundColor: c.surface,
      borderColor: grid,
      textStyle: { color: dark ? '#f0efec' : '#0b0b0b', fontSize: 13 },
      formatter: (ps: { dataIndex: number }[]) => {
        const b = bins[ps[0].dataIndex]
        const n = b.count
        return `${hhmm(b.start_s)} – ${hhmm(b.end_s)}<br/><b>${n}</b> train${n > 1 ? 's' : ''}`
      },
    },
    xAxis: {
      type: 'category',
      data: bins.map((b) => b.start_s),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: grid } },
      axisLabel: {
        color: muted,
        fontSize: 11,
        interval: (_: number, v: string) => Number(v) % (3 * 3600) === 0,
        formatter: (v: string) => hLabel(Number(v)),
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitNumber: 3,
      axisLabel: { color: muted, fontSize: 11 },
      splitLine: { lineStyle: { color: grid } },
    },
    series: [{
      type: 'bar',
      data: bins.map((b) => b.count),
      barMaxWidth: 24,
      barCategoryGap: step <= 1800 ? '12%' : '20%',
      itemStyle: { color: c.series, borderRadius: [4, 4, 0, 0] },
      emphasis: { itemStyle: { color: c.primary } },
      markArea: peakIdx.length ? {
        silent: true,
        itemStyle: { color: dark ? 'rgba(57,135,229,0.10)' : 'rgba(42,120,214,0.07)' },
        label: { show: true, position: 'top', distance: 4, color: muted, fontSize: 11, formatter: props.peakLabel },
        data: [[{ xAxis: peakIdx[0] }, { xAxis: peakIdx[peakIdx.length - 1] }]],
      } : undefined,
    }],
  }
})
</script>

<template>
  <v-chart :option="option" autoresize class="histogram" role="img" :aria-label="description" />
</template>

<style scoped>
.histogram {
  height: 200px;
  width: 100%;
}
</style>
