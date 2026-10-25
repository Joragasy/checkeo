# Checkeo — profil navetteur d'un trajet en train

Checkeo aide à évaluer un trajet ferroviaire quotidien avant de choisir où habiter ou
travailler. Pour deux gares (ou deux villes entières, ex. « Lille » et « Paris »), l'application
affiche, à l'aller et au retour :

- la **distribution des trains directs** sur un jour type (semaine, samedi ou dimanche) ;
- les indicateurs du **profil navetteur** : trains arrivant avant une heure cible, trains
  repartant après une heure cible, plus long trou entre 6 h et 21 h, nombre de trains en
  pointe, durée du trajet (min / médiane / max) ;
- la **fiabilité historique** publiée par la SNCF : ponctualité moyenne sur 12 mois, courbe
  mensuelle, taux d'annulation et causes des retards quand elles existent.

Interface en français, adaptée au mobile, en mode clair ou sombre.

---

## Installation

Prérequis : Python ≥ 3.12 avec [uv](https://docs.astral.sh/uv/), Node.js ≥ 20.

```bash
# Backend
cd backend
uv sync

# Frontend
cd ../frontend
npm install
```

## Mise à jour des données

```bash
cd backend
uv run python -m checkeo.ingest.run
```

Le script télécharge toutes les sources dans `data/raw/`, puis construit la base
`data/checkeo.duckdb`. L'ancienne base n'est remplacée qu'une fois la nouvelle entièrement
écrite. Comptez environ 30 secondes. Relancez-le aussi souvent que nécessaire : le GTFS est
republié chaque jour, la régularité chaque mois.

Options :

| Option | Effet |
|---|---|
| `--offline` | reconstruit la base à partir de `data/raw/` sans retélécharger |
| `--sample-start 2026-12-14` | début de la fenêtre d'échantillonnage du jour type (par défaut : aujourd'hui). Utile pour étudier les horaires d'après le **changement de service de mi-décembre**. |
| `--weeks 4` | nombre de semaines échantillonnées |
| `--out chemin.duckdb` | emplacement de la base |

Le rapport affiché en fin d'exécution liste les libellés de régularité que l'on n'a pas pu
rapprocher d'une gare. Pour corriger un rapprochement, complétez
`backend/checkeo/ingest/regularity_overrides.csv`.

Variables d'environnement : `CHECKEO_DATA_DIR`, `CHECKEO_DB`, `CHECKEO_CORS`.

## Inspecter les données

```bash
cd backend
uv run python -m checkeo.ui          # http://localhost:4213, lecture seule
```

Ouvre `data/checkeo.duckdb` dans l'[interface web DuckDB](https://duckdb.org/docs/stable/core_extensions/ui)
(extension `ui`, téléchargée au premier lancement). En lecture seule, elle peut tourner en même
temps que l'API. Ctrl+C pour arrêter.

| Option | Effet |
|---|---|
| `--db chemin.duckdb` | base à ouvrir (défaut : `CHECKEO_DB`) |
| `--port 4213` | port local de l'interface |
| `--write` | ouvre la base en écriture |

Avec la CLI DuckDB installée, `duckdb -ui data/checkeo.duckdb` fait la même chose.

## Lancer l'application

**Développement** (deux terminaux) :

```bash
cd backend && uv run uvicorn checkeo.api.main:app --reload --port 8000
cd frontend && npm run dev          # http://localhost:5173 (proxy /api → :8000)
```

**Production** : `cd frontend && npm run build`, puis lancez seulement le backend. Il sert
le frontend compilé (`frontend/dist`) à la racine `/` :

```bash
cd backend && uv run uvicorn checkeo.api.main:app --host 0.0.0.0 --port 8000
```

## Déploiement Nomad

Trois jobs, une image chacun (`deploy/`), poussées sur `registry.enopt.ovh:80` :

| Job | Image | Rôle | Accès (Traefik) |
|---|---|---|---|
| `checkeo-frontend` | `checkeo-frontend` | fichiers statiques du frontend | `http://checkeo.enopt.ovh` |
| `checkeo-backend` | `checkeo-backend` | API FastAPI, base en lecture seule | `http://checkeo.enopt.ovh/api`, `/docs` |
| `checkeo-database` | `checkeo-database` | ingestion au démarrage, puis interface web DuckDB | `http://checkeo-db.enopt.ovh` (réseau local uniquement) |

La base est partagée par le host volume `checkeo-data`, à créer une fois :

```bash
export NOMAD_ADDR=http://192.168.1.21:4646 NOMAD_TOKEN=…
sed -n 's/^#> //p' deploy/database.nomad.hcl | nomad volume create -
```

Construction, push et déploiement (tag = commit court) :

```bash
deploy/deploy.sh all              # ou frontend | backend | database ; --no-run pour seulement pousser
```

