"""
Indicadores técnicos, en Python puro (sin pandas ni numpy).

Todas las funciones reciben una lista de precios de cierre ordenada de
MÁS ANTIGUO a MÁS RECIENTE, y devuelven None si no hay datos suficientes.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Medias
# ---------------------------------------------------------------------------

def sma(precios: Sequence[float], periodo: int) -> float | None:
    """Media móvil simple: el precio medio de los últimos N días."""
    if periodo <= 0 or len(precios) < periodo:
        return None
    return sum(precios[-periodo:]) / periodo


def sma_serie(precios: Sequence[float], periodo: int) -> list[float | None]:
    """La SMA calculada en cada punto de la serie (para dibujarla)."""
    if periodo <= 0:
        return [None] * len(precios)
    salida: list[float | None] = []
    acumulado = 0.0
    for i, p in enumerate(precios):
        acumulado += p
        if i >= periodo:
            acumulado -= precios[i - periodo]
        salida.append(acumulado / periodo if i >= periodo - 1 else None)
    return salida


def ema_serie(precios: Sequence[float], periodo: int) -> list[float | None]:
    """Media móvil exponencial: da más peso a los días recientes."""
    if periodo <= 0 or len(precios) < periodo:
        return [None] * len(precios)
    k = 2.0 / (periodo + 1.0)
    salida: list[float | None] = [None] * (periodo - 1)
    actual = sum(precios[:periodo]) / periodo
    salida.append(actual)
    for p in precios[periodo:]:
        actual = p * k + actual * (1 - k)
        salida.append(actual)
    return salida


def ema(precios: Sequence[float], periodo: int) -> float | None:
    serie = ema_serie(precios, periodo)
    return serie[-1] if serie else None


# ---------------------------------------------------------------------------
# RSI (Wilder, el estándar)
# ---------------------------------------------------------------------------

def rsi(precios: Sequence[float], periodo: int = 14) -> float | None:
    """
    RSI de Wilder. Va de 0 a 100.

    Mide la fuerza de las subidas frente a las bajadas recientes:
      < 30  -> el activo ha caído mucho y rápido (sobrevendido)
      > 70  -> ha subido mucho y rápido (sobrecomprado)

    Ojo: NO es una señal de compra ni de venta por sí sola. En una tendencia
    alcista fuerte el RSI puede quedarse semanas por encima de 70.
    """
    serie = rsi_serie(precios, periodo)
    return serie[-1] if serie else None


def rsi_serie(precios: Sequence[float], periodo: int = 14) -> list[float | None]:
    n = len(precios)
    if n < periodo + 1:
        return [None] * n

    ganancias: list[float] = []
    perdidas: list[float] = []
    for i in range(1, n):
        cambio = precios[i] - precios[i - 1]
        ganancias.append(max(cambio, 0.0))
        perdidas.append(max(-cambio, 0.0))

    salida: list[float | None] = [None] * n

    media_g = sum(ganancias[:periodo]) / periodo
    media_p = sum(perdidas[:periodo]) / periodo
    salida[periodo] = _rsi_desde_medias(media_g, media_p)

    for i in range(periodo, len(ganancias)):
        media_g = (media_g * (periodo - 1) + ganancias[i]) / periodo
        media_p = (media_p * (periodo - 1) + perdidas[i]) / periodo
        salida[i + 1] = _rsi_desde_medias(media_g, media_p)

    return salida


def _rsi_desde_medias(media_g: float, media_p: float) -> float:
    if media_p == 0:
        return 100.0 if media_g > 0 else 50.0
    rs = media_g / media_p
    return 100.0 - (100.0 / (1.0 + rs))


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def macd(
    precios: Sequence[float],
    rapida: int = 12,
    lenta: int = 26,
    señal: int = 9,
) -> dict | None:
    """
    MACD: compara una media rápida con una lenta.

    Si la línea MACD cruza por encima de su línea de señal, el impulso
    de corto plazo está mejorando. Si cruza por debajo, empeorando.
    """
    if len(precios) < lenta + señal:
        return None

    ema_rapida = ema_serie(precios, rapida)
    ema_lenta = ema_serie(precios, lenta)

    linea: list[float] = []
    for r, l in zip(ema_rapida, ema_lenta):
        if r is None or l is None:
            continue
        linea.append(r - l)

    if len(linea) < señal:
        return None

    linea_señal = ema_serie(linea, señal)
    ultimo_señal = linea_señal[-1]
    if ultimo_señal is None:
        return None

    histograma = linea[-1] - ultimo_señal

    # ¿Ha habido cruce en los últimos 3 días?
    cruce = None
    if len(linea) >= 4 and linea_señal[-4] is not None:
        for atras in (1, 2, 3):
            prev_s = linea_señal[-atras - 1]
            if prev_s is None:
                continue
            antes = linea[-atras - 1] - prev_s
            ahora = linea[-atras] - (linea_señal[-atras] or 0)
            if antes < 0 <= ahora:
                cruce = "alcista"
                break
            if antes > 0 >= ahora:
                cruce = "bajista"
                break

    return {
        "macd": linea[-1],
        "señal": ultimo_señal,
        "histograma": histograma,
        "cruce_reciente": cruce,
    }


# ---------------------------------------------------------------------------
# Volatilidad y riesgo
# ---------------------------------------------------------------------------

def rendimientos_diarios(precios: Sequence[float]) -> list[float]:
    salida = []
    for i in range(1, len(precios)):
        if precios[i - 1] > 0:
            salida.append((precios[i] / precios[i - 1]) - 1.0)
    return salida


def volatilidad_anualizada(precios: Sequence[float], periodo: int = 30) -> float | None:
    """
    Desviación típica de los rendimientos diarios, escalada a un año, en %.

    Traducción: cuánto se mueve esto normalmente.
      < 40%  -> tranquilo (para ser cripto)
      40-80% -> normal en cripto
      > 100% -> vas a ver caídas del 20% en un día sin que pase nada raro
    """
    rends = rendimientos_diarios(precios[-(periodo + 1):])
    if len(rends) < 5:
        return None
    media = sum(rends) / len(rends)
    varianza = sum((r - media) ** 2 for r in rends) / (len(rends) - 1)
    return math.sqrt(varianza) * math.sqrt(365) * 100.0


def maximo_drawdown(precios: Sequence[float]) -> float | None:
    """La peor caída pico-a-valle dentro de la serie, en % (número negativo)."""
    if len(precios) < 2:
        return None
    pico = precios[0]
    peor = 0.0
    for p in precios:
        pico = max(pico, p)
        if pico > 0:
            peor = min(peor, (p / pico - 1.0) * 100.0)
    return peor


def cambio_pct(precios: Sequence[float], dias: int) -> float | None:
    """Variación porcentual de los últimos N días."""
    if len(precios) < dias + 1 or precios[-dias - 1] == 0:
        return None
    return (precios[-1] / precios[-dias - 1] - 1.0) * 100.0


def distancia_a(precio: float | None, referencia: float | None) -> float | None:
    """A qué distancia porcentual está el precio de una referencia (SMA, ATH...)."""
    if precio is None or referencia in (None, 0):
        return None
    return (precio / referencia - 1.0) * 100.0


# ---------------------------------------------------------------------------
# Soportes y resistencias sencillos
# ---------------------------------------------------------------------------

def soporte_resistencia(precios: Sequence[float], ventana: int = 90) -> dict | None:
    """
    Nivel simple: el mínimo y el máximo de los últimos N días.

    No es magia: es literalmente "hasta dónde ha bajado y subido últimamente".
    Sirve como referencia visual, no como profecía.
    """
    trozo = precios[-ventana:]
    if len(trozo) < 10:
        return None
    minimo, maximo = min(trozo), max(trozo)
    actual = trozo[-1]
    rango = maximo - minimo
    posicion = ((actual - minimo) / rango * 100.0) if rango > 0 else 50.0
    return {
        "soporte": minimo,
        "resistencia": maximo,
        "posicion_en_rango_pct": posicion,
    }


# ---------------------------------------------------------------------------
# Paquete completo para una moneda
# ---------------------------------------------------------------------------

def analizar(precios: Sequence[float], volumenes: Sequence[float] | None = None) -> dict:
    """Calcula todos los indicadores de golpe para una serie de precios."""
    precios = [float(p) for p in precios if p is not None]
    actual = precios[-1] if precios else None

    s20 = sma(precios, 20)
    s50 = sma(precios, 50)
    s200 = sma(precios, 200)

    # ¿Cruce de medias en los últimos 5 días? (la "cruz dorada" / "cruz de la muerte")
    cruce_medias = None
    serie20 = sma_serie(precios, 20)
    serie50 = sma_serie(precios, 50)
    for atras in range(1, min(6, len(precios))):
        a20, a50 = serie20[-atras - 1], serie50[-atras - 1]
        b20, b50 = serie20[-atras], serie50[-atras]
        if None in (a20, a50, b20, b50):
            continue
        if a20 <= a50 and b20 > b50:
            cruce_medias = "alcista"
            break
        if a20 >= a50 and b20 < b50:
            cruce_medias = "bajista"
            break

    volumen_relativo = None
    if volumenes:
        vols = [float(v) for v in volumenes if v is not None]
        if len(vols) >= 31:
            media_30 = sum(vols[-31:-1]) / 30
            if media_30 > 0:
                volumen_relativo = vols[-1] / media_30

    return {
        "precio": actual,
        "rsi": rsi(precios, 14),
        "cambio_1d_pct": cambio_pct(precios, 1),
        "sma20": s20,
        "sma50": s50,
        "sma200": s200,
        "dist_sma50_pct": distancia_a(actual, s50),
        "dist_sma200_pct": distancia_a(actual, s200),
        "cruce_medias": cruce_medias,
        "macd": macd(precios),
        "volatilidad_pct": volatilidad_anualizada(precios, 30),
        "max_drawdown_pct": maximo_drawdown(precios),
        "cambio_7d_pct": cambio_pct(precios, 7),
        "cambio_30d_pct": cambio_pct(precios, 30),
        "cambio_90d_pct": cambio_pct(precios, 90),
        "niveles": soporte_resistencia(precios, 90),
        "volumen_relativo": volumen_relativo,
        "serie": precios,
    }


# ---------------------------------------------------------------------------
# Variante para renta variable
# ---------------------------------------------------------------------------

# En bolsa el año tiene ~252 sesiones, no 365 días: los mercados cierran fines
# de semana y festivos. Usar 365 aquí inflaría la volatilidad un 20%.
SESIONES_ANIO = 252


def volatilidad_bolsa(precios: Sequence[float], periodo: int = 30) -> float | None:
    """Igual que volatilidad_anualizada, pero escalada con sesiones bursátiles."""
    rends = rendimientos_diarios(precios[-(periodo + 1):])
    if len(rends) < 5:
        return None
    media = sum(rends) / len(rends)
    varianza = sum((r - media) ** 2 for r in rends) / (len(rends) - 1)
    return math.sqrt(varianza) * math.sqrt(SESIONES_ANIO) * 100.0


def analizar_bolsa(
    precios: Sequence[float],
    volumenes: Sequence[float] | None = None,
    max_52s: float | None = None,
    min_52s: float | None = None,
) -> dict:
    """
    Análisis de un valor de renta variable.

    Diferencias con analizar():
      • la volatilidad se anualiza con 252 sesiones, no 365 días
      • se añade la distancia al máximo y mínimo de 52 semanas, que es la
        referencia estándar en bolsa (en cripto se usa el máximo histórico)
      • los cambios se miden en sesiones, no en días naturales
    """
    datos = analizar(precios, volumenes)
    precios = [float(p) for p in precios if p is not None]
    actual = datos["precio"]

    # Si no nos dan los máximos de 52 semanas, los sacamos de la serie
    ventana = precios[-SESIONES_ANIO:] if len(precios) >= 60 else precios
    if max_52s is None and ventana:
        max_52s = max(ventana)
    if min_52s is None and ventana:
        min_52s = min(ventana)

    datos.update({
        "volatilidad_pct": volatilidad_bolsa(precios, 30),
        "volatilidad_1a_pct": volatilidad_bolsa(precios, SESIONES_ANIO),
        "max_52s": max_52s,
        "min_52s": min_52s,
        "dist_max52s_pct": distancia_a(actual, max_52s),
        "dist_min52s_pct": distancia_a(actual, min_52s),
        "cambio_1s_pct": cambio_pct(precios, 5),      # 5 sesiones = 1 semana
        "cambio_1m_pct": cambio_pct(precios, 21),     # 21 sesiones = 1 mes
        "cambio_1a_pct": cambio_pct(precios, SESIONES_ANIO),
        "rentabilidad_anualizada_pct": rentabilidad_anualizada(precios),
    })
    return datos


def rentabilidad_anualizada(precios: Sequence[float]) -> float | None:
    """
    Rentabilidad media anual compuesta (CAGR) de toda la serie disponible.

    Es la cifra honesta para comparar activos: convertir «+62% en dos años y
    medio» en «cuánto ha rentado de media cada año».
    """
    if len(precios) < 60 or precios[0] <= 0:
        return None
    anios = len(precios) / SESIONES_ANIO
    if anios < 0.5:
        return None
    return ((precios[-1] / precios[0]) ** (1 / anios) - 1) * 100.0
