// Libellés des modes GTFS. Deux tables distinctes : libellé lisible (listes de trains)
// et abréviation (suggestions de gares).

export const MODE_LABEL: Record<string, string> = {
  'TGV INOUI': 'TGV INOUI', OUIGO: 'OUIGO', 'Train TER': 'TER', 'Car TER': 'Car TER', INTERCITES: 'Intercités',
  'INTERCITES de nuit': 'Intercités de nuit', TramTrain: 'Tram-train',
}

export const MODE_ABBR: Record<string, string> = {
  'TGV INOUI': 'TGV', OUIGO: 'OUIGO', 'Train TER': 'TER', INTERCITES: 'IC', 'INTERCITES de nuit': 'IC nuit',
  TramTrain: 'Tram-train', ICE: 'ICE', Lyria: 'Lyria',
}
