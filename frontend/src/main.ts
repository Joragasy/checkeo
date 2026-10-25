import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import { fr } from 'vuetify/locale'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import App from './App.vue'

// Couleurs : palette de référence data-viz (bleu série 1), avec des valeurs propres au mode sombre.
const vuetify = createVuetify({
  locale: { locale: 'fr', messages: { fr } },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          background: '#f5f5f3',
          surface: '#fcfcfb',
          primary: '#256abf',
          secondary: '#52514e',
          series: '#2a78d6',
          'series-soft': '#b7d3f6',
          good: '#0ca30c',
          warning: '#b97f00',
          critical: '#d03b3b',
        },
      },
      dark: {
        dark: true,
        colors: {
          background: '#121211',
          surface: '#1a1a19',
          primary: '#5598e7',
          secondary: '#c3c2b7',
          series: '#3987e5',
          'series-soft': '#184f95',
          good: '#0ca30c',
          warning: '#fab219',
          critical: '#e66767',
        },
      },
    },
  },
  defaults: {
    VCard: { rounded: 'lg', elevation: 0, border: true },
    VBtn: { rounded: 'lg' },
  },
})

createApp(App).use(vuetify).mount('#app')
