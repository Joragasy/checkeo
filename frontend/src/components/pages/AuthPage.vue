<script setup lang="ts">
import { computed, onMounted } from 'vue'
import GoogleSignInButton from '../atoms/GoogleSignInButton.vue'
import AuthForm from '../molecules/AuthForm.vue'
import DefaultLayout from '../templates/DefaultLayout.vue'
import { useAuth } from '../../composables/useAuth'
import { useAuthView, type AuthMode } from '../../composables/useAuthView'

const { error, pending, loginWithPassword, registerWithPassword } = useAuth()
const { authMode, openAuth } = useAuthView()

const mode = computed<AuthMode>({
  get: () => authMode.value ?? 'signin',
  set: (m) => {
    error.value = null
    openAuth(m)
  },
})
const isSignup = computed(() => mode.value === 'signup')

onMounted(() => { error.value = null })

function onSubmit({ email, password, name }: { email: string; password: string; name: string }) {
  return isSignup.value ? registerWithPassword(email, password, name) : loginWithPassword(email, password)
}
</script>

<template>
  <DefaultLayout>
    <v-container class="py-8 py-md-12">
      <v-card class="auth-card mx-auto">
        <v-tabs v-model="mode" grow color="primary">
          <v-tab value="signin">Se connecter</v-tab>
          <v-tab value="signup">Créer un compte</v-tab>
        </v-tabs>
        <v-divider />

        <div class="pa-6 pa-sm-8">
          <h1 class="text-h6 font-weight-bold mb-1">
            {{ isSignup ? 'Créer votre compte Checkeo' : 'Bon retour sur Checkeo' }}
          </h1>
          <p class="text-body-2 text-medium-emphasis mb-6">
            {{ isSignup
              ? 'Gratuit. Inscrivez-vous avec votre adresse e-mail ou avec Google.'
              : 'Connectez-vous avec votre adresse e-mail ou avec Google.' }}
          </p>

          <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-4">{{ error }}</v-alert>

          <AuthForm :mode="mode" :loading="pending" @submit="onSubmit" />

          <div class="d-flex align-center my-6">
            <v-divider />
            <span class="px-3 text-caption text-medium-emphasis">ou</span>
            <v-divider />
          </div>

          <div class="d-flex justify-center">
            <GoogleSignInButton :text="isSignup ? 'signup_with' : 'signin_with'" shape="rectangular" :width="300" />
          </div>

          <p class="text-body-2 text-center mt-6 mb-0">
            <template v-if="isSignup">
              Déjà un compte ?
              <a href="#/connexion" class="font-weight-medium">Se connecter</a>
            </template>
            <template v-else>
              Pas encore de compte ?
              <a href="#/inscription" class="font-weight-medium">Créer un compte</a>
            </template>
          </p>
        </div>
      </v-card>
    </v-container>
  </DefaultLayout>
</template>

<style scoped>
.auth-card {
  max-width: 460px;
}
a {
  color: rgb(var(--v-theme-primary));
}
</style>
