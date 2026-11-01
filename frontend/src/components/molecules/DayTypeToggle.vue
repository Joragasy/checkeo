<script setup lang="ts">
import type { DayType } from '../../api'
import { DAY_TYPES } from '../../constants/dayTypes'

const model = defineModel<DayType>({ required: true })
</script>

<template>
  <v-btn-toggle v-model="model" mandatory density="comfortable" variant="outlined" divided color="primary">
    <v-btn v-for="d in DAY_TYPES" :key="d.value" :value="d.value" size="small">
      <span class="d-none d-sm-inline">{{ d.title }}</span><span class="d-sm-none">{{ d.short }}</span>
    </v-btn>
  </v-btn-toggle>
</template>
