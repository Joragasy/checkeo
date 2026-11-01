<script setup lang="ts">
defineProps<{ label: string; caption: string }>()
</script>

<template>
  <v-card class="pa-3 tile">
    <div class="text-caption text-medium-emphasis">{{ label }}</div>
    <div class="text-h5 font-weight-bold"><slot /></div>
    <div class="text-caption text-medium-emphasis">{{ caption }}</div>
  </v-card>
</template>

<style scoped>
.tile {
  min-width: 0;
}
</style>
