/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Clé des fonds de carte CARTO (frontend/.env.local, hors git). */
  readonly VITE_CARTO_KEY?: string
  /** Identifiant client OAuth Google (frontend/.env.local, hors git). */
  readonly VITE_GOOGLE_CLIENT_ID?: string
}

// Google Identity Services (https://accounts.google.com/gsi/client), réduit à ce qu'utilise Checkeo.
interface GoogleIdConfiguration {
  client_id: string
  callback: (response: { credential: string }) => void
  auto_select?: boolean
  cancel_on_tap_outside?: boolean
  use_fedcm_for_prompt?: boolean
}

interface GoogleButtonOptions {
  type?: 'standard' | 'icon'
  theme?: 'outline' | 'filled_blue' | 'filled_black'
  size?: 'large' | 'medium' | 'small'
  text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
  shape?: 'rectangular' | 'pill' | 'circle' | 'square'
  logo_alignment?: 'left' | 'center'
  width?: number
  locale?: string
}

interface Window {
  google?: {
    accounts: {
      id: {
        initialize(config: GoogleIdConfiguration): void
        renderButton(parent: HTMLElement, options: GoogleButtonOptions): void
        disableAutoSelect(): void
      }
    }
  }
}
