<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { useAuth } from '../../composables/useAuth'
import { useThemePreference } from '../../composables/useThemePreference'

const props = withDefaults(defineProps<{
  size?: 'large' | 'medium' | 'small'
  shape?: 'rectangular' | 'pill'
}>(), { size: 'large', shape: 'pill' })

const { googleId } = useAuth()
const { isDark } = useThemePreference()
const el = ref<HTMLElement | null>(null)
const unavailable = ref<string | null>(null)

// Le bouton est rendu par Google dans une iframe : on le redessine au changement de thème.
async function render() {
  try {
    const id = await googleId()
    await nextTick()
    if (!el.value) return
    el.value.innerHTML = ''
    id.renderButton(el.value, {
      type: 'standard',
      text: 'continue_with',
      theme: isDark.value ? 'filled_black' : 'outline',
      size: props.size,
      shape: props.shape,
      logo_alignment: 'left',
      locale: 'fr',
    })
  } catch (e) {
    unavailable.value = (e as Error).message
  }
}

onMounted(render)
watch(isDark, render)
</script>

<template>
  <div class="gsi">
    <div ref="el" />
    <span v-if="unavailable" class="text-caption text-medium-emphasis">{{ unavailable }}</span>
  </div>
</template>

<style scoped>
.gsi {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  min-height: 32px;
  color-scheme: light; /* évite un fond blanc opaque autour de l'iframe Google en mode sombre */
}
</style>
