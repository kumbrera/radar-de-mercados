"""
Fuentes de datos de bolsa: índices, ETFs y acciones.

Todo gratuito y sin API key:
  • Yahoo Finance (endpoint público de gráficos) -> histórico diario y datos
    fundamentales (PER, dividendo, capitalización, TER en el caso de ETFs)
  • Stooq (CSV público) -> plan B si Yahoo falla

Ninguno de los dos es una API oficial con contrato de servicio, así que el
cliente está escrito para degradar con elegancia: si un símbolo falla, se
informa y se sigue con el resto en vez de reventar el informe entero.
"""

from __future__ import annotations

import csv
import io
import json
import math
import random
import time
from datetime import datetime, timedelta, timezone

import requests

from . import config

BASE_YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
BASE_YAHOO_QUOTE = "https://query1.finance.yahoo.com/v7/finance/quote"
BASE_YAHOO_SUMMARY = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"
BASE_YAHOO_BUSCAR = "https://query2.finance.yahoo.com/v1/finance/search"
BASE_STOOQ = "https://stooq.com/q/d/l/"

CABECERAS = {
    # Yahoo rechaza peticiones sin un User-Agent de navegador
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

class ClienteBolsa:
    def __init__(self, usar_cache: bool = True, verbose: bool = True):
        self.usar_cache = usar_cache
        self.verbose = verbose
        self.sesion = requests.Session()
        self.sesion.headers.update(CABECERAS)
        self.peticiones_hechas = 0
        self.fallos: list[str] = []
        self._ultima = 0.0
        self._crumb: str | None = None

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)

    # -- caché en disco -----------------------------------------------------

    def _cache(self, clave: str):
        import hashlib
        from pathlib import Path
        nombre = hashlib.sha256(f"bolsa:{clave}".encode()).hexdigest()[:24]
        return Path(config.DIR_CACHE) / f"{nombre}.json"

    def _leer_cache(self, clave: str):
        if not self.usar_cache:
            return None
        ruta = self._cache(clave)
        if not ruta.exists():
            return None
        if time.time() - ruta.stat().st_mtime > config.TTL_CACHE_SEGUNDOS:
            return None
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _guardar_cache(self, clave: str, datos) -> None:
        if not self.usar_cache:
            return
        try:
            self._cache(clave).write_text(json.dumps(datos), encoding="utf-8")
        except (OSError, TypeError):
            pass

    # -- HTTP ---------------------------------------------------------------

    def _pausa(self) -> None:
        t = time.time() - self._ultima
        if t < config.PAUSA_BOLSA:
            time.sleep(config.PAUSA_BOLSA - t)

    def _get(self, url: str, params: dict | None = None, texto: bool = False):
        for intento in range(1, config.REINTENTOS + 1):
            self._pausa()
            try:
                r = self.sesion.get(url, params=params, timeout=config.TIMEOUT)
                self._ultima = time.time()
                self.peticiones_hechas += 1
                if r.status_code in (429, 999):
                    espera = 10 * intento
                    self._log(f"    límite alcanzado, esperando {espera}s...")
                    time.sleep(espera)
                    continue
                r.raise_for_status()
                return r.text if texto else r.json()
            except (requests.RequestException, json.JSONDecodeError) as e:
                self._ultima = time.time()
                if intento == config.REINTENTOS:
                    self.fallos.append(f"{url}: {e}")
                    return None
                time.sleep(2 * intento)
        return None

    # -- histórico ----------------------------------------------------------

    def historico(self, simbolo: str, rango: str = "2y") -> dict | None:
        """
        Cierres diarios de los últimos N años.

        Devuelve fechas (ms), precios, volúmenes y metadatos (divisa, bolsa,
        nombre largo). Prueba Yahoo y, si falla, Stooq.
        """
        clave = f"hist:{simbolo}:{rango}"
        cacheado = self._leer_cache(clave)
        if cacheado:
            return cacheado

        datos = self._historico_yahoo(simbolo, rango)
        if datos is None:
            self._log(f"    {simbolo}: Yahoo no responde, probando Stooq...")
            datos = self._historico_stooq(simbolo)
        if datos:
            self._guardar_cache(clave, datos)
        return datos

    def _historico_yahoo(self, simbolo: str, rango: str) -> dict | None:
        bruto = self._get(f"{BASE_YAHOO_CHART}/{simbolo}",
                          {"range": rango, "interval": "1d",
                           "includePrePost": "false", "events": "div,split"})
        try:
            res = bruto["chart"]["result"][0]
            marcas = res["timestamp"]
            cierres = res["indicators"]["quote"][0]["close"]
            volumenes = res["indicators"]["quote"][0].get("volume") or []
            # el cierre ajustado tiene en cuenta dividendos y splits: es el bueno
            ajustados = (res["indicators"].get("adjclose") or [{}])[0].get("adjclose")
        except (TypeError, KeyError, IndexError):
            return None

        serie = ajustados if ajustados and len(ajustados) == len(marcas) else cierres
        fechas, precios, vols = [], [], []
        for i, (t, p) in enumerate(zip(marcas, serie)):
            if p is None:
                continue
            fechas.append(int(t) * 1000)
            precios.append(float(p))
            vols.append(float(volumenes[i]) if i < len(volumenes) and volumenes[i] else 0.0)

        if len(precios) < 30:
            return None

        meta = res.get("meta") or {}
        return {
            "simbolo": simbolo,
            "fechas": fechas,
            "precios": precios,
            "volumenes": vols,
            "divisa": meta.get("currency"),
            "bolsa": meta.get("fullExchangeName") or meta.get("exchangeName"),
            "nombre": meta.get("longName") or meta.get("shortName") or simbolo,
            "tipo": meta.get("instrumentType"),
            "cierre_anterior": meta.get("chartPreviousClose"),
            "fuente": "Yahoo Finance",
        }

    def _historico_stooq(self, simbolo: str) -> dict | None:
        """Plan B. Stooq usa su propia nomenclatura: AAPL -> aapl.us"""
        s = simbolo.lower()
        if "." not in s:
            s = f"{s}.us"
        else:
            base, sufijo = s.rsplit(".", 1)
            s = f"{base}.{ {'de':'de','l':'uk','mc':'es','pa':'fr','as':'nl','mi':'it'}.get(sufijo, sufijo) }"

        crudo = self._get(BASE_STOOQ, {"s": s, "i": "d"}, texto=True)
        if not crudo or crudo.strip().lower().startswith("no data"):
            return None

        fechas, precios, vols = [], [], []
        try:
            for fila in csv.DictReader(io.StringIO(crudo)):
                cierre = fila.get("Close")
                if not cierre:
                    continue
                dt = datetime.strptime(fila["Date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                fechas.append(int(dt.timestamp() * 1000))
                precios.append(float(cierre))
                vols.append(float(fila.get("Volume") or 0))
        except (csv.Error, ValueError, KeyError):
            return None

        if len(precios) < 30:
            return None
        return {
            "simbolo": simbolo, "fechas": fechas[-750:], "precios": precios[-750:],
            "volumenes": vols[-750:], "divisa": None, "bolsa": None,
            "nombre": simbolo, "tipo": None, "cierre_anterior": None,
            "fuente": "Stooq",
        }

    # -- ficha fundamental --------------------------------------------------

    def ficha(self, simbolo: str) -> dict:
        """
        Datos fundamentales. Para acciones: PER, dividendo, sector.
        Para ETFs: TER, patrimonio, índice replicado.

        Si Yahoo bloquea este endpoint (pasa a veces), devuelve un diccionario
        vacío y el informe simplemente no muestra esos campos.
        """
        clave = f"ficha:{simbolo}"
        cacheado = self._leer_cache(clave)
        if cacheado is not None:
            return cacheado

        modulos = ("summaryDetail,defaultKeyStatistics,price,assetProfile,"
                   "fundProfile,topHoldings")
        bruto = self._get(f"{BASE_YAHOO_SUMMARY}/{simbolo}",
                          {"modules": modulos, "crumb": self._crumb or ""})

        ficha: dict = {}
        try:
            r = bruto["quoteSummary"]["result"][0]
        except (TypeError, KeyError, IndexError):
            self._guardar_cache(clave, ficha)
            return ficha

        def val(dic, *camino):
            actual = dic
            for paso in camino:
                if not isinstance(actual, dict):
                    return None
                actual = actual.get(paso)
            if isinstance(actual, dict):
                return actual.get("raw")
            return actual

        sd, dks = r.get("summaryDetail") or {}, r.get("defaultKeyStatistics") or {}
        precio, perfil = r.get("price") or {}, r.get("assetProfile") or {}
        fondo, holdings = r.get("fundProfile") or {}, r.get("topHoldings") or {}

        ficha = {
            "nombre": val(precio, "longName") or val(precio, "shortName"),
            "tipo": val(precio, "quoteType"),
            "divisa": val(precio, "currency"),
            "capitalizacion": val(precio, "marketCap") or val(sd, "marketCap"),
            "per": val(sd, "trailingPE"),
            "per_futuro": val(sd, "forwardPE"),
            "dividendo_pct": (val(sd, "dividendYield") or val(sd, "yield") or 0) ,
            "beta": val(dks, "beta") or val(sd, "beta3Year"),
            "max_52s": val(sd, "fiftyTwoWeekHigh"),
            "min_52s": val(sd, "fiftyTwoWeekLow"),
            "sector": perfil.get("sector"),
            "industria": perfil.get("industry"),
            "pais": perfil.get("country"),
            "empleados": perfil.get("fullTimeEmployees"),
            "patrimonio": val(dks, "totalAssets"),
            "ter": (val(fondo, "feesExpensesInvestment", "annualReportExpenseRatio")
                    or val(dks, "annualReportExpenseRatio")),
            "familia": fondo.get("family"),
            "categoria": fondo.get("categoryName") or val(dks, "category"),
            "top_holdings": [
                {"nombre": h.get("holdingName"), "peso": (h.get("holdingPercent") or {}).get("raw")}
                for h in (holdings.get("holdings") or [])[:10]
            ],
            "sectores": {
                list(s.keys())[0]: list(s.values())[0]
                for s in (holdings.get("sectorWeightings") or []) if s
            },
        }
        # Yahoo devuelve el dividendo unas veces en tanto por uno y otras en %
        d = ficha["dividendo_pct"]
        if d and d < 1:
            ficha["dividendo_pct"] = d * 100

        self._guardar_cache(clave, ficha)
        return ficha

    # -- buscador de símbolos ----------------------------------------------

    def buscar(self, texto: str, limite: int = 12) -> list[dict]:
        """Resuelve un nombre ('iShares Core S&P 500') a símbolos de Yahoo."""
        bruto = self._get(BASE_YAHOO_BUSCAR,
                          {"q": texto, "quotesCount": limite, "newsCount": 0})
        salida = []
        for q in (bruto or {}).get("quotes", []):
            if not q.get("symbol"):
                continue
            salida.append({
                "simbolo": q.get("symbol"),
                "nombre": q.get("longname") or q.get("shortname") or "",
                "tipo": q.get("quoteType"),
                "bolsa": q.get("exchDisp") or q.get("exchange"),
            })
        return salida


# ---------------------------------------------------------------------------
# Modo demo: series sintéticas con el comportamiento típico de cada activo
# ---------------------------------------------------------------------------

_PLANTILLA_BOLSA = [
    # simbolo, nombre, tipo, precio, divisa, deriva anual, volatilidad, extras
    ("^GSPC", "S&P 500", "INDEX", 5480.0, "USD", 0.11, 0.15, {}),
    ("^IXIC", "NASDAQ Composite", "INDEX", 17820.0, "USD", 0.14, 0.20, {}),
    ("^IBEX", "IBEX 35", "INDEX", 11240.0, "EUR", 0.07, 0.16, {}),
    ("^STOXX50E", "EURO STOXX 50", "INDEX", 4910.0, "EUR", 0.08, 0.16, {}),
    ("^VIX", "CBOE Volatility Index", "INDEX", 14.8, "USD", 0.0, 0.85, {}),
    ("EURUSD=X", "EUR/USD", "CURRENCY", 1.0842, "USD", 0.0, 0.08, {}),
    ("CSPX.L", "iShares Core S&P 500 UCITS ETF USD (Acc)", "ETF", 585.40, "USD", 0.11, 0.15,
     {"ter": 0.0007, "patrimonio": 98_000_000_000, "categoria": "Large Blend",
      "familia": "iShares"}),
    ("IBCF.DE", "iShares Core S&P 500 UCITS ETF EUR Hedged (Acc)", "ETF", 92.15, "EUR", 0.09, 0.14,
     {"ter": 0.0020, "patrimonio": 3_400_000_000, "categoria": "Large Blend (cubierto)",
      "familia": "iShares"}),
    ("VWCE.DE", "Vanguard FTSE All-World UCITS ETF (Acc)", "ETF", 128.70, "EUR", 0.10, 0.14,
     {"ter": 0.0022, "patrimonio": 22_000_000_000, "categoria": "Global Large Blend",
      "familia": "Vanguard"}),
    ("EXS1.DE", "iShares Core DAX UCITS ETF", "ETF", 158.30, "EUR", 0.08, 0.17,
     {"ter": 0.0016, "patrimonio": 6_100_000_000, "categoria": "Alemania", "familia": "iShares"}),
    ("IUIT.L", "iShares S&P 500 Information Technology Sector UCITS ETF", "ETF", 24.85, "USD", 0.17, 0.24,
     {"ter": 0.0015, "patrimonio": 8_900_000_000, "categoria": "Tecnología", "familia": "iShares"}),
    ("AAPL", "Apple Inc.", "EQUITY", 224.30, "USD", 0.13, 0.26,
     {"per": 34.2, "dividendo": 0.44, "sector": "Technology"}),
    ("MSFT", "Microsoft Corporation", "EQUITY", 421.80, "USD", 0.15, 0.24,
     {"per": 36.8, "dividendo": 0.71, "sector": "Technology"}),
    ("NVDA", "NVIDIA Corporation", "EQUITY", 118.40, "USD", 0.35, 0.48,
     {"per": 58.1, "dividendo": 0.03, "sector": "Technology"}),
    ("TEF.MC", "Telefónica, S.A.", "EQUITY", 4.32, "EUR", 0.02, 0.22,
     {"per": 12.4, "dividendo": 6.9, "sector": "Communication Services"}),
    ("ITX.MC", "Industria de Diseño Textil, S.A.", "EQUITY", 47.86, "EUR", 0.12, 0.21,
     {"per": 27.5, "dividendo": 3.1, "sector": "Consumer Cyclical"}),
    ("SAN.MC", "Banco Santander, S.A.", "EQUITY", 4.51, "EUR", 0.09, 0.25,
     {"per": 6.2, "dividendo": 4.4, "sector": "Financial Services"}),
]


class FuenteBolsaDemo:
    """Genera series realistas sin tocar internet. Misma interfaz que ClienteBolsa."""

    def __init__(self, semilla: int = 20260821, verbose: bool = True):
        self.rng = random.Random(semilla + 7)
        self.verbose = verbose
        self.peticiones_hechas = 0
        self.fallos: list[str] = []
        self._series: dict[str, dict] = {}
        self._construir()

    def _construir(self) -> None:
        for fila in list(_PLANTILLA_BOLSA):
            self._construir_una(fila)

    def _construir_una(self, fila: tuple) -> None:
        dias_bursatiles = 504  # unos dos años
        hoy = datetime.now(timezone.utc)
        sim, _n, _t, precio_fin, _d, deriva, vol, _e = fila

        precios = [precio_fin]
        for _ in range(dias_bursatiles - 1):
            paso = deriva / 252.0
            choque = self.rng.gauss(0, vol / math.sqrt(252))
            precios.insert(0, max(precios[0] / math.exp(paso + choque), precio_fin * 0.05))

        fechas, cursor = [], hoy
        while len(fechas) < dias_bursatiles:
            if cursor.weekday() < 5:  # sin fines de semana
                fechas.append(int(cursor.timestamp() * 1000))
            cursor -= timedelta(days=1)
        fechas.reverse()

        base = 40_000_000 if precio_fin > 100 else 12_000_000
        vols = [max(base * (1 + self.rng.gauss(0, 0.4)), base * 0.15) for _ in precios]
        vols[-1] *= self.rng.choice([0.9, 1.0, 1.1, 2.3])

        self._series[sim] = {"fechas": fechas, "precios": precios, "volumenes": vols}

    def _inventar(self, simbolo: str) -> tuple:
        """
        Genera una entrada plausible para un símbolo que no está en la plantilla.

        Sin esto, el modo demo solo funcionaría con los símbolos de ejemplo, y
        en cuanto pusieras tus propios activos en cartera.csv la cartera saldría
        vacía. Los valores salen del propio nombre del símbolo, así que son
        distintos entre activos pero siempre los mismos para el mismo activo.
        """
        semilla = sum(ord(c) * (i + 3) for i, c in enumerate(simbolo))
        rng = random.Random(semilla)
        es_indice = simbolo.startswith("^")
        es_etf = len(simbolo.split(".")[0]) == 4 and "." in simbolo

        if es_indice:
            tipo, precio, vol, deriva = "INDEX", rng.uniform(3_000, 18_000), 0.17, 0.08
        elif es_etf:
            tipo, precio, vol, deriva = "ETF", rng.uniform(20, 600), 0.16, 0.10
        else:
            tipo, precio, vol, deriva = "EQUITY", rng.uniform(5, 400), 0.30, 0.11

        divisa = "EUR" if simbolo.split(".")[-1] in ("DE", "MC", "PA", "AS", "MI") else "USD"
        extras = ({"ter": rng.choice([0.0007, 0.0012, 0.0020]),
                   "patrimonio": rng.randint(200, 40_000) * 1_000_000,
                   "categoria": "Renta variable", "familia": "—"}
                  if tipo == "ETF" else
                  {"per": round(rng.uniform(8, 42), 1),
                   "dividendo": round(rng.uniform(0, 5), 2),
                   "sector": rng.choice(["Technology", "Utilities", "Consumer Cyclical",
                                         "Financial Services", "Healthcare"])})
        return (simbolo, simbolo, tipo, round(precio, 2), divisa, deriva, vol, extras)

    def _asegurar(self, simbolo: str) -> tuple | None:
        """Devuelve la fila de plantilla del símbolo, inventándola si hace falta."""
        fila = next((x for x in _PLANTILLA_BOLSA if x[0] == simbolo), None)
        if fila is None:
            fila = self._inventar(simbolo)
            _PLANTILLA_BOLSA.append(fila)
        if simbolo not in self._series:
            self._construir_una(fila)
        return fila

    def historico(self, simbolo: str, rango: str = "2y") -> dict | None:
        fila = self._asegurar(simbolo)
        s = self._series.get(simbolo)
        if not s or not fila:
            return None
        return {
            "simbolo": simbolo,
            "fechas": s["fechas"], "precios": s["precios"], "volumenes": s["volumenes"],
            "divisa": fila[4], "bolsa": "Demo", "nombre": fila[1],
            "tipo": fila[2], "cierre_anterior": s["precios"][-2],
            "fuente": "Datos de demostración",
        }

    def ficha(self, simbolo: str) -> dict:
        fila = self._asegurar(simbolo)
        if not fila:
            return {}
        sim, nombre, tipo, _p, divisa, _d, _v, extras = fila
        serie = self._series[sim]["precios"]
        base = {
            "nombre": nombre, "tipo": tipo, "divisa": divisa,
            "max_52s": max(serie[-252:]), "min_52s": min(serie[-252:]),
            "top_holdings": [], "sectores": {},
        }
        if tipo == "ETF":
            base.update({
                "ter": extras.get("ter"), "patrimonio": extras.get("patrimonio"),
                "categoria": extras.get("categoria"), "familia": extras.get("familia"),
                "top_holdings": [
                    {"nombre": n, "peso": p} for n, p in
                    [("Apple Inc", .071), ("Microsoft Corp", .068), ("NVIDIA Corp", .062),
                     ("Amazon.com Inc", .037), ("Meta Platforms", .024)]
                ],
                "sectores": {"technology": .32, "financial_services": .13,
                             "healthcare": .12, "consumer_cyclical": .10},
            })
        elif tipo == "EQUITY":
            base.update({
                "per": extras.get("per"), "per_futuro": (extras.get("per") or 20) * 0.88,
                "dividendo_pct": extras.get("dividendo"), "sector": extras.get("sector"),
                "capitalizacion": self.rng.randint(50, 3200) * 1_000_000_000,
                "beta": round(self.rng.uniform(0.6, 1.6), 2),
                "pais": "United States" if "." not in sim else "Spain",
            })
        return base

    # Para que el modo demo enseñe el mismo flujo que la ejecución real:
    # escribes un ISIN y se traduce a un símbolo.
    _ISINS_DEMO = {
        "IE00B5BMR087": ("SXR8.DE", "iShares Core S&P 500 UCITS ETF (Acc)", "ETF"),
        "IE00B3ZW0K18": ("IBCF.DE", "iShares S&P 500 EUR Hedged UCITS ETF (Acc)", "ETF"),
        "IE00BK5BQT80": ("VWCE.DE", "Vanguard FTSE All-World UCITS ETF (Acc)", "ETF"),
        "US21037T1097": ("CEG", "Constellation Energy Corporation", "EQUITY"),
        "ES0105630315": ("PUIG.MC", "PUIG Brands, S.A.", "EQUITY"),
    }

    def buscar(self, texto: str, limite: int = 12) -> list[dict]:
        consulta = (texto or "").strip()
        clave = consulta.upper()

        if clave in self._ISINS_DEMO:
            simbolo, nombre, tipo = self._ISINS_DEMO[clave]
            return [{"simbolo": simbolo, "nombre": nombre, "tipo": tipo, "bolsa": "Demo"}]

        # Un ISIN que no conocemos: nos inventamos un símbolo estable a partir
        # de él, para que el flujo se pueda probar igualmente
        if len(clave) == 12 and clave[:2].isalpha() and clave[2:].isalnum():
            rng = random.Random(sum(ord(c) for c in clave))
            letras = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4))
            sufijo = ".DE" if clave.startswith(("IE", "DE", "LU")) else (
                ".MC" if clave.startswith("ES") else "")
            return [{"simbolo": f"{letras}{sufijo}",
                     "nombre": f"Activo de demostración ({clave})",
                     "tipo": "ETF" if sufijo else "EQUITY", "bolsa": "Demo"}]

        t = consulta.lower()
        return [
            {"simbolo": x[0], "nombre": x[1], "tipo": x[2], "bolsa": "Demo"}
            for x in _PLANTILLA_BOLSA
            if t in x[1].lower() or t in x[0].lower()
        ][:limite]


def obtener_fuente_bolsa(demo: bool = False, usar_cache: bool = True, verbose: bool = True):
    if demo:
        return FuenteBolsaDemo(verbose=verbose)
    return ClienteBolsa(usar_cache=usar_cache, verbose=verbose)
