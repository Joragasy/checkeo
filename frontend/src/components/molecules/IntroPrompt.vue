<script setup lang="ts">
const emit = defineEmits<{ example: [] }>()
</script>

<template>
  <div class="intro text-center py-6 px-2">
    <p class="text-body-1 text-medium-emphasis mb-4">
      Choisissez une gare (ou une ville entière) côté domicile et côté travail. Checkeo montre
      la répartition des trains directs sur une journée type, à l'aller et au retour, et la
      ponctualité historique publiée par la SNCF.
    </p>
    <v-btn color="primary" variant="tonal" prepend-icon="mdi-lightbulb-on-outline" @click="emit('example')">
      Exemple : Lille → Paris
    </v-btn>
  </div>
</template>

<style scoped>
.intro {
  max-width: 640px;
  margin: 0 auto;
}
</style>
