import { computed } from 'vue'
import { useTheme } from 'vuetify'
import { RAMP_DARK, RAMP_LIGHT } from '../constants/connectionsScale'

/** Couleurs de la carte des liaisons selon le thème clair / sombre. */
export function useConnectionTone() {
  const theme = useTheme()
  const isDark = computed(() => theme.global.current.value.dark)
  const ramp = computed(() => (isDark.value ? RAMP_DARK : RAMP_LIGHT))
  const tone = <T,>(pair: { light: T; dark: T }) => (isDark.value ? pair.dark : pair.light)
  return { isDark, ramp, tone }
}
