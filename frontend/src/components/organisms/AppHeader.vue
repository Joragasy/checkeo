<script setup lang="ts">
import AppLogo from '../atoms/AppLogo.vue'
import GoogleSignInButton from '../atoms/GoogleSignInButton.vue'
import ThemeToggleButton from '../atoms/ThemeToggleButton.vue'
import UserMenu from '../molecules/UserMenu.vue'
import { useAuth } from '../../composables/useAuth'
import { useThemePreference } from '../../composables/useThemePreference'

const { isDark, toggleTheme } = useThemePreference()
const { user, ready, logout } = useAuth()
</script>

<template>
  <v-app-bar flat border density="comfortable" color="surface">
    <template #prepend>
      <AppLogo class="ml-2" />
    </template>
    <v-app-bar-title class="font-weight-bold">Checkeo</v-app-bar-title>
    <ThemeToggleButton :is-dark="isDark" @toggle="toggleTheme" />
    <UserMenu v-if="user" :user="user" class="mr-2" @logout="logout" />
    <GoogleSignInButton v-else-if="ready" size="medium" class="mr-3 d-none d-sm-inline-flex" />
  </v-app-bar>
</template>
