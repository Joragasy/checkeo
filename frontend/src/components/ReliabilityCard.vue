<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTheme } from 'vuetify'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import type { ReliabilityBlock } from '../api'
import { dateLabel, monthLabel, pct } from '../format'

use([LineChart, GridComponent, TooltipComponent, SVGRenderer])

const props = defineProps<{ block: ReliabilityBlock }>()
const theme = useTheme()
const showTable = ref(false)

const points = computed(() => (props.block.monthly ?? []).filter((m) => m.rate != null))

const option = computed(() => {
  const c = theme.current.value.colors
  const dark = theme.current.value.dark
  const muted = dark ? '#a3a299' : '#6b6a66'
  const grid = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.07)'
  const rates = points.value.map((p) => p.rate as number)
  const min = Math.max(0, Math.floor((Math.min(...rates, 100) - 5) / 5) * 5)
  return {
    animationDuration: 300,
    grid: { left: 4, right: 12, top: 12, bottom: 4, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: muted, type: 'dashed' } },
      backgroundColor: c.surface,
      borderColor: grid,
      textStyle: { color: dark ? '#f0efec' : '#0b0b0b', fontSize: 13 },
      formatter: (ps: { dataIndex: number }[]) => {
        const p = points.value[ps[0].dataIndex]
        const cancel = p.cancel_rate != null ? `<br/>Annulations : ${pct(p.cancel_rate)}` : ''
        return `${monthLabel(p.month)}<br/>Ponctualité : <b>${pct(p.rate)}</b>${cancel}`
      },
    },
    xAxis: {
      type: 'category',
      data: points.value.map((p) => p.month),
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

const scopeLabel = computed(() => (props.block.scope === 'region' ? 'Moyenne régionale' : 'Liaison'))
</script>

<template>
  <v-card class="pa-4">
    <div class="d-flex align-center flex-wrap ga-2 mb-2">
      <v-icon icon="mdi-clock-check-outline" size="small" />
      <span class="text-subtitle-1 font-weight-medium">Fiabilité {{ block.family_label }}</span>
      <v-chip size="x-small" variant="tonal" :color="block.scope === 'region' ? 'warning' : 'primary'">
        {{ scopeLabel }}
      </v-chip>
      <span v-if="block.label" class="text-body-2 text-medium-emphasis">{{ block.label }}</span>
    </div>

    <v-alert v-if="!block.available" type="info" variant="tonal" density="compact" icon="mdi-database-off-outline">
      <div class="font-weight-medium">Donnée indisponible</div>
      <div class="text-body-2">{{ block.note }}</div>
    </v-alert>

    <template v-else>
      <v-alert
        v-if="block.stale" type="warning" variant="tonal" density="compact" class="mb-3"
        icon="mdi-calendar-alert"
      >
        Données anciennes : dernier mois publié {{ monthLabel(block.last_month) }}
        ({{ block.lag_months }} mois de décalage).
      </v-alert>

      <div class="d-flex flex-wrap ga-6 mb-1">
        <div>
          <div class="text-h4 font-weight-bold">{{ pct(block.punctuality) }}</div>
          <div class="text-caption text-medium-emphasis">
            trains à l'heure · {{ monthLabel(block.window?.from) }} – {{ monthLabel(block.window?.to) }}
          </div>
        </div>
        <div v-if="block.cancel_rate != null">
          <div class="text-h5 font-weight-medium mt-1">{{ pct(block.cancel_rate, 2) }}</div>
          <div class="text-caption text-medium-emphasis">trains annulés</div>
        </div>
      </div>
      <p class="text-body-2 text-medium-emphasis mb-2">{{ block.note }}</p>

      <div class="text-caption text-medium-emphasis mt-2">Ponctualité mensuelle (36 derniers mois publiés)</div>
      <v-chart
        v-if="points.length > 1" :option="option" autoresize class="line" role="img"
        :aria-label="`Évolution mensuelle de la ponctualité ${block.family_label}`"
      />

      <div v-if="block.causes?.length" class="mt-3">
        <div class="text-caption text-medium-emphasis mb-1">Causes des retards (12 mois, pondérées par le nombre de trains en retard)</div>
        <div v-for="c in block.causes" :key="c.key" class="cause">
          <div class="cause-label text-body-2">{{ c.label }}</div>
          <div class="cause-track">
            <div class="cause-bar" :style="{ width: `${Math.max(c.percent, 0.5)}%` }" />
          </div>
          <div class="cause-value text-body-2">{{ pct(c.percent, 0) }}</div>
        </div>
      </div>

      <v-btn
        variant="text" size="small" class="mt-2 px-1" :prepend-icon="showTable ? 'mdi-chevron-up' : 'mdi-table'"
        @click="showTable = !showTable"
      >
        {{ showTable ? 'Masquer les données' : 'Voir les données' }}
      </v-btn>
      <v-table v-if="showTable" density="compact" class="mt-1 data-table">
        <thead>
          <tr><th>Mois</th><th class="text-right">Ponctualité</th><th class="text-right">Annulations</th><th class="text-right">Trains prévus</th></tr>
        </thead>
        <tbody>
          <tr v-for="m in [...(block.monthly ?? [])].reverse()" :key="m.month">
            <td>{{ monthLabel(m.month) }}</td>
            <td class="text-right">{{ pct(m.rate) }}</td>
            <td class="text-right">{{ pct(m.cancel_rate, 2) }}</td>
            <td class="text-right">{{ m.planned?.toLocaleString('fr-FR') ?? '—' }}</td>
          </tr>
        </tbody>
      </v-table>
    </template>

    <div class="text-caption text-medium-emphasis mt-3">
      <template v-if="block.last_month">Données jusqu'à {{ monthLabel(block.last_month) }} · </template>
      jeu de régularité mis à jour le {{ dateLabel(block.dataset_modified) }}
    </div>
  </v-card>
</template>

<style scoped>
.line {
  height: 170px;
  width: 100%;
}
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
.data-table {
  max-height: 260px;
  overflow-y: auto;
}
</style>
