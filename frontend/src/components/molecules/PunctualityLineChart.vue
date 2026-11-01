<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import type { MonthPoint } from '../../api'
import { monthLabel, pct } from '../../format'
import { useChartPalette } from '../../composables/useChartPalette'

use([LineChart, GridComponent, TooltipComponent, SVGRenderer])

/** `points` : mois dont le taux est connu (rate non nul). */
const props = defineProps<{ points: MonthPoint[]; description: string }>()
const palette = useChartPalette()

const option = computed(() => {
  const { c, muted, grid, text } = palette()
  const rates = props.points.map((p) => p.rate as number)
  const min = Math.max(0, Math.floor((Math.min(...rates, 100) - 5) / 5) * 5)
  return {
    animationDuration: 300,
    grid: { left: 4, right: 12, top: 12, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: muted, type: 'dashed' } },
      backgroundColor: c.surface,
      borderColor: grid,
      textStyle: { color: text, fontSize: 13 },
      formatter: (ps: { dataIndex: number }[]) => {
        const p = props.points[ps[0].dataIndex]
        const cancel = p.cancel_rate != null ? `<br/>Annulations : ${pct(p.cancel_rate)}` : ''
        return `${monthLabel(p.month)}<br/>Ponctualité : <b>${pct(p.rate)}</b>${cancel}`
      },
    },
    xAxis: {
      type: 'category',
      data: props.points.map((p) => p.month),
      boundaryGap: false,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: grid } },
      axisLabel: {
        color: muted,
        fontSize: 11,
        interval: (_: number, v: string) => v.endsWith('-01'),
        formatter: (v: string) => v.slice(0, 4),
      },
    },
    yAxis: {
      type: 'value',
      min,
      max: 100,
      splitNumber: 3,
      axisLabel: { color: muted, fontSize: 11, formatter: '{value} %' },
      splitLine: { lineStyle: { color: grid } },
    },
    series: [{
      type: 'line',
      data: rates,
      showSymbol: false,
      symbolSize: 8,
      lineStyle: { width: 2, color: c.series },
      itemStyle: { color: c.series, borderColor: c.surface, borderWidth: 2 },
      emphasis: { focus: 'none' },
    }],
  }
})
</script>

<template>
  <v-chart :option="option" autoresize class="line" role="img" :aria-label="description" />
</template>

<style scoped>
.line {
  height: 170px;
  width: 100%;
}
</style>
