import { computed } from 'vue'
import { useHashView } from './useHashView'

// ---------------------------------------------------------------- page de connexion (#/connexion, #/inscription)
export type AuthMode = 'signin' | 'signup'

export function useAuthView() {
  const { view, openView, closeView } = useHashView()

  const authMode = computed<AuthMode | null>(() =>
    view.value === 'signin' || view.value === 'signup' ? view.value : null)

  return {
    authMode,
    openAuth: (mode: AuthMode) => openView(mode),
    closeAuth: closeView,
  }
}
