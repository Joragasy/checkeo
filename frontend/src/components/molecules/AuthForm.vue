<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AuthMode } from '../../composables/useAuthView'

const props = defineProps<{ mode: AuthMode; loading?: boolean }>()
const emit = defineEmits<{ submit: [payload: { email: string; password: string; name: string }] }>()

const form = ref<{ validate: () => Promise<{ valid: boolean }>; resetValidation: () => void } | null>(null)
const name = ref('')
const email = ref('')
const password = ref('')
const confirm = ref('')
const showPassword = ref(false)

const isSignup = computed(() => props.mode === 'signup')

const rules = {
  required: (v: string) => !!v?.trim() || 'Champ obligatoire',
  email: (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) || 'Adresse e-mail invalide',
  length: (v: string) => (v.length >= 8 && v.length <= 128) || 'Entre 8 et 128 caractères',
  match: (v: string) => v === password.value || 'Les mots de passe ne correspondent pas',
}

watch(() => props.mode, () => {
  confirm.value = ''
  form.value?.resetValidation()
})

async function onSubmit() {
  const result = await form.value?.validate()
  if (!result?.valid) return
  emit('submit', { email: email.value.trim(), password: password.value, name: name.value.trim() })
}
</script>

<template>
  <v-form ref="form" validate-on="submit lazy" @submit.prevent="onSubmit">
    <v-text-field
      v-if="isSignup"
      v-model="name"
      label="Nom (facultatif)"
      autocomplete="name"
      prepend-inner-icon="mdi-account-outline"
      variant="outlined"
      density="comfortable"
      maxlength="120"
      class="mb-1"
    />
    <v-text-field
      v-model="email"
      label="Adresse e-mail"
      type="email"
      autocomplete="email"
      prepend-inner-icon="mdi-email-outline"
      variant="outlined"
      density="comfortable"
      :rules="[rules.required, rules.email]"
      class="mb-1"
    />
    <v-text-field
      v-model="password"
      label="Mot de passe"
      :type="showPassword ? 'text' : 'password'"
      :autocomplete="isSignup ? 'new-password' : 'current-password'"
      prepend-inner-icon="mdi-lock-outline"
      :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
      variant="outlined"
      density="comfortable"
      :rules="isSignup ? [rules.required, rules.length] : [rules.required]"
      :hint="isSignup ? '8 caractères minimum' : undefined"
      class="mb-1"
      @click:append-inner="showPassword = !showPassword"
    />
    <v-text-field
      v-if="isSignup"
      v-model="confirm"
      label="Confirmer le mot de passe"
      :type="showPassword ? 'text' : 'password'"
      autocomplete="new-password"
      prepend-inner-icon="mdi-lock-check-outline"
      variant="outlined"
      density="comfortable"
      :rules="[rules.required, rules.match]"
      class="mb-1"
    />
    <v-btn type="submit" color="primary" variant="flat" size="large" block :loading="loading">
      {{ isSignup ? 'Créer mon compte' : 'Se connecter' }}
    </v-btn>
  </v-form>
</template>
