<script setup lang="ts">
import { ref } from 'vue'
import type { DayType, StationHit } from '../../api'
import SwapButton from '../atoms/SwapButton.vue'
import DayTypeToggle from '../molecules/DayTypeToggle.vue'
import SearchSettings from '../molecules/SearchSettings.vue'
import StationAutocomplete from '../molecules/StationAutocomplete.vue'

const home = defineModel<StationHit | null>('home', { required: true })
const work = defineModel<StationHit | null>('work', { required: true })
const dayType = defineModel<DayType>('dayType', { required: true })
const arriveBy = defineModel<string>('arriveBy', { required: true })
const leaveAfter = defineModel<string>('leaveAfter', { required: true })
const bin = defineModel<number>('bin', { required: true })
const includeBuses = defineModel<boolean>('includeBuses', { required: true })
const emit = defineEmits<{ commit: [] }>()

const showSettings = ref(false)

function swap() {
  ;[home.value, work.value] = [work.value, home.value]
}
</script>

<template>
  <v-card class="search-card pa-3 pa-md-4 mb-4" elevation="4" :border="false">
    <div class="search">
      <StationAutocomplete v-model="home" label="Domicile (gare de départ)" icon="mdi-home-outline" />
      <SwapButton aria-label="Inverser domicile et travail" :disabled="!home && !work" @click="swap" />
      <StationAutocomplete v-model="work" label="Travail (gare d'arrivée)" icon="mdi-briefcase-outline" />
    </div>
    <div class="d-flex flex-wrap align-center ga-2 mt-3">
      <DayTypeToggle v-model="dayType" />
      <v-spacer />
      <v-btn variant="text" size="small" prepend-icon="mdi-tune-variant" @click="showSettings = !showSettings">
        Réglages
      </v-btn>
    </div>
    <v-expand-transition>
      <SearchSettings
        v-if="showSettings" v-model:arrive-by="arriveBy" v-model:leave-after="leaveAfter" v-model:bin="bin"
        v-model:include-buses="includeBuses" class="mt-3" @commit="emit('commit')"
      />
    </v-expand-transition>
  </v-card>
</template>

<style scoped>
.search-card {
  position: relative;
  z-index: 1;
  margin-top: -76px;
}
@media (max-width: 599px) {
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
}
</style>
