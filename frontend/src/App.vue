<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useDisplay, useTheme } from 'vuetify'
import { fetchMeta, fetchProfile, type DayType, type Meta, type Profile, type StationHit } from './api'
import { dateLabel, monthLabel } from './format'
import DirectionPanel from './components/DirectionPanel.vue'
import StationAutocomplete from './components/StationAutocomplete.vue'

const theme = useTheme()
const { mdAndUp } = useDisplay()

// ---------------------------------------------------------------- thème clair / sombre
const THEME_KEY = 'checkeo-theme'
function storedTheme(): string | null {
  try { return localStorage.getItem(THEME_KEY) } catch { return null }
}
function applyTheme(name: 'light' | 'dark', persist: boolean) {
  theme.global.name.value = name
  document.documentElement.dataset.theme = name
  if (persist) try { localStorage.setItem(THEME_KEY, name) } catch { /* stockage indisponible */ }
}
const isDark = computed(() => theme.global.current.value.dark)
const toggleTheme = () => applyTheme(isDark.value ? 'light' : 'dark', true)

// ---------------------------------------------------------------- formulaire
const home = ref<StationHit | null>(null)
const work = ref<StationHit | null>(null)
const dayType = ref<DayType>('weekday')
const settings = reactive({ bin: 60, arriveBy: '09:00', leaveAfter: '18:00', includeBuses: false })
const showSettings = ref(false)

const profile = ref<Profile | null>(null)
const meta = ref<Meta | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const tab = ref<'outbound' | 'inbound'>('outbound')
let controller: AbortController | undefined

function swap() {
  ;[home.value, work.value] = [work.value, home.value]
}

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
  const saved = storedTheme()
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  applyTheme(saved === 'dark' || saved === 'light' ? saved : prefersDark ? 'dark' : 'light', false)
  readUrl()
  try { meta.value = await fetchMeta() } catch { /* le pied de page reste minimal */ }
})

const fromName = computed(() => profile.value?.from.name ?? '')
const toName = computed(() => profile.value?.to.name ?? '')
const sampleDates = computed(() => profile.value?.meta.sample_dates ?? [])
const m = computed(() => profile.value?.meta ?? meta.value)

const DAY_TYPES: { value: DayType; title: string; short: string }[] = [
  { value: 'weekday', title: 'Jour de semaine', short: 'Semaine' },
  { value: 'saturday', title: 'Samedi', short: 'Samedi' },
  { value: 'sunday', title: 'Dimanche', short: 'Dimanche' },
]
const SOURCE_ORDER = ['gtfs', 'tgv', 'ter', 'intercites', 'gares', 'communes']
</script>

