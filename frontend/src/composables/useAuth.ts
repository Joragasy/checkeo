import { computed, ref } from 'vue'
import { fetchMe, onUnauthorized, signInWithGoogle, signOut, type AuthUser } from '../api'

// ---------------------------------------------------------------- état partagé de la session
const user = ref<AuthUser | null>(null)
const ready = ref(false)
const error = ref<string | null>(null)
let googleInitialized = false

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

async function handleCredential(credential: string) {
  error.value = null
  try {
    user.value = await signInWithGoogle(credential)
  } catch (e) {
    error.value = (e as Error).message
  }
}

/** Attend le script Google Identity Services (chargé en async dans index.html). */
function waitForGoogle(timeoutMs = 10000): Promise<NonNullable<Window['google']>> {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const tick = () => {
      if (window.google?.accounts?.id) return resolve(window.google)
      if (Date.now() - start > timeoutMs) return reject(new Error('Connexion Google indisponible.'))
      setTimeout(tick, 100)
    }
    tick()
  })
}

/** Initialise Google Identity Services une seule fois et renvoie son API. */
async function googleId() {
  if (!CLIENT_ID) throw new Error('Connexion Google non configurée (VITE_GOOGLE_CLIENT_ID).')
  const google = await waitForGoogle()
  if (!googleInitialized) {
    google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: ({ credential }) => handleCredential(credential),
      cancel_on_tap_outside: true,
      use_fedcm_for_prompt: true,
    })
    googleInitialized = true
  }
  return google.accounts.id
}

export function useAuth() {
  /** Récupère la session existante (cookie) au démarrage. */
  async function initAuth() {
    onUnauthorized(() => { user.value = null })
    try {
      user.value = await fetchMe()
    } catch {
      user.value = null
    } finally {
      ready.value = true
    }
  }

  async function logout() {
    try { await signOut() } catch { /* la session locale est oubliée de toute façon */ }
    window.google?.accounts.id.disableAutoSelect()
    user.value = null
  }

  return {
    user,
    ready,
    error,
    isSignedIn: computed(() => user.value !== null),
    initAuth,
    logout,
    googleId,
  }
}
