<script setup lang="ts">
import { onMounted, watch } from 'vue'
import AuthPage from './components/pages/AuthPage.vue'
import HomePage from './components/pages/HomePage.vue'
import LandingPage from './components/pages/LandingPage.vue'
import { useAuth } from './composables/useAuth'
import { useAuthView } from './composables/useAuthView'
import { useThemePreference } from './composables/useThemePreference'

const { initTheme } = useThemePreference()
const { user, ready, initAuth } = useAuth()
const { authMode, closeAuth } = useAuthView()

// Une fois connecté, la page de connexion n'a plus lieu d'être : on retire l'ancre.
watch(user, (u) => { if (u && authMode.value) closeAuth() })

initTheme()
onMounted(initAuth)
</script>

<template>
  <HomePage v-if="user" />
  <AuthPage v-else-if="ready && authMode" />
  <LandingPage v-else-if="ready" />
  <v-app v-else>
    <v-progress-linear indeterminate color="primary" />
  </v-app>
</template>
