import { ref } from 'vue'

// ---------------------------------------------------------------- page de connexion (ancre d'URL)
// #/connexion et #/inscription : le bouton « précédent » du navigateur ramène à l'accueil.
export type AuthMode = 'signin' | 'signup'

const HASHES: Record<AuthMode, string> = { signin: '#/connexion', signup: '#/inscription' }

function modeFromHash(): AuthMode | null {
  const entry = Object.entries(HASHES).find(([, h]) => h === window.location.hash)
  return entry ? (entry[0] as AuthMode) : null
}

const authMode = ref<AuthMode | null>(modeFromHash())
window.addEventListener('hashchange', () => { authMode.value = modeFromHash() })

export function useAuthView() {
  /** Affiche la page de connexion (ou d'inscription). */
  function openAuth(mode: AuthMode) {
    if (window.location.hash !== HASHES[mode]) window.location.hash = HASHES[mode]
    authMode.value = mode
    window.scrollTo(0, 0)
  }

  /** Quitte la page de connexion en effaçant l'ancre, sans ajouter d'entrée à l'historique. */
  function closeAuth() {
    if (window.location.hash) history.replaceState(null, '', window.location.pathname + window.location.search)
    authMode.value = null
  }

  return { authMode, openAuth, closeAuth }
}
