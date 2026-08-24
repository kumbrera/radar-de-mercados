"""
Configuración de Cripto Radar.

Este es el ÚNICO fichero que necesitas tocar para personalizar el sistema.
Todo lo demás funciona solo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = RAIZ / "data"
DIR_SALIDAS = RAIZ / "salidas"
FICHERO_HISTORICO = DIR_DATOS / "historico.sqlite3"
DIR_CACHE = DIR_DATOS / "cache"

for _d in (DIR_DATOS, DIR_SALIDAS, DIR_CACHE):
    _d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Moneda y mercado
# ---------------------------------------------------------------------------

MONEDA = "eur"          # eur | usd
SIMBOLO_MONEDA = "€"


# ---------------------------------------------------------------------------
# Tu watchlist: las criptos que sigues de cerca.
# Se analizan en profundidad (indicadores técnicos, señales, historial).
# Usa los IDs de CoinGecko (los ves en la URL: coingecko.com/en/coins/<id>).
# Máximo recomendado: 12-15 (el plan gratuito tiene límite de peticiones).
# ---------------------------------------------------------------------------

WATCHLIST = [
    "bitcoin",
    "ethereum",
    "solana",
    "chainlink",
    "arbitrum",
    "render-token",
    "bittensor",
    "sui",
    "aave",
    "hyperliquid",
]


# ---------------------------------------------------------------------------
# Descubrimiento de proyectos: de dónde salen las ideas nuevas
# ---------------------------------------------------------------------------

# Cuántas monedas del top por capitalización se escanean buscando candidatos
TOP_A_ESCANEAR = 250

# Rango de capitalización donde buscamos "proyectos interesantes".
# Por debajo del mínimo = demasiado pequeño / ilíquido / riesgo de manipulación.
# Por encima del máximo = ya es gigante, poco recorrido explosivo.
MCAP_MIN = 40_000_000       # 40 M
MCAP_MAX = 4_000_000_000    # 4.000 M

# Volumen diario mínimo para que se pueda entrar y salir sin destrozar el precio
VOLUMEN_MIN_24H = 3_000_000

# Cuántos proyectos muestra el informe
MAX_PROYECTOS_INFORME = 12


# ---------------------------------------------------------------------------
# Umbrales de las señales técnicas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Umbrales:
    rsi_sobreventa: float = 30.0        # por debajo: "sobrevendido"
    rsi_sobrecompra: float = 70.0       # por encima: "sobrecomprado"
    rsi_zona_baja: float = 40.0         # zona de interés moderado
    rsi_zona_alta: float = 60.0

    caida_fuerte_24h: float = -7.0      # % que consideramos caída digna de mirar
    subida_fuerte_24h: float = 7.0

    # Volumen de hoy frente a la media de 30 días. 2.0 = el doble de lo normal.
    volumen_anomalo: float = 2.0

    # Distancia mínima desde el máximo histórico para considerarlo "de rebajas"
    drawdown_interesante: float = -50.0

    # Volatilidad anualizada por encima de la cual avisamos de que va a doler
    volatilidad_alta: float = 90.0


UMBRALES = Umbrales()

# La bolsa se mueve MUCHÍSIMO menos que las criptos. Aplicarle los mismos
# umbrales llenaría el informe de alertas inútiles o no daría ninguna.
# Referencia: el S&P 500 tiene una volatilidad del 12-20% anual; Bitcoin, del
# 40-70%. Una caída del 3% en un índice es un titular de portada; en cripto es
# un martes cualquiera.
UMBRALES_BOLSA = Umbrales(
    rsi_sobreventa=35.0,
    rsi_sobrecompra=68.0,
    caida_fuerte_24h=-2.5,
    subida_fuerte_24h=2.5,
    volumen_anomalo=1.8,
    drawdown_interesante=-20.0,
    volatilidad_alta=30.0,
)


# ---------------------------------------------------------------------------
# Pesos del scoring de proyectos (deben sumar 100)
# Puedes moverlos si te importa más una cosa que otra.
# ---------------------------------------------------------------------------

PESOS_SCORING = {
    "liquidez": 18,        # ¿se puede entrar y salir de verdad?
    "desarrollo": 20,      # ¿hay gente escribiendo código?
    "comunidad": 12,       # ¿hay alguien ahí fuera?
    "momento": 15,         # ¿el mercado le está prestando atención?
    "valoracion": 15,      # ¿está caro respecto a su propia historia?
    "tokenomics": 20,      # ¿te van a diluir con desbloqueos futuros?
}


# ---------------------------------------------------------------------------
# Red flags: cosas que restan puntos directamente
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RedFlags:
    # Volumen/capitalización absurdamente alto suele oler a wash trading
    ratio_volumen_mcap_sospechoso: float = 1.5
    # Menos de este % del supply en circulación = te esperan desbloqueos gordos
    circulante_minimo_pct: float = 25.0
    # Subida en 30 días por encima de la cual el riesgo de comprar el techo es real
    pump_30d_peligroso: float = 150.0
    # Sin commits en tanto tiempo = proyecto potencialmente abandonado
    dias_sin_commits_alerta: int = 60


RED_FLAGS = RedFlags()


# ===========================================================================
# BOLSA: índices, ETFs y acciones
# ===========================================================================

# Los símbolos son los de Yahoo Finance. Si no sabes el de un ETF, búscalo:
#     python3 radar.py --buscar "iShares Core S&P 500"
#
# Pista sobre los sufijos: .MC = Madrid, .DE = Xetra (Alemania), .L = Londres,
# .AS = Ámsterdam, .PA = París, .MI = Milán. Sin sufijo = Estados Unidos.

# Índices de referencia: el "cómo va el mundo" del informe.
INDICES = [
    ("^GSPC",     "S&P 500"),
    ("^IXIC",     "NASDAQ"),
    ("^IBEX",     "IBEX 35"),
    ("^STOXX50E", "EURO STOXX 50"),
    ("^VIX",      "VIX (miedo)"),
    ("EURUSD=X",  "EUR/USD"),
]

# Tus ETFs y fondos. Se analizan en profundidad.
#
# AVISO: estos símbolos son un punto de partida razonable, pero NO están
# verificados uno a uno. Los símbolos de ETF europeos cambian según la bolsa y
# a veces se renombran. Antes de fiarte, comprueba cada uno con:
#     python3 radar.py --buscar "iShares Core S&P 500"
# Si uno falla, el informe te lo dirá por pantalla y seguirá con el resto.
# NO hace falta repetir aquí lo que ya tienes en cartera.csv: tus posiciones se
# añaden solas. Esta lista es para lo que quieres VIGILAR sin tenerlo todavía.
WATCHLIST_ETFS = [
    "CSPX.L",    # iShares Core S&P 500 USD (Acc), para comparar comisiones
    "VWCE.DE",   # Vanguard FTSE All-World (Acc), la alternativa global
]

WATCHLIST_ACCIONES = [
    # Ejemplos: "AAPL", "ITX.MC", "SAN.MC"
]


# ---------------------------------------------------------------------------
# TU CARTERA
#
# Apunta aquí lo que compras y el sistema te calculará ganancias, pérdidas y
# cuánto te has desviado de tu reparto objetivo.
#
# Cada posición: (identificador, tipo, unidades, precio_medio_de_compra)
#   tipo: "cripto" | "etf" | "accion"
#   Para cripto el identificador es el ID de CoinGecko ("bitcoin").
#   Para bolsa, el símbolo de Yahoo ("CSPX.L").
#
# Si aún no has comprado nada, déjalo vacío: POSICIONES = []
# El informe seguirá funcionando y te mostrará el plan objetivo.
# ---------------------------------------------------------------------------

# >>> NO EDITES ESTO. Tus posiciones van en el fichero cartera.csv <<<
#
# Se lee automáticamente al arrancar. Está en la raíz del proyecto y puedes
# editarlo desde el móvil sin tocar código.
#
# (Si prefieres escribirlas aquí a mano, puedes: basta con poner las tuplas
#  en esta lista y borrar o vaciar cartera.csv. Lo que haya en el CSV manda.)

FICHERO_CARTERA = RAIZ / "cartera.csv"

POSICIONES: list[tuple] = []
AVISOS_CARTERA: list[str] = []

try:
    from .cartera_csv import ErrorCartera, leer as _leer_cartera

    POSICIONES, AVISOS_CARTERA = _leer_cartera(FICHERO_CARTERA)
except ErrorCartera as _e:
    AVISOS_CARTERA = [str(_e)]
except Exception as _e:  # noqa: BLE001
    AVISOS_CARTERA = [f"No se ha podido leer cartera.csv: {_e}"]

# Tu reparto objetivo, en porcentaje. Debe sumar 100.
# Este es el que acordamos: 70% renta variable, 15% cripto, 15% acciones sueltas.
REPARTO_OBJETIVO = {
    "etf": 70,
    "cripto": 15,
    "accion": 15,
}

# Cuánto te desvías del objetivo antes de que el sistema te avise.
# Por debajo de esto, rebalancear cuesta más en comisiones e impuestos de lo
# que aporta.
DESVIACION_AVISO_PCT = 5.0

# Aportación periódica (DCA). Ponlo a 0 si no aportas de forma regular.
APORTACION_MENSUAL = 100.0


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

# CoinGecko funciona sin API key (plan gratuito, ~10-30 peticiones/minuto).
# Si algún día te haces una key gratuita "Demo", ponla en la variable de
# entorno COINGECKO_API_KEY y el sistema la usará automáticamente.
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "").strip()

BASE_COINGECKO = "https://api.coingecko.com/api/v3"
BASE_FEAR_GREED = "https://api.alternative.me/fng/"

# Segundos de espera entre peticiones para no chocar con el rate limit
PAUSA_ENTRE_PETICIONES = 2.5

# Yahoo Finance aguanta bastante más ritmo que CoinGecko
PAUSA_BOLSA = 0.7

# ---------------------------------------------------------------------------
# PRESUPUESTO DE TIEMPO
#
# Sin esto, un mal día de rate limits puede dejar el informe colgado 45 minutos:
# 32 peticiones x 3 reintentos x esperas crecientes se multiplican deprisa.
#
# Con un presupuesto, cuando se agota el tiempo el sistema deja de pedir cosas
# nuevas y genera el informe con lo que haya conseguido. Prefiero un informe
# incompleto que te avisa de lo que falta, a uno perfecto que no llega nunca.
# ---------------------------------------------------------------------------

PRESUPUESTO_CRIPTO_SEGUNDOS = 8 * 60
PRESUPUESTO_BOLSA_SEGUNDOS = 5 * 60

# Cuántos rechazos seguidos hacen falta para dar por saturada una fuente y
# dejar de insistir durante esta ejecución.
RECHAZOS_SEGUIDOS_PARA_RENDIRSE = 4

# Cuántos segundos vale una respuesta cacheada (evita repetir llamadas si
# ejecutas el script varias veces seguidas mientras trasteas)
TTL_CACHE_SEGUNDOS = 60 * 30  # 30 minutos

TIMEOUT = 30
REINTENTOS = 3


# ---------------------------------------------------------------------------
# Informe
# ---------------------------------------------------------------------------

@dataclass
class OpcionesInforme:
    titulo: str = "Cripto Radar"
    subtitulo: str = "Tu informe diario de mercado"
    incluir_glosario: bool = True
    incluir_disclaimer: bool = True
    abrir_navegador: bool = False
    idioma: str = "es"


INFORME = OpcionesInforme()
