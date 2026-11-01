<script setup lang="ts">
import type { TrainRow } from '../../api'
import { MODE_LABEL } from '../../constants/trainModes'

defineProps<{ trains: TrainRow[]; nDates: number }>()
</script>

<template>
  <v-table density="compact" class="trains">
    <thead><tr><th>Départ</th><th>Arrivée</th><th>Train</th><th>Jours</th><th class="text-right">Circule</th></tr></thead>
    <tbody>
      <tr v-for="t in trains" :key="t.train_number">
        <td><strong>{{ t.dep }}</strong></td>
        <td>{{ t.arr }}</td>
        <td><span class="text-no-wrap">{{ MODE_LABEL[t.mode] ?? t.mode }}</span> <span class="text-medium-emphasis">{{ t.train_number }}</span></td>
        <td class="text-caption">{{ t.weekdays.join(' ') }}</td>
        <td class="text-right text-caption">{{ t.n_days }}/{{ nDates }} j.</td>
      </tr>
    </tbody>
  </v-table>
</template>

<style scoped>
.trains td,
.trains th {
  padding: 4px 8px !important;
}
</style>
