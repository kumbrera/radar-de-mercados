#!/usr/bin/env python3
"""
Comprobaciones de los indicadores.

El RSI se valida contra la serie original de J. Welles Wilder ("New Concepts in
Technical Trading Systems", 1978), que es la referencia canónica que usan
TradingView, Investing.com y el resto. Si estos números cuadran, el resto de
plataformas te darán el mismo RSI que este sistema.

    python3 test_indicadores.py
"""

from __future__ import annotations

import sys

from radar import indicators as ind

FALLOS: list[str] = []


def comprobar(nombre: str, obtenido, esperado, tolerancia=0.0):
    if esperado is None:
        ok = obtenido is None
    elif obtenido is None:
        ok = False
    else:
        ok = abs(obtenido - esperado) <= tolerancia
    marca = "OK  " if ok else "FALLO"
    valor = "None" if obtenido is None else f"{obtenido:.4f}"
    esp = "None" if esperado is None else f"{esperado:.4f}"
    print(f"  [{marca}] {nombre}: obtenido={valor} esperado={esp}")
    if not ok:
        FALLOS.append(nombre)


# ---------------------------------------------------------------------------
print("\nRSI — serie de referencia de Wilder (1978)")
# ---------------------------------------------------------------------------
WILDER = [
    44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
    45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64,
    46.21, 46.25, 45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57,
    43.42, 42.66, 43.13,
]
# Valores RSI-14 que StockCharts publica para esta misma serie. Su tabla va a
# dos decimales y arrastra redondeos intermedios, de ahí la tolerancia de 0,1.
PUBLICADOS_STOCKCHARTS = [
    70.53, 66.32, 66.55, 69.41, 66.36, 57.97, 62.93, 63.26, 56.06, 62.38,
    54.71, 50.42, 39.99, 41.46, 41.87, 45.46, 37.30, 33.08, 37.77,
]

serie = ind.rsi_serie(WILDER, 14)
for k, idx in enumerate(range(14, len(WILDER))):
    comprobar(f"RSI índice {idx} vs valor publicado", serie[idx],
              PUBLICADOS_STOCKCHARTS[k], 0.1)
comprobar("RSI con datos insuficientes devuelve None", ind.rsi([1, 2, 3], 14), None)

# ---------------------------------------------------------------------------
print("\nCasos límite del RSI")
# ---------------------------------------------------------------------------
solo_sube = [100 + i for i in range(40)]
comprobar("Serie que solo sube -> RSI 100", ind.rsi(solo_sube), 100.0, 0.001)
solo_baja = [100 - i for i in range(40)]
comprobar("Serie que solo baja -> RSI 0", ind.rsi(solo_baja), 0.0, 0.001)

# ---------------------------------------------------------------------------
print("\nMedias móviles")
# ---------------------------------------------------------------------------
comprobar("SMA 5 de 1..10", ind.sma(list(range(1, 11)), 5), 8.0, 0.0001)
comprobar("SMA con periodo mayor que la serie", ind.sma([1, 2, 3], 10), None)

s = ind.sma_serie([2, 4, 6, 8, 10], 3)
comprobar("SMA serie: primer valor calculable", s[2], 4.0, 0.0001)
comprobar("SMA serie: último valor", s[4], 8.0, 0.0001)
comprobar("SMA serie: hueco inicial es None", None if s[0] is None else 1, None)

# EMA: comprobación manual. Con periodo 3, k = 0.5
# semilla = media(1,2,3) = 2 ; luego 4*0.5 + 2*0.5 = 3 ; luego 5*0.5 + 3*0.5 = 4
comprobar("EMA 3 de [1,2,3,4,5]", ind.ema([1, 2, 3, 4, 5], 3), 4.0, 0.0001)

# ---------------------------------------------------------------------------
print("\nCambios porcentuales y drawdown")
# ---------------------------------------------------------------------------
comprobar("Cambio de 100 a 110 en 1 día", ind.cambio_pct([100, 110], 1), 10.0, 0.0001)
comprobar("Cambio a 7 días", ind.cambio_pct([100] + [0] * 6 + [50], 7), -50.0, 0.0001)
comprobar("Drawdown de 100->50->75", ind.maximo_drawdown([100, 50, 75]), -50.0, 0.0001)
comprobar("Drawdown de serie siempre alcista", ind.maximo_drawdown([1, 2, 3, 4]), 0.0, 0.0001)
comprobar("Distancia de 110 respecto a 100", ind.distancia_a(110, 100), 10.0, 0.0001)
comprobar("Distancia con referencia 0 devuelve None", ind.distancia_a(110, 0), None)

