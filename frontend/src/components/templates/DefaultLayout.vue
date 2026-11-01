<script setup lang="ts">
import AppFooter from '../organisms/AppFooter.vue'
import AppHeader from '../organisms/AppHeader.vue'
</script>

<template>
  <v-app>
    <AppHeader />

    <v-main>
      <slot />
    </v-main>

    <AppFooter />
  </v-app>
</template>
