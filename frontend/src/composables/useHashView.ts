import { ref } from 'vue'

// ---------------------------------------------------------------- vues secondaires (ancre d'URL)
// #/connexion, #/mentions-legales… : le bouton « précédent » du navigateur ramène à la vue principale.
export type View = 'signin' | 'signup' | 'legal' | 'privacy'

const HASHES: Record<View, string> = {
  signin: '#/connexion',
  signup: '#/inscription',
  legal: '#/mentions-legales',
  privacy: '#/confidentialite',
}

function viewFromHash(): View | null {
  const entry = Object.entries(HASHES).find(([, h]) => h === window.location.hash)
  return entry ? (entry[0] as View) : null
}

const view = ref<View | null>(viewFromHash())
window.addEventListener('hashchange', () => { view.value = viewFromHash() })

export function useHashView() {
  /** Affiche une vue secondaire (ajoute une entrée à l'historique). */
  function openView(v: View) {
    if (window.location.hash !== HASHES[v]) window.location.hash = HASHES[v]
    view.value = v
    window.scrollTo(0, 0)
  }

  /** Revient à la vue principale en effaçant l'ancre, sans ajouter d'entrée à l'historique. */
  function closeView() {
    if (window.location.hash) history.replaceState(null, '', window.location.pathname + window.location.search)
    view.value = null
    window.scrollTo(0, 0)
  }

  return { view, openView, closeView, hrefOf: (v: View) => HASHES[v] }
}
