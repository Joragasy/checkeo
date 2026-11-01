<script setup lang="ts">
defineProps<{ title: string; fromName: string; toName: string; count: number; variability: string | null }>()
</script>

<template>
  <div>
    <div class="text-overline text-medium-emphasis">{{ title }}</div>
    <h2 class="text-h6 font-weight-medium">{{ fromName }} <v-icon icon="mdi-arrow-right" size="small" /> {{ toName }}</h2>
    <div class="text-body-2 text-medium-emphasis">
      <strong class="text-high-emphasis">{{ count }}</strong>
      train{{ count > 1 ? 's' : '' }} direct{{ count > 1 ? 's' : '' }} sur un jour type
      <template v-if="variability"> ({{ variability }})</template>
    </div>
  </div>
</template>
