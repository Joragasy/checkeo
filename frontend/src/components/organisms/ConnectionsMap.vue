<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { fetchConnections, type Connections, type ConnectionStation, type DayType, type Direction, type StationHit } from '../../api'
import ConnectionsLegend from '../molecules/ConnectionsLegend.vue'
import ConnectionsTable from '../molecules/ConnectionsTable.vue'
import DirectionToggle from '../molecules/DirectionToggle.vue'
import ConnectionsMapCanvas from './ConnectionsMapCanvas.vue'

const props = defineProps<{ place: StationHit; dayType: DayType; includeBuses: boolean; selectedId?: string | null }>()
const emit = defineEmits<{ select: [StationHit] }>()

const direction = ref<Direction>('outbound')
const data = shallowRef<Connections | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showList = ref(false)
let controller: AbortController | undefined

const regular = computed(() => data.value?.stations.filter((s) => s.trains > 0) ?? [])
const occasionalOnly = computed(() => data.value?.stations.filter((s) => s.trains === 0) ?? [])

// ---------------------------------------------------------------- chargement
async function load() {
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = null
  try {
    data.value = await fetchConnections({
      from: props.place.id, day_type: props.dayType, direction: direction.value, include_buses: props.includeBuses,
    }, controller.signal)
  } catch (e) {
    if ((e as Error).name === 'AbortError') return
    error.value = (e as Error).message
    data.value = null
  } finally {
    loading.value = false
  }
}

watch([() => props.place.id, () => props.dayType, () => props.includeBuses, direction], load, { immediate: true })

onBeforeUnmount(() => {
  controller?.abort()
})

function select(s: ConnectionStation) {
  emit('select', { id: s.id, kind: 'station', name: s.name, city: s.city, n_stations: 1, modes: [] })
}

const verb = computed(() => (direction.value === 'outbound' ? 'au départ de' : "à l'arrivée à"))
</script>

<template>
  <v-card class="pa-3 pa-md-4 mb-4">
    <div class="d-flex flex-wrap align-center ga-2 mb-3">
      <div class="mr-auto">
        <h2 class="text-h6 font-weight-bold">Liaisons directes</h2>
        <div class="text-body-2 text-medium-emphasis">
          Trains sans changement {{ verb }} {{ place.name }} · {{ data?.day_type_label ?? '…' }}.
          Cliquez une gare pour en faire votre gare de travail.
        </div>
      </div>
      <DirectionToggle v-model="direction" />
    </div>

    <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-3">{{ error }}</v-alert>

    <ConnectionsMapCanvas
      :data="data" :direction="direction" :loading="loading" :selected-id="selectedId"
      :label="`Carte des liaisons directes ${verb} ${place.name}`" @select="select"
    />

    <div class="d-flex flex-wrap align-center ga-3 mt-3 text-caption text-medium-emphasis">
      <ConnectionsLegend />
      <v-spacer />
      <v-btn
        v-if="data?.stations.length" variant="text" size="small"
        :append-icon="showList ? 'mdi-chevron-up' : 'mdi-chevron-down'" @click="showList = !showList"
      >
        {{ regular.length }} gare{{ regular.length > 1 ? 's' : '' }}
        <template v-if="occasionalOnly.length"> + {{ occasionalOnly.length }} occasionnelle{{ occasionalOnly.length > 1 ? 's' : '' }}</template>
      </v-btn>
    </div>

    <v-expand-transition>
      <ConnectionsTable v-if="showList && data" :stations="data.stations" :selected-id="selectedId" @select="select" />
    </v-expand-transition>
  </v-card>
</template>
