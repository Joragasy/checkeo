<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useTheme } from 'vuetify'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { fetchConnections, type Connections, type ConnectionStation, type DayType, type Direction, type StationHit } from '../api'
import { duration } from '../format'

const props = defineProps<{ place: StationHit; dayType: DayType; includeBuses: boolean; selectedId?: string | null }>()
const emit = defineEmits<{ select: [StationHit] }>()

const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)

const direction = ref<Direction>('outbound')
const data = shallowRef<Connections | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showList = ref(false)
let controller: AbortController | undefined

// ---------------------------------------------------------------- échelle : trains directs par jour
// Rampe ordinale bleue de la palette data-viz (validée sur les surfaces claire et sombre) ;
// en mode sombre, les liaisons les plus fréquentes sont les plus lumineuses.
const BUCKETS = [
  { min: 1, label: '1–2' },
  { min: 3, label: '3–5' },
  { min: 6, label: '6–11' },
  { min: 12, label: '12–23' },
  { min: 24, label: '24 +' },
]
const RAMP_LIGHT = ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281']
const RAMP_DARK = ['#184f95', '#256abf', '#3987e5', '#6da7ec', '#9ec5f4']
const ramp = computed(() => (isDark.value ? RAMP_DARK : RAMP_LIGHT))
const bucketOf = (trains: number) => BUCKETS.reduce((i, b, j) => (trains >= b.min ? j : i), 0)
const radiusOf = (trains: number) => (trains > 0 ? Math.min(4 + 2.2 * Math.sqrt(trains), 18) : 3.5)

const OCCASIONAL = { light: '#8a8984', dark: '#7a7973' }
const INK = { light: '#1f1f1d', dark: '#f0efea' }
const SURFACE = { light: '#fcfcfb', dark: '#1a1a19' }
const tone = <T,>(pair: { light: T; dark: T }) => (isDark.value ? pair.dark : pair.light)

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

// ---------------------------------------------------------------- carte Leaflet
const el = ref<HTMLElement | null>(null)
let map: L.Map | undefined
let tiles: L.TileLayer | undefined
let layer: L.LayerGroup | undefined
const renderer = L.canvas({ padding: 0.5 })

const esc = (s: string) => s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)

// Fond de carte CARTO (clé gratuite : carto.com/basemaps/apikey, dans frontend/.env.local).
// Sans clé, CARTO ne renvoie qu'une image « API KEY REQUIRED » : on se rabat sur les tuiles OSM.
const CARTO_KEY = import.meta.env.VITE_CARTO_KEY
const OSM = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

function setTiles() {
  if (!map) return
  tiles?.remove()
  tiles = CARTO_KEY
    ? L.tileLayer(`https://basemaps.cartocdn.com/rastertiles/${isDark.value ? 'dark_all' : 'light_all'}/{z}/{x}/{y}{r}.png?key=${encodeURIComponent(CARTO_KEY)}`, {
      maxZoom: 19,
      attribution: `${OSM} &copy; <a href="https://carto.com/attributions">CARTO</a>`,
    })
    : L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: OSM })
  tiles.addTo(map)
}

function tooltip(s: ConnectionStation): string {
  const verb = direction.value === 'outbound' ? 'vers' : 'depuis'
  const lines = [`<strong>${esc(s.name)}</strong>`]
  lines.push(s.trains
    ? `${s.trains} train${s.trains > 1 ? 's' : ''} direct${s.trains > 1 ? 's' : ''} / jour ${verb} cette gare`
    : 'Aucun train régulier')
  if (s.occasional) lines.push(`+ ${s.occasional} occasionnel${s.occasional > 1 ? 's' : ''}`)
  lines.push(`Dès ${duration(s.min_duration_min)} · ${s.families.map(esc).join(', ')}`)
  return lines.join('<br>')
}

function hit(s: ConnectionStation): StationHit {
  return { id: s.id, kind: 'station', name: s.name, city: s.city, n_stations: 1, modes: [] }
}

