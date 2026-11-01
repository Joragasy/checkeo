import { computed } from 'vue'
import { useTheme } from 'vuetify'

// ---------------------------------------------------------------- thème clair / sombre
const THEME_KEY = 'checkeo-theme'

function storedTheme(): string | null {
  try { return localStorage.getItem(THEME_KEY) } catch { return null }
}

export function useThemePreference() {
  const theme = useTheme()

  function applyTheme(name: 'light' | 'dark', persist: boolean) {
    theme.global.name.value = name
    document.documentElement.dataset.theme = name
    if (persist) try { localStorage.setItem(THEME_KEY, name) } catch { /* stockage indisponible */ }
  }
  const isDark = computed(() => theme.global.current.value.dark)
  const toggleTheme = () => applyTheme(isDark.value ? 'light' : 'dark', true)

  /** Thème enregistré, sinon préférence du système. */
  function initTheme() {
    const saved = storedTheme()
    const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
    applyTheme(saved === 'dark' || saved === 'light' ? saved : prefersDark ? 'dark' : 'light', false)
  }

  return { isDark, toggleTheme, initTheme }
}
