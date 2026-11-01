<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Connections, ConnectionStation, Direction } from '../../api'
import { duration } from '../../format'
import { INK, OCCASIONAL, SURFACE, bucketOf, radiusOf } from '../../constants/connectionsScale'
import { useConnectionTone } from '../../composables/useConnectionTone'

const props = defineProps<{
  data: Connections | null
  direction: Direction
  loading: boolean
  selectedId?: string | null
  label: string
}>()
const emit = defineEmits<{ select: [ConnectionStation] }>()

const { isDark, ramp, tone } = useConnectionTone()

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
  const verb = props.direction === 'outbound' ? 'vers' : 'depuis'
  const lines = [`<strong>${esc(s.name)}</strong>`]
  lines.push(s.trains
    ? `${s.trains} train${s.trains > 1 ? 's' : ''} direct${s.trains > 1 ? 's' : ''} / jour ${verb} cette gare`
    : 'Aucun train régulier')
  if (s.occasional) lines.push(`+ ${s.occasional} occasionnel${s.occasional > 1 ? 's' : ''}`)
  lines.push(`Dès ${duration(s.min_duration_min)} · ${s.families.map(esc).join(', ')}`)
  return lines.join('<br>')
}

function draw(fit: boolean) {
  if (!map) return
  layer?.remove()
  layer = L.layerGroup().addTo(map)
  const d = props.data
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
    m.on('click', () => emit('select', s))
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
  map?.remove()
  map = undefined
})

watch(() => props.data, () => draw(true))
watch(() => props.selectedId, () => draw(false))
watch(isDark, () => { setTiles(); draw(false) })
</script>

<template>
  <div class="map-wrap">
    <div ref="el" class="map" :class="{ 'osm-dark': !CARTO_KEY && isDark }" role="region" :aria-label="label" />
    <v-progress-linear v-if="loading" indeterminate color="primary" class="map-progress" />
    <div v-if="data && !loading && !data.stations.length" class="map-empty text-body-2">
      Aucun train direct sur ce jour type.
    </div>
  </div>
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
:deep(.leaflet-tooltip) {
  font: inherit;
  font-size: 12px;
}
:deep(.place-label) {
  font-weight: 700;
}
</style>
