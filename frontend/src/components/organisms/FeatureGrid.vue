<script setup lang="ts">
import FeatureTile from '../molecules/FeatureTile.vue'

const FEATURES = [
  {
    icon: 'mdi-chart-bar',
    title: 'Trains directs sur un jour type',
    text: "Répartition heure par heure des trains sans changement, à l'aller et au retour, en semaine, le samedi ou le dimanche.",
  },
  {
    icon: 'mdi-clock-check-outline',
    title: 'Profil navetteur',
    text: "Trains arrivant avant votre heure d'embauche, départs après la débauche, plus long trou de la journée, trains en pointe et durée du trajet.",
  },
  {
    icon: 'mdi-timer-alert-outline',
    title: 'Ponctualité réelle',
    text: "Ponctualité moyenne sur 12 mois publiée par la SNCF, courbe mensuelle, taux d'annulation et causes des retards.",
  },
  {
    icon: 'mdi-map-marker-radius-outline',
    title: 'Carte des liaisons directes',
    text: 'Toutes les gares reliées sans changement depuis chez vous, colorées selon le nombre de trains par jour. Un clic pour la choisir.',
  },
  {
    icon: 'mdi-city-variant-outline',
    title: 'Une gare ou une ville entière',
    text: 'Comparez « Lille » et « Paris » toutes gares confondues, ou ciblez une gare précise. TGV, Intercités et TER.',
  },
  {
    icon: 'mdi-cellphone-link',
    title: 'Partout, en clair ou sombre',
    text: "Interface adaptée au mobile, mode sombre, et lien partageable qui retrouve exactement votre recherche.",
  },
]
</script>

<template>
  <section aria-labelledby="features-title">
    <h2 id="features-title" class="text-h6 font-weight-bold mb-4">Ce que Checkeo vous montre</h2>
    <v-row dense>
      <v-col v-for="f in FEATURES" :key="f.title" cols="12" sm="6" lg="4">
        <FeatureTile :icon="f.icon" :title="f.title">{{ f.text }}</FeatureTile>
      </v-col>
    </v-row>
  </section>
</template>
