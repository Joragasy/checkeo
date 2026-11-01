<script setup lang="ts">
import { computed } from 'vue'
import { useDisplay } from 'vuetify'
import type { Direction, Profile } from '../../api'
import DirectionPanel from './DirectionPanel.vue'

const props = defineProps<{ profile: Profile }>()
const tab = defineModel<Direction>('tab', { required: true })

const { mdAndUp } = useDisplay()

const fromName = computed(() => props.profile.from.name ?? '')
const toName = computed(() => props.profile.to.name ?? '')
const multiStation = computed(() => props.profile.from.kind === 'city' || props.profile.to.kind === 'city')

const panels = computed(() => [
  { key: 'outbound' as const, title: 'Aller', fromName: fromName.value, toName: toName.value, data: props.profile.outbound, isOutbound: true },
  { key: 'inbound' as const, title: 'Retour', fromName: toName.value, toName: fromName.value, data: props.profile.inbound, isOutbound: false },
])
</script>

<template>
  <v-row v-if="mdAndUp">
    <v-col v-for="p in panels" :key="p.key" cols="6">
      <DirectionPanel
        :title="p.title" :from-name="p.fromName" :to-name="p.toName" :data="p.data" :is-outbound="p.isOutbound"
        :multi-station="multiStation"
      />
    </v-col>
  </v-row>
  <template v-else>
    <v-tabs v-model="tab" grow color="primary" class="mb-3">
      <v-tab value="outbound">Aller · {{ profile.outbound.count }}</v-tab>
      <v-tab value="inbound">Retour · {{ profile.inbound.count }}</v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item v-for="p in panels" :key="p.key" :value="p.key">
        <DirectionPanel
          :title="p.title" :from-name="p.fromName" :to-name="p.toName" :data="p.data" :is-outbound="p.isOutbound"
          :multi-station="multiStation"
        />
      </v-window-item>
    </v-window>
  </template>
</template>