<template>
  <v-app>
    <v-app-bar flat border density="comfortable" color="surface">
      <template #prepend>
        <img src="/favicon.svg" alt="" width="28" height="28" class="ml-2" />
      </template>
      <v-app-bar-title class="font-weight-bold">Checkeo</v-app-bar-title>
      <span class="text-body-2 text-medium-emphasis d-none d-sm-inline mr-2">Profil navetteur en train</span>
      <v-btn
        :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
        :aria-label="isDark ? 'Passer en mode clair' : 'Passer en mode sombre'"
        variant="text" @click="toggleTheme"
      />
    </v-app-bar>

    <v-main>
      <section class="hero">
        <div class="hero-bg" role="img" aria-label="TGV Duplex sur le viaduc de Cize-Bolozon, au-dessus de l'Ain" />
        <div class="hero-inner page mx-auto">
          <h1 class="hero-title">Votre trajet, en un coup d'œil</h1>
          <p class="hero-sub">Trains directs et ponctualité réelle.</p>
        </div>
        <a
          class="hero-credit"
          href="https://commons.wikimedia.org/wiki/File:SNCF_TGV_Duplex_Viaduc_de_Cize_-_Bolozon.jpg"
          target="_blank" rel="noopener"
        >Photo : Kabelleger / David Gubler, CC BY-SA 3.0 (recadrée)</a>
      </section>

      <v-container class="page pt-0 pb-4 pb-md-6">
        <v-card class="search-card pa-3 pa-md-4 mb-4" elevation="4" :border="false">
          <div class="search">
            <StationAutocomplete v-model="home" label="Domicile (gare de départ)" icon="mdi-home-outline" />
            <v-btn
              icon="mdi-swap-horizontal" variant="text" class="swap" aria-label="Inverser domicile et travail"
              :disabled="!home && !work" @click="swap"
            />
            <StationAutocomplete v-model="work" label="Travail (gare d'arrivée)" icon="mdi-briefcase-outline" />
          </div>
          <div class="d-flex flex-wrap align-center ga-2 mt-3">
            <v-btn-toggle v-model="dayType" mandatory density="comfortable" variant="outlined" divided color="primary">
              <v-btn v-for="d in DAY_TYPES" :key="d.value" :value="d.value" size="small">
                <span class="d-none d-sm-inline">{{ d.title }}</span><span class="d-sm-none">{{ d.short }}</span>
              </v-btn>
            </v-btn-toggle>
            <v-spacer />
            <v-btn variant="text" size="small" prepend-icon="mdi-tune-variant" @click="showSettings = !showSettings">
              Réglages
            </v-btn>
          </div>
          <v-expand-transition>
            <div v-if="showSettings" class="settings mt-3">
              <v-text-field
                v-model="settings.arriveBy" type="time" label="Arriver au travail avant" density="compact"
                variant="outlined" hide-details @change="load"
              />
              <v-text-field
                v-model="settings.leaveAfter" type="time" label="Repartir après" density="compact"
                variant="outlined" hide-details @change="load"
              />
              <v-select
                v-model="settings.bin" :items="[{ title: '30 min', value: 30 }, { title: '1 heure', value: 60 }]"
                label="Pas de l'histogramme" density="compact" variant="outlined" hide-details
              />
              <v-switch
                v-model="settings.includeBuses" label="Inclure les cars TER" color="primary" density="compact"
                hide-details inset
              />
            </div>
          </v-expand-transition>
        </v-card>

        <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>

        <div v-if="!profile && !loading" class="intro text-center py-6 px-2">
          <p class="text-body-1 text-medium-emphasis mb-4">
            Choisissez une gare (ou une ville entière) côté domicile et côté travail. Checkeo montre
            la répartition des trains directs sur une journée type, à l'aller et au retour, et la
            ponctualité historique publiée par la SNCF.
          </p>
          <v-btn color="primary" variant="tonal" prepend-icon="mdi-lightbulb-on-outline" @click="example">
            Exemple : Lille → Paris
          </v-btn>
        </div>

        <div v-if="loading && !profile" class="d-flex flex-column ga-4">
          <v-skeleton-loader type="article" />
          <v-skeleton-loader type="image" />
        </div>

        <template v-if="profile">
          <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-2" />
          <div class="text-body-2 text-medium-emphasis mb-4">
            <v-icon icon="mdi-calendar-range" size="small" />
            {{ profile.day_type_label }} : trains présents sur au moins
            {{ Math.round(profile.meta.presence_threshold * 100) }} % des {{ sampleDates.length }} dates étudiées
            (du {{ dateLabel(sampleDates[0]) }} au {{ dateLabel(sampleDates[sampleDates.length - 1]) }}, jours fériés exclus).
            Horaires valables du {{ dateLabel(profile.meta.feed_start) }} au {{ dateLabel(profile.meta.feed_end) }}.
          </div>

          <v-row v-if="mdAndUp">
            <v-col cols="6">
              <DirectionPanel
                title="Aller" :from-name="fromName" :to-name="toName" :data="profile.outbound" is-outbound
                :multi-station="profile.from.kind === 'city' || profile.to.kind === 'city'"
              />
            </v-col>
            <v-col cols="6">
              <DirectionPanel
                title="Retour" :from-name="toName" :to-name="fromName" :data="profile.inbound" :is-outbound="false"
                :multi-station="profile.from.kind === 'city' || profile.to.kind === 'city'"
              />
            </v-col>
          </v-row>
          <template v-else>
            <v-tabs v-model="tab" grow color="primary" class="mb-3">
              <v-tab value="outbound">Aller · {{ profile.outbound.count }}</v-tab>
              <v-tab value="inbound">Retour · {{ profile.inbound.count }}</v-tab>
            </v-tabs>
            <v-window v-model="tab">
              <v-window-item value="outbound">
                <DirectionPanel
                  title="Aller" :from-name="fromName" :to-name="toName" :data="profile.outbound" is-outbound
                  :multi-station="profile.from.kind === 'city' || profile.to.kind === 'city'"
                />
              </v-window-item>
              <v-window-item value="inbound">
                <DirectionPanel
                  title="Retour" :from-name="toName" :to-name="fromName" :data="profile.inbound" :is-outbound="false"
                  :multi-station="profile.from.kind === 'city' || profile.to.kind === 'city'"
                />
              </v-window-item>
            </v-window>
          </template>
        </template>
      </v-container>
    </v-main>

    <v-footer border class="text-caption text-medium-emphasis d-block py-4">
      <div class="page mx-auto">
        
      </div>
    </v-footer>
  </v-app>
</template>

<style scoped>
.page {
  max-width: 1280px;
}
/* Bandeau photo : la carte de recherche vient chevaucher son bas. */
.hero {
  position: relative;
  height: 320px;
  overflow: hidden;
  color: #fff;
}
.hero-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 0%, rgba(0, 0, 0, 0.2) 45%, rgba(0, 0, 0, 0.6) 100%),
    url('/hero-viaduc-cize.jpg');
  background-size: cover;
  background-position: center 55%;
}
.hero-inner {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0 16px 96px;
}
.hero-title {
  font-size: clamp(1.6rem, 4vw, 2.75rem);
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.45);
  max-width: 18em;
}
.hero-sub {
  margin-top: 6px;
  font-size: clamp(0.95rem, 1.6vw, 1.15rem);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
}
.hero-credit {
  position: absolute;
  right: 8px;
  top: 6px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.85) !important;
  text-decoration: none;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
}
.hero-credit:hover {
  text-decoration: underline;
}
.search-card {
  position: relative;
  z-index: 1;
  margin-top: -76px;
}
@media (max-width: 599px) {
  .hero {
    height: 250px;
  }
  .hero-bg {
    background-image:
      linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 0%, rgba(0, 0, 0, 0.25) 45%, rgba(0, 0, 0, 0.65) 100%),
      url('/hero-viaduc-cize-960.jpg');
    background-position: 40% 55%;
  }
  .hero-inner {
    padding-bottom: 88px;
  }
  .search-card {
    margin-top: -64px;
  }
}
.search {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 8px;
}
@media (max-width: 599px) {
  .search {
    grid-template-columns: minmax(0, 1fr);
  }
  .swap {
    justify-self: center;
    transform: rotate(90deg);
    margin: -6px 0;
  }
}
.settings {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  align-items: center;
}
.intro {
  max-width: 640px;
  margin: 0 auto;
}
a {
  color: rgb(var(--v-theme-primary));
}
</style>
