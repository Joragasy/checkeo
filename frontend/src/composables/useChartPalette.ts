import { useTheme } from 'vuetify'

/** Couleurs communes aux graphiques ECharts ; à appeler dans un `computed` pour suivre le thème. */
export function useChartPalette() {
  const theme = useTheme()
  return () => {
    const c = theme.current.value.colors
    const dark = theme.current.value.dark
    return {
      c,
      dark,
      muted: dark ? '#a3a299' : '#6b6a66',
      grid: dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.07)',
      text: dark ? '#f0efec' : '#0b0b0b',
    }
  }
}