function draw(fit: boolean) {
  if (!map) return
  layer?.remove()
  layer = L.layerGroup().addTo(map)
  const d = data.value
  if (!d) return
  const points: L.LatLngExpression[] = []
  // Les petites liaisons d'abord, pour que les plus fréquentes restent au-dessus.
  const ordered = [...d.stations].sort((a, b) => a.trains - b.trains)
  for (const s of ordered) {
    const selected = s.id === props.selectedId
    const m = L.circleMarker([s.lat, s.lon], {
      renderer,
      radius: radiusOf(s.trains),
      fillColor: s.trains ? ramp.value[bucketOf(s.trains)] : tone(OCCASIONAL),
      fillOpacity: s.trains ? 0.9 : 0.6,
      color: selected ? tone(INK) : tone(SURFACE),
      weight: selected ? 3 : 1.5,
    })
    m.bindTooltip(tooltip(s), { direction: 'top', offset: [0, -4] })
    m.on('click', () => emit('select', hit(s)))
    m.addTo(layer)
    points.push([s.lat, s.lon])
  }
  if (d.place.lat != null && d.place.lon != null) {
    L.circleMarker([d.place.lat, d.place.lon], {
      renderer, radius: 8, fillColor: tone(INK), fillOpacity: 1, color: tone(SURFACE), weight: 3, interactive: true,
    }).bindTooltip(`<strong>${esc(d.place.name)}</strong>`, { permanent: true, direction: 'right', offset: [8, 0], className: 'place-label' })
      .addTo(layer)
    points.push([d.place.lat, d.place.lon])
  }
  if (fit && points.length) map.fitBounds(L.latLngBounds(points), { padding: [28, 28], maxZoom: 10 })
}

onMounted(async () => {
  await nextTick()
  if (!el.value) return
  map = L.map(el.value, { zoomControl: true, scrollWheelZoom: false, attributionControl: true }).setView([46.6, 2.4], 5)
  // La molette ne zoome qu'après un clic dans la carte, pour ne pas bloquer le défilement de la page.
  map.on('click', () => map?.scrollWheelZoom.enable())
  map.on('mouseout', () => map?.scrollWheelZoom.disable())
  setTiles()
  draw(true)
})

onBeforeUnmount(() => {
  controller?.abort()
  map?.remove()
  map = undefined
})

watch(data, () => draw(true))
watch(() => props.selectedId, () => draw(false))
watch(isDark, () => { setTiles(); draw(false) })

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
      <v-btn-toggle v-model="direction" mandatory density="comfortable" variant="outlined" divided color="primary">
        <v-btn value="outbound" size="small" prepend-icon="mdi-arrow-top-right">Départs</v-btn>
        <v-btn value="inbound" size="small" prepend-icon="mdi-arrow-bottom-left">Arrivées</v-btn>
      </v-btn-toggle>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-3">{{ error }}</v-alert>

    <div class="map-wrap">
      <div ref="el" class="map" :class="{ 'osm-dark': !CARTO_KEY && isDark }" role="region" :aria-label="`Carte des liaisons directes ${verb} ${place.name}`" />
      <v-progress-linear v-if="loading" indeterminate color="primary" class="map-progress" />
      <div v-if="data && !loading && !data.stations.length" class="map-empty text-body-2">
        Aucun train direct sur ce jour type.
      </div>
    </div>

    <div class="d-flex flex-wrap align-center ga-3 mt-3 text-caption text-medium-emphasis">
      <span>Trains directs / jour :</span>
      <span v-for="(b, i) in BUCKETS" :key="b.label" class="legend-item">
        <span class="dot" :style="{ background: ramp[i], width: `${2 * radiusOf(b.min)}px`, height: `${2 * radiusOf(b.min)}px` }" />
        {{ b.label }}
      </span>
      <span class="legend-item">
        <span class="dot" :style="{ background: tone(OCCASIONAL), opacity: 0.6, width: '7px', height: '7px' }" />
        occasionnel
      </span>
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
      <v-table v-if="showList && data" density="compact" class="mt-2 station-table" fixed-header height="300">
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
            v-for="s in data.stations" :key="s.id" class="clickable" :class="{ 'font-weight-bold': s.id === selectedId }"
            tabindex="0" @click="emit('select', hit(s))" @keydown.enter="emit('select', hit(s))"
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
    </v-expand-transition>
  </v-card>
</template>

<style scoped>
.map-wrap {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.map {
  height: 420px;
  width: 100%;
  background: rgb(var(--v-theme-background));
}
@media (max-width: 599px) {
  .map {
    height: 320px;
  }
}
/* Les tuiles OSM n'ont pas de style sombre : on les assombrit. */
.osm-dark :deep(.leaflet-tile-pane) {
  filter: invert(1) hue-rotate(180deg) brightness(0.85) contrast(0.9);
}
.map-progress {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}
.map-empty {
  position: absolute;
  inset: 0;
  z-index: 900;
  display: grid;
  place-items: center;
  pointer-events: none;
  color: rgb(var(--v-theme-on-surface));
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.dot {
  display: inline-block;
  border-radius: 50%;
}
.clickable {
  cursor: pointer;
}
:deep(.leaflet-tooltip) {
  font: inherit;
  font-size: 12px;
}
:deep(.place-label) {
  font-weight: 700;
}
</style>
