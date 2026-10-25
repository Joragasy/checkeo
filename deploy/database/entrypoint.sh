#!/bin/sh
# Lance l'interface web DuckDB et l'expose sur 0.0.0.0:4214.
# Le serveur de l'extension ui n'écoute que sur localhost (::1 ou 127.0.0.1 selon que l'IPv6 est
# active dans le conteneur) : socat relaie le port en TCP brut vers l'adresse effectivement utilisée.
set -e
python -m checkeo.ui --db "${CHECKEO_DB:-/data/checkeo.duckdb}" --port 4213 &
ui=$!
trap 'kill "$ui" 2>/dev/null' INT TERM

# 4213 = 0x1075, état 0A = LISTEN
listening() { awk '$2 ~ /:1075$/ && $4 == "0A" { found = 1 } END { exit !found }' "$1" 2>/dev/null; }
target=
for _ in $(seq 60); do
  if listening /proc/net/tcp6; then target="TCP6:[::1]:4213"; break; fi
  if listening /proc/net/tcp; then target="TCP4:127.0.0.1:4213"; break; fi
  kill -0 "$ui" 2>/dev/null || exit 1
  sleep 1
done
[ -n "$target" ] || { echo "l'interface DuckDB n'écoute pas sur 4213" >&2; exit 1; }
echo "relais 0.0.0.0:4214 -> $target"

socat TCP4-LISTEN:4214,fork,reuseaddr "$target" &
proxy=$!
# Si l'un des deux processus s'arrête, le conteneur s'arrête et Nomad le redémarre.
while kill -0 "$ui" 2>/dev/null && kill -0 "$proxy" 2>/dev/null; do sleep 5; done
kill "$ui" "$proxy" 2>/dev/null || true
exit 1
