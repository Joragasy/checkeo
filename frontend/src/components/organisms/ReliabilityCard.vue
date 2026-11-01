<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ReliabilityBlock } from '../../api'
import { dateLabel, monthLabel, pct } from '../../format'
import CauseBar from '../molecules/CauseBar.vue'
import PunctualityLineChart from '../molecules/PunctualityLineChart.vue'

const props = defineProps<{ block: ReliabilityBlock }>()
const showTable = ref(false)

const points = computed(() => (props.block.monthly ?? []).filter((m) => m.rate != null))

const scopeLabel = computed(() => (props.block.scope === 'region' ? 'Moyenne régionale' : 'Liaison'))
</script>

<template>
  <v-card class="pa-4">
    <div class="d-flex align-center flex-wrap ga-2 mb-2">
      <v-icon icon="mdi-clock-check-outline" size="small" />
      <span class="text-subtitle-1 font-weight-medium">Fiabilité {{ block.family_label }}</span>
      <v-chip size="x-small" variant="tonal" :color="block.scope === 'region' ? 'warning' : 'primary'">
        {{ scopeLabel }}
      </v-chip>
      <span v-if="block.label" class="text-body-2 text-medium-emphasis">{{ block.label }}</span>
    </div>

    <v-alert v-if="!block.available" type="info" variant="tonal" density="compact" icon="mdi-database-off-outline">
      <div class="font-weight-medium">Donnée indisponible</div>
      <div class="text-body-2">{{ block.note }}</div>
    </v-alert>

    <template v-else>
      <v-alert
        v-if="block.stale" type="warning" variant="tonal" density="compact" class="mb-3"
        icon="mdi-calendar-alert"
      >
        Données anciennes : dernier mois publié {{ monthLabel(block.last_month) }}
        ({{ block.lag_months }} mois de décalage).
      </v-alert>

      <div class="d-flex flex-wrap ga-6 mb-1">
        <div>
          <div class="text-h4 font-weight-bold">{{ pct(block.punctuality) }}</div>
          <div class="text-caption text-medium-emphasis">
            trains à l'heure · {{ monthLabel(block.window?.from) }} – {{ monthLabel(block.window?.to) }}
          </div>
        </div>
        <div v-if="block.cancel_rate != null">
          <div class="text-h5 font-weight-medium mt-1">{{ pct(block.cancel_rate, 2) }}</div>
          <div class="text-caption text-medium-emphasis">trains annulés</div>
        </div>
      </div>
      <p class="text-body-2 text-medium-emphasis mb-2">{{ block.note }}</p>

      <div class="text-caption text-medium-emphasis mt-2">Ponctualité mensuelle (36 derniers mois publiés)</div>
      <PunctualityLineChart
        v-if="points.length > 1" :points="points"
        :description="`Évolution mensuelle de la ponctualité ${block.family_label}`"
      />

      <div v-if="block.causes?.length" class="mt-3">
        <div class="text-caption text-medium-emphasis mb-1">Causes des retards (12 mois, pondérées par le nombre de trains en retard)</div>
        <CauseBar v-for="c in block.causes" :key="c.key" :cause="c" />
      </div>

      <v-btn
        variant="text" size="small" class="mt-2 px-1" :prepend-icon="showTable ? 'mdi-chevron-up' : 'mdi-table'"
        @click="showTable = !showTable"
      >
        {{ showTable ? 'Masquer les données' : 'Voir les données' }}
      </v-btn>
      <v-table v-if="showTable" density="compact" class="mt-1 data-table">
        <thead>
          <tr><th>Mois</th><th class="text-right">Ponctualité</th><th class="text-right">Annulations</th><th class="text-right">Trains prévus</th></tr>
        </thead>
        <tbody>
          <tr v-for="m in [...(block.monthly ?? [])].reverse()" :key="m.month">
            <td>{{ monthLabel(m.month) }}</td>
            <td class="text-right">{{ pct(m.rate) }}</td>
            <td class="text-right">{{ pct(m.cancel_rate, 2) }}</td>
            <td class="text-right">{{ m.planned?.toLocaleString('fr-FR') ?? '—' }}</td>
          </tr>
        </tbody>
      </v-table>
    </template>

    <div class="text-caption text-medium-emphasis mt-3">
      <template v-if="block.last_month">Données jusqu'à {{ monthLabel(block.last_month) }} · </template>
      jeu de régularité mis à jour le {{ dateLabel(block.dataset_modified) }}
    </div>
  </v-card>
</template>

<style scoped>
.data-table {
  max-height: 260px;
  overflow-y: auto;
}
</style>
