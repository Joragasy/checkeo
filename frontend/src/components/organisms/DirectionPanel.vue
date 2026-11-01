<script setup lang="ts">
import { computed } from 'vue'
import type { DirectionProfile } from '../../api'
import { duration, hLabel } from '../../format'
import DirectionHeading from '../molecules/DirectionHeading.vue'
import HourHistogram from '../molecules/HourHistogram.vue'
import OccasionalTrainsTable from '../molecules/OccasionalTrainsTable.vue'
import StatTile from '../molecules/StatTile.vue'
import TrainsTable from '../molecules/TrainsTable.vue'

const props = defineProps<{
  title: string
  fromName: string
  toName: string
  data: DirectionProfile
  isOutbound: boolean
  multiStation: boolean
}>()

const counts = computed(() => props.data.daily_counts)
const variability = computed(() => {
  const c = counts.value
  if (c.min == null || c.max == null || c.min === c.max) return null
  return `${c.min} à ${c.max} selon les jours`
})

const peakLabel = computed(() => {
  const [a, b] = props.data.peak.window
  return `Pointe ${hLabel(a)}–${hLabel(b)}`
})
</script>

<template>
  <section class="d-flex flex-column ga-4" :aria-label="title">
    <DirectionHeading :title="title" :from-name="fromName" :to-name="toName" :count="data.count" :variability="variability" />

    <v-alert v-if="data.count === 0" type="info" variant="tonal" icon="mdi-train-variant">
      Aucun train direct régulier sur ce trajet pour ce type de jour.
      <template v-if="data.occasional_trains.length">
        {{ data.occasional_trains.length }} train(s) circule(nt) certains jours seulement (voir plus bas).
      </template>
    </v-alert>

    <template v-else>
      <div class="tiles">
        <!-- <v-card class="pa-3 tile">
          <div class="text-caption text-medium-emphasis">
            {{ isOutbound ? `Arriver avant ${hLabel(target.target_s)}` : `Partir après ${hLabel(target.target_s)}` }}
          </div>
          <div class="text-h5 font-weight-bold">{{ target.count }} <span class="text-body-2">train{{ target.count > 1 ? 's' : '' }}</span></div>
          <div v-if="isOutbound && target.last" class="text-body-2">
            Dernier : départ <strong>{{ target.last.dep }}</strong>, arrivée {{ target.last.arr }}
          </div>
          <div v-if="isOutbound && target.first" class="text-caption text-medium-emphasis">
            Premier du matin : {{ target.first.dep }} → {{ target.first.arr }}
          </div>
          <div v-if="!isOutbound && target.first" class="text-body-2">
            Premier : <strong>{{ target.first.dep }}</strong> → {{ target.first.arr }}
          </div>
          <div v-if="!isOutbound && target.last" class="text-caption text-medium-emphasis">
            Dernier de la journée : {{ target.last.dep }} → {{ target.last.arr }}
          </div>
          <div v-if="!target.count" class="text-caption text-medium-emphasis">Aucun train ne convient.</div>
        </v-card>

        <v-card class="pa-3 tile">
          <div class="text-caption text-medium-emphasis">{{ peakLabel }} ({{ data.peak.by === 'arr' ? 'arrivée' : 'départ' }})</div>
          <div class="text-h5 font-weight-bold">{{ data.peak.count }} <span class="text-body-2">train{{ data.peak.count > 1 ? 's' : '' }}</span></div>
        </v-card> -->

        <StatTile
          label="Plus long trou entre 6h et 21h"
          :caption="`de ${data.largest_gap.from} à ${data.largest_gap.to} (départs)`"
        >{{ duration(data.largest_gap.minutes) }}</StatTile>

        <StatTile
          label="Durée du trajet"
          :caption="`de ${duration(data.durations.min)} à ${duration(data.durations.max)}`"
        >{{ duration(data.durations.median) }} <span class="text-body-2">médiane</span></StatTile>
      </div>

      <v-card class="pa-3">
        <div class="text-body-2 font-weight-medium">
          Trains par heure {{ data.histogram_by === 'arr' ? "d'arrivée" : 'de départ' }}
        </div>
        <HourHistogram
          :bins="data.histogram"
          :peak="data.peak.window"
          :peak-label="peakLabel"
          :description="`Histogramme des trains par heure, ${fromName} vers ${toName}`"
        />
      </v-card>
    </template>

    <v-expansion-panels v-if="data.count || data.occasional_trains.length" variant="accordion">
      <v-expansion-panel v-if="data.count" elevation="0" class="border">
        <v-expansion-panel-title>
          <v-icon icon="mdi-format-list-bulleted" size="small" class="mr-2" /> Liste des {{ data.count }} trains
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <TrainsTable :trains="data.trains" :multi-station="multiStation" :n-dates="counts.n_dates" />
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel v-if="data.occasional_trains.length" elevation="0" class="border">
        <v-expansion-panel-title>
          <v-icon icon="mdi-calendar-question" size="small" class="mr-2" />
          {{ data.occasional_trains.length }} train(s) certains jours seulement
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <OccasionalTrainsTable :trains="data.occasional_trains" :n-dates="counts.n_dates" />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- <ReliabilityCard v-for="(b, i) in data.reliability" :key="`${b.family}-${i}`" :block="b" /> -->
  </section>
</template>

<style scoped>
.tiles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
</style>
