<script setup lang="ts">
defineProps<{ icon: string; title: string }>()
</script>

<template>
  <v-card class="pa-4 pa-md-5 tile h-100">
    <v-avatar color="primary" variant="tonal" size="44" rounded="lg" class="mb-3">
      <v-icon :icon="icon" size="24" />
    </v-avatar>
    <h3 class="text-subtitle-1 font-weight-bold mb-1">{{ title }}</h3>
    <p class="text-body-2 text-medium-emphasis mb-0"><slot /></p>
  </v-card>
</template>

<style scoped>
.tile {
  min-width: 0;
}
</style>
