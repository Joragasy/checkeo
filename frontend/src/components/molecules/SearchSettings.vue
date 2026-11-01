<script setup lang="ts">
const arriveBy = defineModel<string>('arriveBy', { required: true })
const leaveAfter = defineModel<string>('leaveAfter', { required: true })
const bin = defineModel<number>('bin', { required: true })
const includeBuses = defineModel<boolean>('includeBuses', { required: true })
const emit = defineEmits<{ commit: [] }>()
</script>

<template>
  <div class="settings">
    <v-text-field
      v-model="arriveBy" type="time" label="Arriver au travail avant" density="compact"
      variant="outlined" hide-details @change="emit('commit')"
    />
    <v-text-field
      v-model="leaveAfter" type="time" label="Repartir après" density="compact"
      variant="outlined" hide-details @change="emit('commit')"
    />
    <v-select
      v-model="bin" :items="[{ title: '30 min', value: 30 }, { title: '1 heure', value: 60 }]"
      label="Pas de l'histogramme" density="compact" variant="outlined" hide-details
    />
    <v-switch
      v-model="includeBuses" label="Inclure les cars TER" color="primary" density="compact"
      hide-details inset
    />
  </div>
</template>

<style scoped>
.settings {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  align-items: center;
}
</style>
