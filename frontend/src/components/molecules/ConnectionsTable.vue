<script setup lang="ts">
import type { ConnectionStation } from '../../api'
import { duration } from '../../format'

defineProps<{ stations: ConnectionStation[]; selectedId?: string | null }>()
const emit = defineEmits<{ select: [ConnectionStation] }>()
</script>

<template>
  <v-table density="compact" class="mt-2 station-table" fixed-header height="300">
    <thead>
      <tr>
        <th>Gare</th>
        <th class="text-right">Trains / jour</th>
        <th class="text-right">Plus rapide</th>
        <th class="d-none d-sm-table-cell">Trains</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="s in stations" :key="s.id" class="clickable" :class="{ 'font-weight-bold': s.id === selectedId }"
        tabindex="0" @click="emit('select', s)" @keydown.enter="emit('select', s)"
      >
        <td>{{ s.name }}</td>
        <td class="text-right">
          {{ s.trains }}<span v-if="s.occasional" class="text-medium-emphasis"> (+{{ s.occasional }})</span>
        </td>
        <td class="text-right">{{ duration(s.min_duration_min) }}</td>
        <td class="d-none d-sm-table-cell text-medium-emphasis">{{ s.families.join(', ') }}</td>
      </tr>
    </tbody>
  </v-table>
</template>

<style scoped>
.clickable {
  cursor: pointer;
}
</style>
