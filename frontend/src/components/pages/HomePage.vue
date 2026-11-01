<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { fetchMeta, fetchProfile, type DayType, type Meta, type Profile, type StationHit } from '../../api'
import { useThemePreference } from '../../composables/useThemePreference'
import IntroPrompt from '../molecules/IntroPrompt.vue'
import ProfileSummary from '../molecules/ProfileSummary.vue'
import ConnectionsMap from '../organisms/ConnectionsMap.vue'
import HeroBanner from '../organisms/HeroBanner.vue'
import ProfileResults from '../organisms/ProfileResults.vue'
import SearchCard from '../organisms/SearchCard.vue'
import DefaultLayout from '../templates/DefaultLayout.vue'

const { initTheme } = useThemePreference()

// ---------------------------------------------------------------- formulaire
const home = ref<StationHit | null>(null)
const work = ref<StationHit | null>(null)
const dayType = ref<DayType>('weekday')
const settings = reactive({ bin: 60, arriveBy: '09:00', leaveAfter: '18:00', includeBuses: false })

const profile = ref<Profile | null>(null)
const meta = ref<Meta | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const tab = ref<'outbound' | 'inbound'>('outbound')
let controller: AbortController | undefined

async function load() {
  if (!home.value || !work.value) return
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = null
  try {
    profile.value = await fetchProfile({
      from: home.value.id,
      to: work.value.id,
      day_type: dayType.value,
      bin: settings.bin,
      arrive_by: settings.arriveBy,
      leave_after: settings.leaveAfter,
      include_buses: settings.includeBuses,
    }, controller.signal)
    syncUrl()
  } catch (e) {
    if ((e as Error).name === 'AbortError') return
    error.value = (e as Error).message
    profile.value = null
  } finally {
    loading.value = false
  }
}

watch([home, work, dayType, () => settings.bin, () => settings.includeBuses], load)

// ---------------------------------------------------------------- état partageable dans l'URL
function syncUrl() {
  if (!home.value || !work.value) return
  const q = new URLSearchParams({
    from: home.value.id, fromName: home.value.name, fromKind: home.value.kind,
    to: work.value.id, toName: work.value.name, toKind: work.value.kind,
    day: dayType.value,
  })
  if (settings.bin !== 60) q.set('bin', String(settings.bin))
  if (settings.arriveBy !== '09:00') q.set('arrive', settings.arriveBy)
  if (settings.leaveAfter !== '18:00') q.set('leave', settings.leaveAfter)
  if (settings.includeBuses) q.set('cars', '1')
  history.replaceState(null, '', `?${q}`)
}

function readUrl() {
  const q = new URLSearchParams(location.search)
  const hit = (id: string | null, name: string | null, kind: string | null): StationHit | null =>
    id && name ? { id, name, kind: kind === 'city' ? 'city' : 'station', city: null, n_stations: 1, modes: [] } : null
  const d = q.get('day')
  if (d === 'weekday' || d === 'saturday' || d === 'sunday') dayType.value = d
  if (q.get('bin')) settings.bin = Number(q.get('bin')) || 60
  if (q.get('arrive')) settings.arriveBy = q.get('arrive')!
  if (q.get('leave')) settings.leaveAfter = q.get('leave')!
  settings.includeBuses = q.get('cars') === '1'
  home.value = hit(q.get('from'), q.get('fromName'), q.get('fromKind'))
  work.value = hit(q.get('to'), q.get('toName'), q.get('toKind'))
}

function example() {
  home.value = { id: 'city:59350', name: 'Lille (toutes gares)', kind: 'city', city: 'Lille', n_stations: 0, modes: [] }
  work.value = { id: 'city:75056', name: 'Paris (toutes gares)', kind: 'city', city: 'Paris', n_stations: 0, modes: [] }
}

onMounted(async () => {
  initTheme()
  readUrl()
  try { meta.value = await fetchMeta() } catch { /* le pied de page reste minimal */ }
})

// const m = computed(() => profile.value?.meta ?? meta.value)
// const SOURCE_ORDER = ['gtfs', 'tgv', 'ter', 'intercites', 'gares', 'communes']
</script>

<template>
  <DefaultLayout>
    <HeroBanner />

    <v-container class="page pt-0 pb-4 pb-md-6">
      <SearchCard
        v-model:home="home" v-model:work="work" v-model:day-type="dayType"
        v-model:arrive-by="settings.arriveBy" v-model:leave-after="settings.leaveAfter"
        v-model:bin="settings.bin" v-model:include-buses="settings.includeBuses"
        @commit="load"
      />

      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

      <ConnectionsMap
        v-if="home" :place="home" :day-type="dayType" :include-buses="settings.includeBuses"
        :selected-id="work?.id" @select="work = $event"
      />

      <IntroPrompt v-if="!profile && !loading" @example="example" />

      <div v-if="loading && !profile" class="d-flex flex-column ga-4">
        <v-skeleton-loader type="article" />
        <v-skeleton-loader type="image" />
      </div>

      <template v-if="profile">
        <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
        <ProfileSummary :profile="profile" />
        <ProfileResults v-model:tab="tab" :profile="profile" />
      </template>
    </v-container>
  </DefaultLayout>
</template>

<style scoped>
.page {
  max-width: 1280px;
}
</style>
