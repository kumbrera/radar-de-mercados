"""
Fuentes de datos.

Todo lo que usa aquí es GRATIS y sin tarjeta:
  • CoinGecko API pública  -> precios, market cap, volumen, GitHub, comunidad
  • alternative.me         -> índice de miedo y codicia

CoinGecko en plan gratuito permite del orden de 10-30 peticiones por minuto.
El cliente respeta ese límite solo (pausas + reintentos con espera creciente)
y cachea las respuestas en disco para no repetir llamadas innecesarias.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from pathlib import Path
from typing import Any

import requests

from . import config


# ---------------------------------------------------------------------------
# Cliente HTTP con caché y control de rate limit
# ---------------------------------------------------------------------------

class ClienteAPI:
    def __init__(self, usar_cache: bool = True, verbose: bool = True):
        self.usar_cache = usar_cache
        self.verbose = verbose
        self.sesion = requests.Session()
        self.sesion.headers.update({
            "Accept": "application/json",
            "User-Agent": "cripto-radar/1.0 (uso personal)",
        })
        if config.COINGECKO_API_KEY:
            self.sesion.headers["x-cg-demo-api-key"] = config.COINGECKO_API_KEY
        self._ultima_peticion = 0.0
        self.peticiones_hechas = 0
        self.fallos = []

    # -- caché --------------------------------------------------------------

    def _ruta_cache(self, url: str, params: dict | None) -> Path:
        clave = url + json.dumps(params or {}, sort_keys=True)
        nombre = hashlib.sha256(clave.encode()).hexdigest()[:24]
        return config.DIR_CACHE / f"{nombre}.json"

    def _leer_cache(self, ruta: Path) -> Any | None:
        if not self.usar_cache or not ruta.exists():
            return None
        edad = time.time() - ruta.stat().st_mtime
        if edad > config.TTL_CACHE_SEGUNDOS:
            return None
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _escribir_cache(self, ruta: Path, datos: Any) -> None:
        if not self.usar_cache:
            return
        try:
            ruta.write_text(json.dumps(datos), encoding="utf-8")
        except OSError:
            pass

    # -- peticiones ---------------------------------------------------------

    def _esperar_turno(self) -> None:
        transcurrido = time.time() - self._ultima_peticion
        if transcurrido < config.PAUSA_ENTRE_PETICIONES:
            time.sleep(config.PAUSA_ENTRE_PETICIONES - transcurrido)

    def get(self, url: str, params: dict | None = None) -> Any | None:
        ruta = self._ruta_cache(url, params)
        cacheado = self._leer_cache(ruta)
        if cacheado is not None:
            return cacheado

        for intento in range(1, config.REINTENTOS + 1):
            self._esperar_turno()
            try:
                r = self.sesion.get(url, params=params, timeout=config.TIMEOUT)
                self._ultima_peticion = time.time()
                self.peticiones_hechas += 1

                if r.status_code == 429:
                    espera = 15 * intento
                    self._log(f"  rate limit alcanzado, esperando {espera}s...")
                    time.sleep(espera)
                    continue

                r.raise_for_status()
                datos = r.json()
                self._escribir_cache(ruta, datos)
                return datos

            except requests.RequestException as e:
                self._ultima_peticion = time.time()
                if intento == config.REINTENTOS:
                    self.fallos.append(f"{url}: {e}")
                    self._log(f"  ! fallo definitivo en {url.split('/')[-1]}: {e}")
                    return None
                time.sleep(3 * intento)
        return None

    def _log(self, mensaje: str) -> None:
        if self.verbose:
            print(mensaje, flush=True)

    # -- endpoints concretos ------------------------------------------------

    def estado_global(self) -> dict | None:
        """Capitalización total del mercado y dominancia de BTC."""
        datos = self.get(f"{config.BASE_COINGECKO}/global")
        return (datos or {}).get("data")

    def mercado(self, por_pagina: int = 250, pagina: int = 1) -> list[dict]:
        """Top de monedas por capitalización, con variaciones y sparkline de 7d."""
        datos = self.get(
            f"{config.BASE_COINGECKO}/coins/markets",
            {
                "vs_currency": config.MONEDA,
                "order": "market_cap_desc",
                "per_page": min(por_pagina, 250),
                "page": pagina,
                "sparkline": "true",
                "price_change_percentage": "1h,24h,7d,30d",
            },
        )
        return datos or []

    def historico(self, moneda_id: str, dias: int = 365) -> dict | None:
        """
        Precios y volúmenes diarios. Devuelve listas ordenadas de antiguo a nuevo.

        El plan gratuito limita el histórico a 365 días, que es más que suficiente
        para calcular una SMA 200.
        """
        datos = self.get(
            f"{config.BASE_COINGECKO}/coins/{moneda_id}/market_chart",
            {"vs_currency": config.MONEDA, "days": min(dias, 365), "interval": "daily"},
        )
        if not datos or "prices" not in datos:
            return None
        return {
            "fechas": [p[0] for p in datos["prices"]],
            "precios": [p[1] for p in datos["prices"]],
            "volumenes": [v[1] for v in datos.get("total_volumes", [])],
        }

    def ficha(self, moneda_id: str) -> dict | None:
        """Datos de desarrollo (GitHub), comunidad y supply de una moneda."""
        return self.get(
            f"{config.BASE_COINGECKO}/coins/{moneda_id}",
            {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "true",
                "sparkline": "false",
            },
        )

    def tendencias(self) -> list[dict]:
        """Las monedas más buscadas en CoinGecko en las últimas 24h."""
        datos = self.get(f"{config.BASE_COINGECKO}/search/trending")
        return [c.get("item", {}) for c in (datos or {}).get("coins", [])]

    def miedo_codicia(self, dias: int = 30) -> list[dict]:
        """Índice de miedo y codicia, del más reciente al más antiguo."""
        datos = self.get(config.BASE_FEAR_GREED, {"limit": dias, "format": "json"})
        return (datos or {}).get("data", [])


# ---------------------------------------------------------------------------
# Modo demo: datos sintéticos realistas, sin tocar internet
#
# Sirve para dos cosas: probar el sistema antes de conectarlo, y poder trastear
# con el diseño del informe sin gastar peticiones de la API.
# ---------------------------------------------------------------------------

_PLANTILLA_DEMO = [
    # id, nombre, símbolo, precio, mcap, deriva anual, volatilidad, %circulante
    ("bitcoin",      "Bitcoin",    "btc",  61240.0, 1_215_000_000_000, 0.55, 0.45, 95.2),
    ("ethereum",     "Ethereum",   "eth",   2985.0,   359_000_000_000, 0.40, 0.55, 99.5),
    ("solana",       "Solana",     "sol",    142.5,    67_000_000_000, 0.70, 0.85, 82.0),
    ("chainlink",    "Chainlink",  "link",    14.20,    9_100_000_000, 0.20, 0.75, 63.0),
    ("arbitrum",     "Arbitrum",   "arb",     0.612,    2_400_000_000, -0.15, 0.90, 41.0),
    ("render-token", "Render",     "rndr",    4.83,     2_500_000_000, 0.35, 0.95, 71.0),
    ("bittensor",    "Bittensor",  "tao",   298.40,     2_600_000_000, 0.45, 1.10, 63.5),
    ("sui",          "Sui",        "sui",     2.94,     9_800_000_000, 0.60, 1.00, 33.0),
    ("aave",         "Aave",       "aave",  178.30,     2_650_000_000, 0.30, 0.80, 93.0),
    ("hyperliquid",  "Hyperliquid","hype",   28.15,     9_400_000_000, 1.20, 1.30, 33.4),
    ("celestia",     "Celestia",   "tia",     4.12,       870_000_000, -0.40, 1.05, 21.0),
    ("injective",    "Injective",  "inj",    21.60,     2_100_000_000, 0.10, 0.95, 97.0),
    ("the-graph",    "The Graph",  "grt",     0.184,      1_760_000_000, 0.05, 0.85, 94.0),
    ("pendle",       "Pendle",     "pendle",  4.37,       700_000_000, 0.50, 1.00, 63.0),
    ("dydx",         "dYdX",       "dydx",    1.24,       880_000_000, -0.30, 0.95, 72.0),
    ("optimism",     "Optimism",   "op",      1.71,     2_800_000_000, -0.10, 0.90, 46.0),
]


class FuenteDemo:
    """Imita a ClienteAPI pero genera los datos con un paseo aleatorio."""

    def __init__(self, semilla: int = 20260821, verbose: bool = True):
        self.rng = random.Random(semilla)
        self.verbose = verbose
        self.peticiones_hechas = 0
        self.fallos = []
        self._series: dict[str, dict] = {}
        self._construir_series()

    def _construir_series(self) -> None:
        ahora_ms = int(time.time() * 1000)
        dia_ms = 86_400_000
        for cid, _n, _s, precio_final, mcap, deriva, vol, _circ in _PLANTILLA_DEMO:
            dias = 365
            # Generamos hacia atrás desde el precio actual con un paseo aleatorio
            precios = [precio_final]
            for _ in range(dias - 1):
                paso_deriva = deriva / 365.0
                choque = self.rng.gauss(0, vol / math.sqrt(365))
                previo = precios[0] / math.exp(paso_deriva + choque)
                precios.insert(0, max(previo, precio_final * 0.02))

            base_vol_diario = mcap * 0.06
            volumenes = [
                max(base_vol_diario * (1 + self.rng.gauss(0, 0.45)), base_vol_diario * 0.1)
                for _ in precios
            ]
            volumenes[-1] *= self.rng.choice([0.8, 1.0, 1.3, 2.4])

            fechas = [ahora_ms - (dias - 1 - i) * dia_ms for i in range(dias)]
            self._series[cid] = {
                "fechas": fechas,
                "precios": precios,
                "volumenes": volumenes,
            }

    # -- misma interfaz que ClienteAPI --------------------------------------

    def estado_global(self) -> dict:
        return {
            "total_market_cap": {config.MONEDA: 2_180_000_000_000},
            "total_volume": {config.MONEDA: 94_500_000_000},
            "market_cap_percentage": {"btc": 55.7, "eth": 16.4},
            "market_cap_change_percentage_24h_usd": 1.84,
        }

    def mercado(self, por_pagina: int = 250, pagina: int = 1) -> list[dict]:
        if pagina > 1:
            return []
        salida = []
        for i, (cid, nombre, simbolo, _p, mcap, _d, _v, circ) in enumerate(_PLANTILLA_DEMO):
            serie = self._series[cid]["precios"]
            precio = serie[-1]
            def cambio(dias):
                return (serie[-1] / serie[-dias - 1] - 1) * 100 if len(serie) > dias else 0.0
            ath = max(serie) * self.rng.uniform(1.0, 2.4)
            salida.append({
                "id": cid,
                "symbol": simbolo,
                "name": nombre,
                "current_price": precio,
                "market_cap": mcap,
                "market_cap_rank": i + 1,
                "total_volume": self._series[cid]["volumenes"][-1],
                "high_24h": precio * 1.03,
                "low_24h": precio * 0.96,
                "price_change_percentage_24h": cambio(1),
                "price_change_percentage_1h_in_currency": self.rng.gauss(0, 0.6),
                "price_change_percentage_24h_in_currency": cambio(1),
                "price_change_percentage_7d_in_currency": cambio(7),
                "price_change_percentage_30d_in_currency": cambio(30),
                "circulating_supply": mcap / precio,
                "total_supply": (mcap / precio) / (circ / 100.0),
                "ath": ath,
                "ath_change_percentage": (precio / ath - 1) * 100,
                "sparkline_in_7d": {"price": serie[-168:]},
            })
        return salida

    def historico(self, moneda_id: str, dias: int = 365) -> dict | None:
        serie = self._series.get(moneda_id)
        if not serie:
            return None
        return {
            "fechas": serie["fechas"][-dias:],
            "precios": serie["precios"][-dias:],
            "volumenes": serie["volumenes"][-dias:],
        }

    def ficha(self, moneda_id: str) -> dict | None:
        entrada = next((x for x in _PLANTILLA_DEMO if x[0] == moneda_id), None)
        if not entrada:
            return None
        cid, nombre, simbolo, _p, mcap, _d, _v, circ = entrada
        serie = self._series[cid]["precios"]
        precio = serie[-1]
        commits = self.rng.choice([0, 2, 8, 25, 60, 140])
        return {
            "id": cid,
            "name": nombre,
            "symbol": simbolo,
            "categories": self.rng.choice([
                ["Smart Contract Platform", "Layer 1"],
                ["DeFi", "Lending"],
                ["Infrastructure", "Oracle"],
                ["AI & Big Data"],
                ["Layer 2", "Scaling"],
            ]),
            "description": {"es": "", "en": "Proyecto de demostración generado localmente."},
            "links": {"homepage": ["https://example.org"],
                      "repos_url": {"github": ["https://github.com/demo/demo"]}},
            "developer_data": {
                "forks": self.rng.randint(20, 2200),
                "stars": self.rng.randint(80, 18000),
                "subscribers": self.rng.randint(10, 900),
                "total_issues": self.rng.randint(100, 4000),
                "closed_issues": self.rng.randint(80, 3800),
                "pull_request_contributors": self.rng.randint(3, 320),
                "commit_count_4_weeks": commits,
            },
            "community_data": {
                "twitter_followers": self.rng.randint(15_000, 2_500_000),
                "reddit_subscribers": self.rng.randint(1_000, 800_000),
                "telegram_channel_user_count": self.rng.randint(500, 120_000),
            },
            "market_data": {
                "current_price": {config.MONEDA: precio},
                "market_cap": {config.MONEDA: mcap},
                "total_volume": {config.MONEDA: self._series[cid]["volumenes"][-1]},
                "circulating_supply": mcap / precio,
                "total_supply": (mcap / precio) / (circ / 100.0),
                "max_supply": (mcap / precio) / (circ / 100.0),
                "ath": {config.MONEDA: max(serie) * 1.6},
                "ath_change_percentage": {config.MONEDA: (precio / (max(serie) * 1.6) - 1) * 100},
                "ath_date": {config.MONEDA: "2021-11-09T00:00:00.000Z"},
            },
            "genesis_date": self.rng.choice(
                ["2015-07-30", "2017-06-01", "2020-03-14", "2021-08-01", "2023-04-12"]
            ),
        }

    def tendencias(self) -> list[dict]:
        elegidas = self.rng.sample(_PLANTILLA_DEMO, 5)
        return [
            {"id": c[0], "name": c[1], "symbol": c[2].upper(), "market_cap_rank": i + 1}
            for i, c in enumerate(elegidas)
        ]

    def miedo_codicia(self, dias: int = 30) -> list[dict]:
        valores = []
        v = 62
        ahora = int(time.time())
        for d in range(dias):
            v = max(5, min(95, v + self.rng.randint(-7, 6)))
            etiqueta = (
                "Extreme Fear" if v < 25 else
                "Fear" if v < 45 else
                "Neutral" if v < 55 else
                "Greed" if v < 75 else "Extreme Greed"
            )
            valores.append({
                "value": str(v),
                "value_classification": etiqueta,
                "timestamp": str(ahora - d * 86400),
            })
        return valores


def obtener_fuente(demo: bool = False, usar_cache: bool = True, verbose: bool = True):
    """Devuelve la fuente de datos adecuada."""
    if demo:
        return FuenteDemo(verbose=verbose)
    return ClienteAPI(usar_cache=usar_cache, verbose=verbose)
