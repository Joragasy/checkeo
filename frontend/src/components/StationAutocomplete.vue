<script setup lang="ts">
import { ref, watch } from 'vue'
import { searchStations, type StationHit } from '../api'

const model = defineModel<StationHit | null>({ required: true })
defineProps<{ label: string; icon: string }>()

const search = ref('')
const items = ref<StationHit[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
let timer: number | undefined
let controller: AbortController | undefined

watch(model, (v) => {
  if (v && !items.value.some((i) => i.id === v.id)) items.value = [v]
}, { immediate: true })

watch(search, (q) => {
  window.clearTimeout(timer)
  if (!q || q.trim().length < 2 || q === model.value?.name) return
  timer = window.setTimeout(async () => {
    controller?.abort()
    controller = new AbortController()
    loading.value = true
    error.value = null
    try {
      items.value = await searchStations(q, controller.signal)
    } catch (e) {
      if ((e as Error).name !== 'AbortError') error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }, 200)
})

const MODE_SHORT: Record<string, string> = {
  'TGV INOUI': 'TGV', OUIGO: 'OUIGO', 'Train TER': 'TER', INTERCITES: 'IC', 'INTERCITES de nuit': 'IC nuit',
  TramTrain: 'Tram-train', ICE: 'ICE', Lyria: 'Lyria',
}
const modes = (m: string[]) => [...new Set(m.map((x) => MODE_SHORT[x]).filter(Boolean))].join(' · ')
</script>

<template>
  <v-autocomplete
    v-model="model"
    v-model:search="search"
    :items="items"
    :loading="loading"
    :label="label"
    :prepend-inner-icon="icon"
    :error-messages="error ?? undefined"
    item-title="name"
    item-value="id"
    return-object
    no-filter
    clearable
    hide-details="auto"
    variant="outlined"
    density="comfortable"
    no-data-text="Tapez au moins 2 lettres (ex. « Lille »)"
    auto-select-first
  >
    <template #item="{ props: itemProps, item }">
      <v-list-item v-bind="itemProps" :subtitle="modes(item.raw.modes)">
        <template #prepend>
          <v-icon :icon="item.raw.kind === 'city' ? 'mdi-city-variant-outline' : 'mdi-train'" size="small" />
        </template>
        <template v-if="item.raw.kind === 'city'" #append>
          <v-chip size="x-small" variant="tonal" color="primary">{{ item.raw.n_stations }} gares</v-chip>
        </template>
      </v-list-item>
    </template>
  </v-autocomplete>
</template>