Mise à jour des données : `nomad job restart -yes checkeo-database` relance l'ingestion, puis
`nomad job restart -yes checkeo-backend` (l'API garde l'ancienne base ouverte jusqu'au redémarrage).

## API

| Endpoint | Description |
|---|---|
| `GET /api/stations?q=lil&limit=10` | autocomplétion, insensible aux accents et à la casse. Renvoie des villes (`city:<INSEE>`, toutes leurs gares) et des gares (`StopArea:OCE<UIC>`). |
| `GET /api/profile?from=…&to=…&day_type=weekday&bin=60&arrive_by=09:00&leave_after=18:00&include_buses=false` | profil complet : `outbound` (aller), `inbound` (retour), fiabilité, métadonnées |
| `GET /api/meta` | période de validité des horaires, dates échantillonnées, fraîcheur de chaque source |

`day_type` : `weekday`, `saturday` ou `sunday`. `bin` : 15, 30, 60 ou 120 minutes.
La documentation interactive est disponible sur `/docs`.

## Tests

```bash
cd backend && uv run pytest
```

Les tests s'appuient sur un petit GTFS fabriqué à la main (`backend/tests/fixtures/mini_gtfs`).
Ils couvrent :

- `calendar.txt` combiné à `calendar_dates.txt` (ajouts et suppressions) ;
- l'ordre des arrêts et les règles de montée et de descente ;
- les horaires au-delà de 24:00 ;
- les trains couplés et les trains occasionnels ;
- les indicateurs et la fiabilité ;
- l'API.

---

## Comment c'est calculé

**Trajets directs.** Un train est retenu s'il dessert la gare d'origine **avant** la gare de
destination (`stop_sequence`), si l'on peut y monter (`pickup_type ≠ 1`) et en descendre
(`drop_off_type ≠ 1`). Quand une ville est choisie, toutes ses gares sont prises en compte.
Si un train dessert deux gares de la même ville, on retient la dernière montée possible et
la première descente possible.

**Regroupement par ville.** Le GTFS SNCF ne relie pas les gares d'une même ville : Lille
Flandres et Lille Europe sont deux zones d'arrêt indépendantes. On les regroupe donc par
commune, avec le code INSEE du référentiel « Gares de voyageurs », joint par code UIC. Les
arrondissements de Paris, Lyon et Marseille sont ramenés à leur commune.

**Jour type.** Plutôt que d'utiliser une date arbitraire, on échantillonne des dates réelles :
par défaut, les 4 semaines à venir, jours fériés exclus (19 jours de semaine environ, 4
samedis, 4 dimanches).
- Un train, identifié par son numéro, fait partie du jour type s'il circule **au moins un
  jour sur deux** parmi ces dates. Ses horaires sont ceux qu'il a le plus souvent : ils
  peuvent varier de quelques minutes d'une semaine à l'autre à cause de travaux.
- Les trains moins fréquents, comme les renforts du vendredi, sont listés à part.
- Le nombre de trains par date (médiane, minimum, maximum) est affiché pour montrer la
  variabilité.
- Deux numéros qui roulent ensemble aux mêmes horaires (unités multiples) ne comptent que
  pour un seul train.

**Horaires après minuit.** Les horaires GTFS au-delà de 24:00:00 sont conservés tels quels
dans les calculs. Ils s'affichent « 00:40 (+1) ». Dans l'histogramme, ils sont ramenés dans
la tranche correspondante du cycle de 24 h.

**Aller et retour.** L'aller est analysé par heure d'**arrivée** : heure cible, pointe
7 h – 9 h à l'arrivée, histogramme. Le retour est analysé par heure de **départ** : heure
cible, pointe 17 h – 20 h au départ, histogramme.

**Fiabilité, sans extrapolation.**

| Famille | Série affichée | Si la donnée manque |
|---|---|---|
| TGV et Intercités | la liaison publiée dont les gares de départ et d'arrivée correspondent à celles des trains du profil, dans le même sens | « donnée indisponible » |
| TER | la moyenne des TER de la région d'exploitation des trains, présentée comme telle (la SNCF ne publie pas de données par ligne) | — |

- La région d'exploitation d'un TER est la région la plus représentée parmi ses arrêts, hors
  Île-de-France. Exemple : un TER Paris – Chartres compte comme un TER Centre-Val de Loire.
- La ponctualité TGV est calculée ainsi : 1 − trains en retard à l'arrivée / trains ayant
  circulé.
- Les moyennes sur 12 mois sont pondérées par le nombre de trains.
- Un bandeau signale les séries dont le dernier mois publié date de plus de 3 mois.

---

## Sources et licences

| Donnée | Source | Licence |
|---|---|---|
| Horaires théoriques TGV, Intercités, TER (GTFS) | `https://eu.ftp.opendatasoft.com/sncf/plandata/Export_OpenData_SNCF_GTFS_NewTripId.zip`, référencé dans le jeu [horaires-sncf](https://ressources.data.sncf.com/explore/dataset/horaires-sncf/) et sur [transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/horaires-sncf) | ODbL |
| Régularité mensuelle TGV par liaisons | [regularite-mensuelle-tgv-aqst](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-tgv-aqst/) | ODbL |
| Régularité mensuelle TER (par région) | [regularite-mensuelle-ter](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-ter/) | ODbL |
| Régularité mensuelle Intercités | [regularite-mensuelle-intercites](https://ressources.data.sncf.com/explore/dataset/regularite-mensuelle-intercites/) | ODbL |
| Référentiel des gares de voyageurs | [gares-de-voyageurs](https://ressources.data.sncf.com/explore/dataset/gares-de-voyageurs/) | ODbL |
| Communes et régions | [geo.api.gouv.fr](https://geo.api.gouv.fr/decoupage-administratif) | Licence Ouverte 2.0 |
| Photo du bandeau (`frontend/public/hero-viaduc-cize*.jpg`, recadrée et compressée) | [TGV Duplex, viaduc de Cize-Bolozon](https://commons.wikimedia.org/wiki/File:SNCF_TGV_Duplex_Viaduc_de_Cize_-_Bolozon.jpg), Kabelleger / David Gubler | CC BY-SA 3.0 |

Les données SNCF sont publiées par **SNCF Voyageurs** et **SNCF Gares & Connexions** sur
[ressources.data.sncf.com](https://ressources.data.sncf.com) sous **Open Database License
(ODbL) 1.0**.
- Toute réutilisation doit citer la source.
- Toute base de données dérivée, comme `data/checkeo.duckdb`, doit être partagée sous la même
  licence.

L'application affiche ces mentions dans son pied de page.

## Limites connues

- **Trajets directs uniquement** : pas de correspondances en V1.
- **Horaires théoriques.** Le GTFS couvre environ 5 mois et intègre les adaptations connues la
  veille à 17 h, mais pas le temps réel. Il n'a pas de `calendar.txt` : seul
  `calendar_dates.txt` est fourni (le code gère quand même les deux).
- **Changement de service annuel (mi-décembre).** Le jour type reflète la fenêtre
  échantillonnée. Pour la période suivante, relancez l'ingestion avec `--sample-start`.
- **Transilien et RER non inclus.** Ils font l'objet d'un GTFS séparé (`sncf-transilien-gtfs`).
  Les TER d'Île-de-France sont présents, mais sans série de régularité francilienne.
- **Régularité TGV** : environ 110 grandes liaisons seulement, surtout de bout en bout. Une
  liaison intermédiaire (ex. Arras → Paris) n'a pas de série. La régularité est mesurée au
  **terminus du train**, pas à la gare de descente du voyageur. L'inclusion des OUIGO dans la
  série « National » n'est pas documentée.
- **Régularité TER** : uniquement par région. Les sous-périmètres publiés (« Etoile Amiens »,
  « Loire Océan », « Sud Azur ») et les anciennes régions d'avant 2016 ne sont pas utilisés.
- **Régularité Intercités** : publiée avec plusieurs mois de retard (mai 2026 au 24/10/2026),
  et sans causes de retard.
- **Libellés non rapprochés** : quelques libellés de régularité ne correspondent à aucune gare
  du GTFS (ex. « ITALIE », « MADRID », « ZURICH »). Ces liaisons restent indisponibles.
- **Gares étrangères** : absentes du référentiel français, elles ne sont pas regroupées par
  ville.

## Architecture

```
backend/checkeo/
  ingest/   téléchargement, normalisation GTFS, gares, régularité, construction DuckDB
  core/     logique pure, testée : horaires GTFS, calendriers, trajets directs, jour type,
            indicateurs, fiabilité
  service.py  requêtes DuckDB et assemblage d'un profil
  ui.py     lancement de l'interface web DuckDB sur la base
  api/      FastAPI
frontend/src/  Vue 3 + Vuetify 3 + ECharts
```

Prévu dans l'architecture, mais pas codé en V1 :

- **Correspondances** : les trajets sont des `Journey` composés de `Leg`
  (`core/trips.py`). Un calcul de type RAPTOR pourra produire des trajets à plusieurs legs
  sans changer les indicateurs.
- **Temps réel** : la fiabilité passe par `core/reliability.py`. Une archive GTFS-RT (API
  SNCF, clé requise) pourrait alimenter une table `rt_observations` et fournir une fiabilité
  par train et par horaire.
- **Coût du trajet** : le champ `cost` est réservé dans la réponse `/api/profile`.
- **Mode inversé** (« où habiter pour arriver avant 9 h ? ») : la table des gares et les
  groupes de villes permettent d'appliquer la même fonction de profil à toutes les origines,
  puis de calculer un score.
