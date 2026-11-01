<script setup lang="ts">
import { computed } from 'vue'
import type { AuthUser } from '../../api'

const props = defineProps<{ user: AuthUser }>()
const emit = defineEmits<{ logout: [] }>()

const initial = computed(() => (props.user.name || props.user.email).charAt(0).toUpperCase())
</script>

<template>
  <v-menu location="bottom end">
    <template #activator="{ props: activator }">
      <v-btn v-bind="activator" icon variant="text" :aria-label="`Compte de ${user.name || user.email}`">
        <v-avatar size="32" color="primary">
          <v-img v-if="user.picture" :src="user.picture" :alt="''" referrerpolicy="no-referrer" />
          <span v-else class="text-body-1 font-weight-bold">{{ initial }}</span>
        </v-avatar>
      </v-btn>
    </template>
    <v-list density="comfortable" min-width="240">
      <v-list-item :title="user.name || user.email" :subtitle="user.name ? user.email : undefined" />
      <v-divider />
      <v-list-item prepend-icon="mdi-logout" title="Se déconnecter" @click="emit('logout')" />
    </v-list>
  </v-menu>
</template>
