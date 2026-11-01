<script setup lang="ts">
import AppLogo from '../atoms/AppLogo.vue'
import ThemeToggleButton from '../atoms/ThemeToggleButton.vue'
import UserMenu from '../molecules/UserMenu.vue'
import { useAuth } from '../../composables/useAuth'
import { useAuthView } from '../../composables/useAuthView'
import { useThemePreference } from '../../composables/useThemePreference'

const { isDark, toggleTheme } = useThemePreference()
const { user, ready, logout } = useAuth()
const { openAuth } = useAuthView()
</script>

<template>
  <v-app-bar flat border density="comfortable" color="surface">
    <template #prepend>
      <AppLogo class="ml-2" />
    </template>
    <v-app-bar-title class="font-weight-bold">Checkeo</v-app-bar-title>
    <ThemeToggleButton :is-dark="isDark" @toggle="toggleTheme" />
    <UserMenu v-if="user" :user="user" class="mr-2" @logout="logout" />
    <v-btn
      v-else-if="ready"
      icon="mdi-account-circle-outline"
      variant="text"
      class="mr-2"
      aria-label="Se connecter ou créer un compte"
      v-tooltip:bottom="'Se connecter / Créer un compte'"
      @click="openAuth('signin')"
    />
  </v-app-bar>
</template>
