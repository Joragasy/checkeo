<script setup lang="ts">
import GoogleSignInButton from '../atoms/GoogleSignInButton.vue'
import FeatureGrid from '../organisms/FeatureGrid.vue'
import HeroBanner from '../organisms/HeroBanner.vue'
import DefaultLayout from '../templates/DefaultLayout.vue'
import { useAuth } from '../../composables/useAuth'

const { error } = useAuth()
</script>

<template>
  <DefaultLayout>
    <HeroBanner :overlap="false">
      <div class="mt-4">
        <GoogleSignInButton />
      </div>
    </HeroBanner>

    <v-container class="page py-6 py-md-8">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-6">{{ error }}</v-alert>

      <FeatureGrid />

      <v-card class="cta pa-6 pa-md-8 mt-8 text-center">
        <h2 class="text-h6 font-weight-bold mb-2">Prêt à évaluer votre trajet ?</h2>
        <p class="text-body-2 text-medium-emphasis mb-5">
          Créez votre compte en un clic avec Google, ou connectez-vous si vous en avez déjà un.
          Gratuit, sans mot de passe à retenir.
        </p>
        <GoogleSignInButton />
      </v-card>
    </v-container>
  </DefaultLayout>
</template>

<style scoped>
.page {
  max-width: 1280px;
}
.cta {
  max-width: 720px;
  margin-left: auto;
  margin-right: auto;
}
</style>
