<script setup lang="ts">
import { computed } from 'vue'
import type { Profile } from '../../api'
import { dateLabel } from '../../format'

const props = defineProps<{ profile: Profile }>()
const sampleDates = computed(() => props.profile.meta.sample_dates ?? [])
</script>

<template>
  <div class="text-body-2 text-medium-emphasis mb-4">
    <v-icon icon="mdi-calendar-range" size="small" />
    {{ profile.day_type_label }} : trains présents sur au moins
    {{ Math.round(profile.meta.presence_threshold * 100) }} % des {{ sampleDates.length }} dates étudiées
    (du {{ dateLabel(sampleDates[0]) }} au {{ dateLabel(sampleDates[sampleDates.length - 1]) }}, jours fériés exclus).
    Horaires valables du {{ dateLabel(profile.meta.feed_start) }} au {{ dateLabel(profile.meta.feed_end) }}.
  </div>
</template>
