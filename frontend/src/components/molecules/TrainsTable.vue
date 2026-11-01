<script setup lang="ts">
import type { TrainRow } from '../../api'
import { duration } from '../../format'
import { MODE_LABEL } from '../../constants/trainModes'

defineProps<{ trains: TrainRow[]; multiStation: boolean; nDates: number }>()
</script>

<template>
  <v-table density="compact" class="trains">
    <thead>
      <tr>
        <th>Départ</th><th>Arrivée</th><th>Durée</th><th>Train</th>
        <th v-if="multiStation">Gares</th><th class="text-right">Circule</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="t in trains" :key="t.train_number">
        <td>
          <strong>{{ t.dep }}</strong>
          <div v-if="t.dep_range" class="text-caption text-medium-emphasis" title="Horaire variable selon les dates">
            {{ t.dep_range[0] }}–{{ t.dep_range[1] }}
          </div>
        </td>
        <td>{{ t.arr }}</td>
        <td>{{ duration(t.duration_min) }}</td>
        <td><span class="text-no-wrap">{{ MODE_LABEL[t.mode] ?? t.mode }}</span> <span class="text-medium-emphasis">{{ t.train_number }}</span></td>
        <td v-if="multiStation" class="text-caption">{{ t.from_name }} → {{ t.to_name }}</td>
        <td class="text-right text-caption">{{ t.n_days }}/{{ nDates }} j.</td>
      </tr>
    </tbody>
  </v-table>
  <div class="text-caption text-medium-emphasis mt-2">
    « Circule » : nombre de jours échantillonnés où le train roule. Une fourchette sous l'heure de départ
    signale un horaire qui varie selon les dates (travaux…).
  </div>
</template>

<style scoped>
.trains td,
.trains th {
  padding: 4px 8px !important;
}
</style>
