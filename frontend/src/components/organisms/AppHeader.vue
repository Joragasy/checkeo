<script setup lang="ts">
import AppLogo from '../atoms/AppLogo.vue'
import ThemeToggleButton from '../atoms/ThemeToggleButton.vue'
import { useThemePreference } from '../../composables/useThemePreference'

const { isDark, toggleTheme } = useThemePreference()
</script>

<template>
  <v-app-bar flat border density="comfortable" color="surface">
    <template #prepend>
      <AppLogo class="ml-2" />
    </template>
    <v-app-bar-title class="font-weight-bold">Checkeo</v-app-bar-title>
    <span class="text-body-2 text-medium-emphasis d-none d-sm-inline mr-2"></span>
    <ThemeToggleButton :is-dark="isDark" @toggle="toggleTheme" />
  </v-app-bar>
</template>
