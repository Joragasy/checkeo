import type { DayType } from '../api'

export const DAY_TYPES: { value: DayType; title: string; short: string }[] = [
  { value: 'weekday', title: 'Jour de semaine', short: 'Semaine' },
  { value: 'saturday', title: 'Samedi', short: 'Samedi' },
  { value: 'sunday', title: 'Dimanche', short: 'Dimanche' },
]
