// Types et appels de l'API Checkeo (voir backend/checkeo/api/main.py).

export type DayType = 'weekday' | 'saturday' | 'sunday'

export interface StationHit {
  id: string
  kind: 'city' | 'station'
  name: string
  city: string | null
  n_stations: number
  modes: string[]
}

export interface TrainBrief {
  dep_s: number
  arr_s: number
  dep: string
  arr: string
  duration_min: number
  train_numbers: string[]
}

export interface TrainRow {
  train_number: string
  mode: string
  family: string
  from_stop: string
  from_name: string | null
  to_stop: string
  to_name: string | null
  dep_s: number
  arr_s: number
  dep: string
  arr: string
  duration_min: number
  n_days: number
  frequency: number
  weekdays: string[]
  dep_range: [string, string] | null
}

export interface Bin {
  start_s: number
  end_s: number
  count: number
}

export interface MonthPoint {
  month: string
  rate: number | null
  cancel_rate: number | null
  planned: number | null
}

export interface Cause {
  key: string
  label: string
  percent: number
}

export interface ReliabilityBlock {
  family: 'TGV' | 'IC' | 'TER'
  family_label: string
  scope: 'liaison' | 'region'
  label: string | null
  available: boolean
  note: string
  dataset_modified: string | null
  window?: { from: string; to: string; months: number }
  punctuality?: number | null
  cancel_rate?: number | null
  trains_planned?: number | null
  causes?: Cause[] | null
  monthly?: MonthPoint[]
  last_month?: string
  stale?: boolean
  lag_months?: number
}

export interface DirectionProfile {
  count: number
  histogram: Bin[]
  histogram_by: 'dep' | 'arr'
  largest_gap: { window: [number, number]; minutes: number; from: string; to: string; trains_in_window: number }
  durations: { min: number | null; median: number | null; max: number | null }
  arrive_by?: { target_s: number; count: number; first: TrainBrief | null; last: TrainBrief | null }
  leave_after?: { target_s: number; count: number; first: TrainBrief | null; last: TrainBrief | null }
  peak: { window: [number, number]; by: 'dep' | 'arr'; count: number }
  trains: TrainRow[]
  occasional_trains: TrainRow[]
  daily_counts: { n_dates: number; median: number | null; min: number | null; max: number | null; per_date: Record<string, number> }
  reliability: ReliabilityBlock[]
}

export interface SourceMeta {
  title?: string
  url?: string
  page?: string
  modified?: string
  last_modified?: string
  license?: string
  downloaded_at?: string
}

export interface Meta {
  feed_start: string
  feed_end: string
  feed_version: string | null
  built_at: string
  samples: Record<DayType, string[]>
  regularity_last_month: Record<string, string>
  sources: Record<string, SourceMeta>
}

export interface Place {
  id: string
  kind: 'city' | 'station'
  name: string
  stop_area_ids: string[]
}

export interface Profile {
  from: Place
  to: Place
  day_type: DayType
  day_type_label: string
  outbound: DirectionProfile
  inbound: DirectionProfile
  meta: Meta & { sample_dates: string[]; presence_threshold: number; include_buses: boolean }
}

export interface ProfileParams {
  from: string
  to: string
  day_type: DayType
  bin: number
  arrive_by: string
  leave_after: string
  include_buses: boolean
}

async function get<T>(path: string, params: Record<string, string | number | boolean>, signal?: AbortSignal): Promise<T> {
  const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const r = await fetch(`/api/${path}?${qs}`, { signal })
  if (!r.ok) {
    let detail = `Erreur ${r.status}`
    try {
      const body = await r.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch { /* corps non JSON */ }
    throw new Error(detail)
  }
  return r.json() as Promise<T>
}

export const searchStations = (q: string, signal?: AbortSignal) =>
  get<{ results: StationHit[] }>('stations', { q, limit: 12 }, signal).then((r) => r.results)

export const fetchProfile = (p: ProfileParams, signal?: AbortSignal) =>
  get<Profile>('profile', { ...p }, signal)

export const fetchMeta = () => get<Meta>('meta', {})
