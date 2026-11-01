<script setup lang="ts">
import type { Direction } from '../../api'

const model = defineModel<Direction>({ required: true })
</script>

<template>
  <v-btn-toggle v-model="model" mandatory density="comfortable" variant="outlined" divided color="primary">
    <v-btn value="outbound" size="small" prepend-icon="mdi-arrow-top-right">Départs</v-btn>
    <v-btn value="inbound" size="small" prepend-icon="mdi-arrow-bottom-left">Arrivées</v-btn>
  </v-btn-toggle>
</template>
