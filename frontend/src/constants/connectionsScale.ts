// ---------------------------------------------------------------- échelle : trains directs par jour
// Rampe ordinale bleue de la palette data-viz (validée sur les surfaces claire et sombre) ;
// en mode sombre, les liaisons les plus fréquentes sont les plus lumineuses.
export const BUCKETS = [
  { min: 1, label: '1–2' },
  { min: 3, label: '3–5' },
  { min: 6, label: '6–11' },
  { min: 12, label: '12–23' },
  { min: 24, label: '24 +' },
]
export const RAMP_LIGHT = ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281']
export const RAMP_DARK = ['#184f95', '#256abf', '#3987e5', '#6da7ec', '#9ec5f4']
export const bucketOf = (trains: number) => BUCKETS.reduce((i, b, j) => (trains >= b.min ? j : i), 0)
export const radiusOf = (trains: number) => (trains > 0 ? Math.min(4 + 2.2 * Math.sqrt(trains), 18) : 3.5)

export const OCCASIONAL = { light: '#8a8984', dark: '#7a7973' }
export const INK = { light: '#1f1f1d', dark: '#f0efea' }
export const SURFACE = { light: '#fcfcfb', dark: '#1a1a19' }
