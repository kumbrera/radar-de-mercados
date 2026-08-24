#!/usr/bin/env bash
# Ejecuta el informe diario. Pensado para cron.
#   0 8 * * * /ruta/a/cripto-radar/ejecutar_diario.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 radar.py --silencio >> data/registro.log 2>&1
