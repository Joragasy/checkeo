<script setup lang="ts">
import { onMounted } from 'vue'
import HomePage from './components/pages/HomePage.vue'
import LandingPage from './components/pages/LandingPage.vue'
import { useAuth } from './composables/useAuth'
import { useThemePreference } from './composables/useThemePreference'

const { initTheme } = useThemePreference()
const { user, ready, initAuth } = useAuth()

initTheme()
onMounted(initAuth)
</script>

<template>
  <HomePage v-if="user" />
  <LandingPage v-else-if="ready" />
  <v-app v-else>
    <v-progress-linear indeterminate color="primary" />
  </v-app>
</template>