# ---------------------------------------------------------------------------
print("\nVolatilidad")
# ---------------------------------------------------------------------------
plana = [100.0] * 40
comprobar("Serie plana -> volatilidad 0", ind.volatilidad_anualizada(plana), 0.0, 0.0001)
# Serie que alterna entre 98 y 102: los rendimientos alternan +4,08% y -3,92%,
# desviación típica ~4% diaria -> 4% * raíz(365) ≈ 76% anualizado.
vol_real = ind.volatilidad_anualizada([100 * (1.02 if i % 2 else 0.98) for i in range(40)])
comprobar("Serie alternante ±2% -> ~76% anualizado", vol_real, 76.4, 2.0)

# ---------------------------------------------------------------------------
print("\nSoporte, resistencia y posición en el rango")
# ---------------------------------------------------------------------------
niveles = ind.soporte_resistencia([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 55], 90)
comprobar("Soporte del rango", niveles["soporte"], 10.0, 0.0001)
comprobar("Resistencia del rango", niveles["resistencia"], 100.0, 0.0001)
comprobar("Posición en el rango (55 entre 10 y 100)", niveles["posicion_en_rango_pct"], 50.0, 0.001)

# ---------------------------------------------------------------------------
print("\nCruce de medias y análisis completo")
# ---------------------------------------------------------------------------
# El detector solo mira los últimos 5 días a propósito: un cruce de hace un mes
# ya no es noticia. Buscamos por fuerza bruta la duración de subida que coloca
# el cruce dentro de esa ventana, y comprobamos las tres situaciones posibles.
bajada = [100 - i * 0.4 for i in range(120)]

recientes = []
for dias_subida in range(1, 60):
    serie_t = bajada + [bajada[-1] + i * 2.2 for i in range(1, dias_subida + 1)]
    if ind.analizar(serie_t)["cruce_medias"] == "alcista":
        recientes.append(dias_subida)

comprobar("El cruce alcista se detecta en alguna ventana",
          1 if recientes else None, 1)
comprobar("Solo se detecta durante 5 días (no antes ni después)",
          float(len(recientes)) if recientes else None, 5.0, 0.001)

if recientes:
    justo = bajada + [bajada[-1] + i * 2.2 for i in range(1, recientes[0] + 1)]
    analisis = ind.analizar(justo)
    comprobar("Cruce alcista en la ventana correcta",
              1 if analisis["cruce_medias"] == "alcista" else None, 1)
    print(f"  [INFO ] RSI en el giro alcista: {analisis['rsi']:.1f}")

    viejo = bajada + [bajada[-1] + i * 2.2 for i in range(1, recientes[-1] + 15)]
    comprobar("Un cruce antiguo ya no se reporta",
              1 if ind.analizar(viejo)["cruce_medias"] is None else None, 1)

# Y el caso simétrico: subida larga seguida de giro a la baja
subida_larga = [100 + i * 0.4 for i in range(120)]
bajistas = [d for d in range(1, 60)
            if ind.analizar(subida_larga + [subida_larga[-1] - i * 2.2
                                            for i in range(1, d + 1)]
                            )["cruce_medias"] == "bajista"]
comprobar("El cruce bajista también se detecta", 1 if bajistas else None, 1)

# Serie plana: no debe inventarse ningún cruce
comprobar("Serie plana no genera cruces",
          1 if ind.analizar([100.0] * 250)["cruce_medias"] is None else None, 1)

vacio = ind.analizar([50.0])
comprobar("analizar() con un solo dato no revienta", vacio["precio"], 50.0, 0.0001)
comprobar("analizar() con un solo dato: RSI None", vacio["rsi"], None)

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if FALLOS:
    print(f"{len(FALLOS)} COMPROBACIÓN(ES) FALLIDA(S):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
print("Todas las comprobaciones han pasado.")
print("=" * 60)
