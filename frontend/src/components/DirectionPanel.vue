<script setup lang="ts">
import { computed } from 'vue'
import type { DirectionProfile, TrainRow } from '../api'
import { duration, hLabel } from '../format'
import HourHistogram from './HourHistogram.vue'
import ReliabilityCard from './ReliabilityCard.vue'

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

const target = computed(() => (props.isOutbound ? props.data.arrive_by : props.data.leave_after)!)
const peakLabel = computed(() => {
  const [a, b] = props.data.peak.window
  return `Pointe ${hLabel(a)}–${hLabel(b)}`
})

const MODE_SHORT: Record<string, string> = {
  'TGV INOUI': 'TGV INOUI', OUIGO: 'OUIGO', 'Train TER': 'TER', 'Car TER': 'Car TER', INTERCITES: 'Intercités',
  'INTERCITES de nuit': 'Intercités de nuit', TramTrain: 'Tram-train',
}
const modeLabel = (t: TrainRow) => MODE_SHORT[t.mode] ?? t.mode
const daysLabel = (t: TrainRow) => `${t.n_days}/${counts.value.n_dates} j.`
</script>

<template>
  <section class="d-flex flex-column ga-4" :aria-label="title">
    <div>
      <div class="text-overline text-medium-emphasis">{{ title }}</div>
      <h2 class="text-h6 font-weight-medium">{{ fromName }} <v-icon icon="mdi-arrow-right" size="small" /> {{ toName }}</h2>
      <div class="text-body-2 text-medium-emphasis">
        <strong class="text-high-emphasis">{{ data.count }}</strong>
        train{{ data.count > 1 ? 's' : '' }} direct{{ data.count > 1 ? 's' : '' }} sur un jour type
        <template v-if="variability"> ({{ variability }})</template>
      </div>
    </div>

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

        <v-card class="pa-3 tile">
          <div class="text-caption text-medium-emphasis">Plus long trou entre 6h et 21h</div>
          <div class="text-h5 font-weight-bold">{{ duration(data.largest_gap.minutes) }}</div>
          <div class="text-caption text-medium-emphasis">de {{ data.largest_gap.from }} à {{ data.largest_gap.to }} (départs)</div>
        </v-card>

        <v-card class="pa-3 tile">
          <div class="text-caption text-medium-emphasis">Durée du trajet</div>
          <div class="text-h5 font-weight-bold">{{ duration(data.durations.median) }} <span class="text-body-2">médiane</span></div>
          <div class="text-caption text-medium-emphasis">
            de {{ duration(data.durations.min) }} à {{ duration(data.durations.max) }}
          </div>
        </v-card>
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
          <v-table density="compact" class="trains">
            <thead>
              <tr>
                <th>Départ</th><th>Arrivée</th><th>Durée</th><th>Train</th>
                <th v-if="multiStation">Gares</th><th class="text-right">Circule</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in data.trains" :key="t.train_number">
                <td>
                  <strong>{{ t.dep }}</strong>
                  <div v-if="t.dep_range" class="text-caption text-medium-emphasis" title="Horaire variable selon les dates">
                    {{ t.dep_range[0] }}–{{ t.dep_range[1] }}
                  </div>
                </td>
                <td>{{ t.arr }}</td>
                <td>{{ duration(t.duration_min) }}</td>
                <td><span class="text-no-wrap">{{ modeLabel(t) }}</span> <span class="text-medium-emphasis">{{ t.train_number }}</span></td>
                <td v-if="multiStation" class="text-caption">{{ t.from_name }} → {{ t.to_name }}</td>
                <td class="text-right text-caption">{{ daysLabel(t) }}</td>
              </tr>
            </tbody>
          </v-table>
          <div class="text-caption text-medium-emphasis mt-2">
            « Circule » : nombre de jours échantillonnés où le train roule. Une fourchette sous l'heure de départ
            signale un horaire qui varie selon les dates (travaux…).
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
      <v-expansion-panel v-if="data.occasional_trains.length" elevation="0" class="border">
        <v-expansion-panel-title>
          <v-icon icon="mdi-calendar-question" size="small" class="mr-2" />
          {{ data.occasional_trains.length }} train(s) certains jours seulement
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-table density="compact" class="trains">
            <thead><tr><th>Départ</th><th>Arrivée</th><th>Train</th><th>Jours</th><th class="text-right">Circule</th></tr></thead>
            <tbody>
              <tr v-for="t in data.occasional_trains" :key="t.train_number">
                <td><strong>{{ t.dep }}</strong></td>
                <td>{{ t.arr }}</td>
                <td><span class="text-no-wrap">{{ modeLabel(t) }}</span> <span class="text-medium-emphasis">{{ t.train_number }}</span></td>
                <td class="text-caption">{{ t.weekdays.join(' ') }}</td>
                <td class="text-right text-caption">{{ daysLabel(t) }}</td>
              </tr>
            </tbody>
          </v-table>
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
.tile {
  min-width: 0;
}
.trains td,
.trains th {
  padding: 4px 8px !important;
}
</style>
