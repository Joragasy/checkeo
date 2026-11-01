<script setup lang="ts">
import FeatureGrid from '../organisms/FeatureGrid.vue'
import HeroBanner from '../organisms/HeroBanner.vue'
import DefaultLayout from '../templates/DefaultLayout.vue'
import { useAuthView } from '../../composables/useAuthView'

const { openAuth } = useAuthView()
</script>

<template>
  <DefaultLayout>
    <HeroBanner :overlap="false" />

    <v-container class="page py-6 py-md-8">
      <FeatureGrid />

      <v-card class="cta pa-6 pa-md-8 mt-8 text-center">
        <h2 class="text-h6 font-weight-bold mb-2">Prêt à évaluer votre trajet ?</h2>
        <p class="text-body-2 text-medium-emphasis mb-5">
          Créez votre compte gratuit avec votre adresse e-mail ou avec Google,
          ou connectez-vous si vous en avez déjà un.
        </p>
        <div class="d-flex flex-wrap justify-center ga-3">
          <v-btn color="primary" variant="flat" size="large" @click="openAuth('signup')">Créer un compte</v-btn>
          <v-btn color="primary" variant="outlined" size="large" @click="openAuth('signin')">Se connecter</v-btn>
        </div>
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
