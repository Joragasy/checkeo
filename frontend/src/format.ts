export const hhmm = (s: number): string => {
  const t = ((s % 86400) + 86400) % 86400
  return `${String(Math.floor(t / 3600)).padStart(2, '0')}:${String(Math.floor((t % 3600) / 60)).padStart(2, '0')}`
}

/** "09:00" → "9h", "09:30" → "9h30" */
export const hLabel = (s: number): string => {
  const t = s % 86400
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  return m ? `${h}h${String(m).padStart(2, '0')}` : `${h}h`
}

export const duration = (min: number | null | undefined): string => {
  if (min == null) return '—'
  const h = Math.floor(min / 60)
  const m = min % 60
  return h ? `${h} h ${String(m).padStart(2, '0')}` : `${m} min`
}

const MONTHS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']

/** "2026-09" → "sept. 2026" */
export const monthLabel = (ym: string | undefined | null): string => {
  if (!ym) return '—'
  const [y, m] = ym.split('-')
  return `${MONTHS[Number(m) - 1]} ${y}`
}

export const dateLabel = (iso: string | undefined | null): string => {
  if (!iso) return '—'
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso)
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

export const pct = (v: number | null | undefined, digits = 1): string =>
  v == null ? '—' : `${v.toLocaleString('fr-FR', { minimumFractionDigits: digits, maximumFractionDigits: digits })} %`
