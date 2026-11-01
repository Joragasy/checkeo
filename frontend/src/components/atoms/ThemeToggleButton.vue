<script setup lang="ts">
defineProps<{ isDark: boolean }>()
const emit = defineEmits<{ toggle: [] }>()
</script>

<template>
  <v-btn
    :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
    :aria-label="isDark ? 'Passer en mode clair' : 'Passer en mode sombre'"
    variant="text" @click="emit('toggle')"
  />
</template>
