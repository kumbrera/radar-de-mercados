#!/usr/bin/env python3
"""
Comprobaciones de la cartera y de la evaluación de ETFs.

Aquí lo que se valida es aritmética con dinero, así que las tolerancias son
estrictas: los números tienen que salir exactos.

    python3 test_cartera.py
"""

from __future__ import annotations

import sys

from radar import cartera as mod_cartera
from radar import config, indicators, scoring_bolsa

FALLOS: list[str] = []


def comprobar(nombre, obtenido, esperado, tol=0.0):
    if esperado is None:
        ok = obtenido is None
    elif obtenido is None:
        ok = False
    else:
        ok = abs(obtenido - esperado) <= tol
    marca = "OK  " if ok else "FALLO"
    v = "None" if obtenido is None else f"{obtenido:.4f}"
    e = "None" if esperado is None else f"{esperado:.4f}"
    print(f"  [{marca}] {nombre}: obtenido={v} esperado={e}")
    if not ok:
        FALLOS.append(nombre)


def comprobar_texto(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"  [{'OK  ' if ok else 'FALLO'}] {nombre}: obtenido={obtenido!r} esperado={esperado!r}")
    if not ok:
        FALLOS.append(nombre)


# ---------------------------------------------------------------------------
print("\nCartera: aritmética básica (todo en euros)")
# ---------------------------------------------------------------------------
config.POSICIONES = [
    ("ETF_A", "etf", 10.0, 100.0),      # coste 1000, ahora 1100 -> +100
    ("CRIP_A", "cripto", 2.0, 50.0),    # coste  100, ahora   80 -> -20
]
config.REPARTO_OBJETIVO = {"etf": 80, "cripto": 20}
config.APORTACION_MENSUAL = 0.0

precios = {
    "ETF_A":  {"precio": 110.0, "divisa": "EUR", "nombre": "ETF A", "cambio_24h_pct": 1.0},
    "CRIP_A": {"precio": 40.0,  "divisa": "EUR", "nombre": "Cripto A", "cambio_24h_pct": -5.0},
}
c = mod_cartera.construir(precios, eur_usd=None)

comprobar("Valor total (1100 + 80)", c["total_actual"], 1180.0, 0.001)
comprobar("Invertido total (1000 + 100)", c["total_invertido"], 1100.0, 0.001)
comprobar("Ganancia (1180 - 1100)", c["ganancia"], 80.0, 0.001)
comprobar("Ganancia % (80/1100)", c["ganancia_pct"], 7.2727, 0.001)

etf = next(p for p in c["posiciones"] if p["id"] == "ETF_A")
crip = next(p for p in c["posiciones"] if p["id"] == "CRIP_A")
comprobar("Valor del ETF", etf["valor"], 1100.0, 0.001)
comprobar("Ganancia % del ETF", etf["ganancia_pct"], 10.0, 0.001)
comprobar("Ganancia % de la cripto", crip["ganancia_pct"], -20.0, 0.001)
comprobar("Peso del ETF (1100/1180)", etf["peso_pct"], 93.2203, 0.001)
comprobar("Los pesos suman 100", sum(p["peso_pct"] for p in c["posiciones"]), 100.0, 0.001)

# Movimiento del día ponderado: (1100*1% + 80*-5%) / 1180
# (1100 * +1% + 80 * -5%) / 1180 = 7 / 1180 = 0,5932%
comprobar("Cambio de hoy ponderado", c["cambio_hoy"]["pct"], 0.5932, 0.001)

# ---------------------------------------------------------------------------
print("\nCartera: conversión de divisas")
# ---------------------------------------------------------------------------
config.POSICIONES = [("USA", "etf", 10.0, 100.0)]
config.REPARTO_OBJETIVO = {"etf": 100}
precios_usd = {"USA": {"precio": 110.0, "divisa": "USD", "nombre": "ETF USA",
                       "cambio_24h_pct": 0.0}}

# Con EUR/USD = 1.10: 1100 dólares son 1000 euros
c2 = mod_cartera.construir(precios_usd, eur_usd=1.10)
comprobar("1100 USD a 1,10 son 1000 EUR", c2["total_actual"], 1000.0, 0.001)
comprobar("Coste 1000 USD a 1,10 son 909,09 EUR", c2["total_invertido"], 909.0909, 0.001)
comprobar("La ganancia en % no cambia con la divisa",
          c2["posiciones"][0]["ganancia_pct"], 10.0, 0.001)

# Sin tipo de cambio, debe avisar en vez de mezclar en silencio
c3 = mod_cartera.construir(precios_usd, eur_usd=None)
comprobar("Sin tipo de cambio se marca la conversión como incompleta",
          1.0 if c3["conversion_incompleta"] else None, 1.0)

# ---------------------------------------------------------------------------
print("\nCartera: desviación respecto al objetivo")
# ---------------------------------------------------------------------------
config.POSICIONES = [
    ("A", "etf", 1.0, 50.0),      # 50 -> 50% real, objetivo 70%
    ("B", "cripto", 1.0, 50.0),   # 50 -> 50% real, objetivo 30%
]
config.REPARTO_OBJETIVO = {"etf": 70, "cripto": 30}
config.DESVIACION_AVISO_PCT = 5.0
p = {"A": {"precio": 50.0, "divisa": "EUR", "nombre": "A", "cambio_24h_pct": 0},
     "B": {"precio": 50.0, "divisa": "EUR", "nombre": "B", "cambio_24h_pct": 0}}
c4 = mod_cartera.construir(p, None)

r_etf = next(r for r in c4["reparto"] if r["tipo"] == "etf")
r_cri = next(r for r in c4["reparto"] if r["tipo"] == "cripto")
comprobar("ETF real 50%", r_etf["real_pct"], 50.0, 0.001)
comprobar("ETF desviación -20 puntos", r_etf["desviacion"], -20.0, 0.001)
comprobar_texto("ETF marcado como por debajo", r_etf["estado"], "bajo")
comprobar("Cripto desviación +20 puntos", r_cri["desviacion"], 20.0, 0.001)
comprobar_texto("Cripto marcada como por encima", r_cri["estado"], "sobre")

# Una desviación pequeña no debe generar aviso
config.REPARTO_OBJETIVO = {"etf": 52, "cripto": 48}
c5 = mod_cartera.construir(p, None)
comprobar_texto("Desviación de 2 puntos no genera aviso",
                next(r for r in c5["reparto"] if r["tipo"] == "etf")["estado"], "ok")

# ---------------------------------------------------------------------------
print("\nCartera: reparto de la aportación")
# ---------------------------------------------------------------------------
config.REPARTO_OBJETIVO = {"etf": 70, "cripto": 30}
config.APORTACION_MENSUAL = 100.0
c6 = mod_cartera.construir(p, None)
ap = c6["aportacion"]

comprobar("La aportación reparte el importe completo",
          sum(r["importe"] for r in ap["reparto"]), 100.0, 0.01)
comprobar("Los porcentajes de la aportación suman 100",
          sum(r["pct"] for r in ap["reparto"]), 100.0, 0.01)
# Cartera de 100 (50 ETF / 50 cripto), objetivo 70/30, aportación de 100.
# Tras aportar habrá 200: el ETF debería tener 140 (le faltan 90) y la cripto
# 60 (le faltan 10). El reparto correcto es 90/10, y deja la cartera clavada
# en el objetivo sin vender nada.
por_tipo = {r["tipo"]: r["importe"] for r in ap["reparto"]}
comprobar("Al ETF le corresponden 90", por_tipo.get("etf"), 90.0, 0.01)
comprobar("A la cripto le corresponden 10", por_tipo.get("cripto"), 10.0, 0.01)
comprobar("Tras aportar, el ETF queda exactamente en su 70% objetivo",
          (50 + por_tipo.get("etf", 0)) / 200 * 100, 70.0, 0.01)
comprobar("Tras aportar, la cripto queda exactamente en su 30% objetivo",
          (50 + por_tipo.get("cripto", 0)) / 200 * 100, 30.0, 0.01)

# Caso contrario: todo por encima del objetivo -> reparto según objetivo
config.REPARTO_OBJETIVO = {"etf": 50, "cripto": 50}
c7 = mod_cartera.construir(p, None)
ap7 = c7["aportacion"]
comprobar("Cartera equilibrada: la aportación sigue sumando el total",
          sum(r["importe"] for r in ap7["reparto"]), 100.0, 0.01)

# ---------------------------------------------------------------------------
print("\nCartera: casos límite")
# ---------------------------------------------------------------------------
config.POSICIONES = []
c8 = mod_cartera.construir({}, None)
comprobar("Cartera vacía no revienta", 1.0 if c8["vacia"] else None, 1.0)
comprobar("Cartera vacía: total 0", c8["total_actual"], 0.0, 0.001)
comprobar("Cartera vacía: sin avisos", float(len(mod_cartera.avisos(c8))), 0.0, 0.001)

config.POSICIONES = [("FANTASMA", "etf", 1.0, 10.0)]
c9 = mod_cartera.construir({}, None)
comprobar("Posición sin precio se aparta sin romper",
          float(len(c9["sin_datos"])), 1.0, 0.001)
comprobar("Posición sin precio no cuenta en el total", c9["total_actual"], 0.0, 0.001)

# ---------------------------------------------------------------------------
print("\nAvisos de cartera")
# ---------------------------------------------------------------------------
config.POSICIONES = [("X", "etf", 1.0, 100.0), ("Y", "cripto", 1.0, 10.0)]
config.REPARTO_OBJETIVO = {"etf": 50, "cripto": 50}
px = {"X": {"precio": 100.0, "divisa": "EUR", "nombre": "X", "cambio_24h_pct": 0},
      "Y": {"precio": 5.0, "divisa": "EUR", "nombre": "Y", "cambio_24h_pct": 0}}
c10 = mod_cartera.construir(px, None)
avisos = mod_cartera.avisos(c10)
tipos = {a["tipo"] for a in avisos}
comprobar("Detecta concentración excesiva (X pesa 95%)",
          1.0 if "concentracion" in tipos else None, 1.0)
comprobar("Detecta la posición con pérdidas fuertes (Y a -50%)",
          1.0 if "posicion_perdidas" in tipos else None, 1.0)
comprobar("Todos los avisos llevan explicación de la trampa",
          1.0 if all(a.get("ojo") for a in avisos) else None, 1.0)


# ---------------------------------------------------------------------------
print("\nDivisa de compra distinta de la de cotización")
# ---------------------------------------------------------------------------
# El caso real: Constellation Energy cotiza en USD en el Nasdaq, pero Trade
# Republic te la cobra en euros. Si convertimos también el precio de compra,
# el coste sale inflado y las ganancias son mentira.
config.POSICIONES = [("CEG", "accion", 1.0, 100.0, "EUR")]
config.REPARTO_OBJETIVO = {"accion": 100}
config.APORTACION_MENSUAL = 0.0

precios_ceg = {"CEG": {"precio": 110.0, "divisa": "USD", "nombre": "Constellation",
                       "cambio_24h_pct": 0.0}}
cc = mod_cartera.construir(precios_ceg, eur_usd=1.10)

comprobar("Valor actual: 110 USD a 1,10 = 100 EUR", cc["total_actual"], 100.0, 0.001)
comprobar("Coste: 100 EUR se quedan en 100 EUR (NO se reconvierten)",
          cc["total_invertido"], 100.0, 0.001)
comprobar("Resultado correcto: ni ganancia ni pérdida", cc["ganancia"], 0.0, 0.001)

# Sin declarar la divisa, el coste se trata como USD (comportamiento anterior)
config.POSICIONES = [("CEG", "accion", 1.0, 100.0)]
cc2 = mod_cartera.construir(precios_ceg, eur_usd=1.10)
comprobar("Sin declarar divisa, el coste se convierte desde USD",
          cc2["total_invertido"], 90.9091, 0.001)
comprobar("...lo que daría una ganancia ficticia del 10%",
          cc2["ganancia_pct"], 10.0, 0.001)

# ---------------------------------------------------------------------------
print("\nDetección de identificador equivocado")
# ---------------------------------------------------------------------------
config.POSICIONES = [("XXXX", "accion", 1.0, 131.37, "EUR")]
config.REPARTO_OBJETIVO = {"accion": 100}
# Un ETF del S&P 500 a 585 EUR cuando pagaste 131: casi seguro otro producto
malo = mod_cartera.construir(
    {"XXXX": {"precio": 585.40, "divisa": "EUR", "nombre": "Otro fondo",
              "cambio_24h_pct": 0.0}}, None)
tipos_malo = {a["tipo"] for a in mod_cartera.avisos(malo)}
comprobar("Avisa de que el identificador puede estar mal",
          1.0 if "ticker_sospechoso" in tipos_malo else None, 1.0)

# Una subida grande pero plausible NO debe disparar el aviso
bueno = mod_cartera.construir(
    {"XXXX": {"precio": 180.0, "divisa": "EUR", "nombre": "Normal",
              "cambio_24h_pct": 0.0}}, None)
tipos_bueno = {a["tipo"] for a in mod_cartera.avisos(bueno)}
comprobar("Una subida del 37% no dispara el aviso",
          1.0 if "ticker_sospechoso" not in tipos_bueno else None, 1.0)

# Cripto comprada muy abajo: x4 es el límite, x3 debe pasar sin aviso
config.POSICIONES = [("bitcoin", "cripto", 1.0, 20000.0)]
config.REPARTO_OBJETIVO = {"cripto": 100}
cripto_ok = mod_cartera.construir(
    {"bitcoin": {"precio": 60000.0, "divisa": "EUR", "nombre": "Bitcoin",
                 "cambio_24h_pct": 0.0}}, None)
comprobar("Un x3 real en cripto no se confunde con un error",
          1.0 if "ticker_sospechoso" not in {a["tipo"] for a in mod_cartera.avisos(cripto_ok)} else None, 1.0)

# ---------------------------------------------------------------------------
print("\nETFs: el coste de las comisiones")
# ---------------------------------------------------------------------------
# 10.000 € al 7% durante 30 años = 76.122,55 €
c30 = scoring_bolsa.coste_en_30_anios(0.20, capital=10_000, rentabilidad=7.0, anios=30)
comprobar("Capital final sin comisión (10.000 x 1,07^30)",
          c30["final_sin_comision"], 76_122.55, 1.0)
# Al 6,8% (7% - 0,20%): 10.000 x 1,068^30 = 71.967,69
comprobar("Capital final con un TER del 0,20%", c30["final_con_comision"], 71_967.69, 1.0)
comprobar("Coste de la comisión", c30["coste"], 4_154.86, 1.0)
comprobar("El coste representa ~5,5% del capital final", c30["coste_pct"], 5.4581, 0.01)

# Los mismos números que aparecen en el glosario, para que texto y código no
# se separen nunca: con un TER del 1,20% quedan 54.271 EUR.
c120 = scoring_bolsa.coste_en_30_anios(1.20, capital=10_000, rentabilidad=7.0, anios=30)
comprobar("Glosario: con un TER del 1,20% quedan 54.271 EUR",
          c120["final_con_comision"], 54_271.28, 1.0)
comprobar("Glosario: la diferencia entre 0,20% y 1,20% son 17.696 EUR",
          c30["final_con_comision"] - c120["final_con_comision"], 17_696.42, 1.0)

# Un TER de 0 no debe costar nada
c0 = scoring_bolsa.coste_en_30_anios(0.0)
comprobar("Con TER 0 el coste es 0", c0["coste"], 0.0, 0.001)
comprobar("Sin dato de TER devuelve None",
          1.0 if scoring_bolsa.coste_en_30_anios(None) is None else None, 1.0)

# ---------------------------------------------------------------------------
print("\nETFs: la nota premia lo barato")
# ---------------------------------------------------------------------------
serie = [100 * (1.0003 ** i) for i in range(600)]
ind = indicators.analizar_bolsa(serie)

base = {"patrimonio": 10_000_000_000, "divisa": "EUR",
        "top_holdings": [{"nombre": f"E{i}", "peso": 0.01} for i in range(10)],
        "sectores": {"tech": 0.25}}

barato = scoring_bolsa.puntuar_etf("A", "ETF barato", {**base, "ter": 0.0007}, ind)
caro = scoring_bolsa.puntuar_etf("B", "ETF caro", {**base, "ter": 0.0150}, ind)
comprobar("El ETF barato puntúa más que el caro",
          1.0 if barato["nota"] > caro["nota"] else None, 1.0)
print(f"  [INFO ] barato (0,07%): {barato['nota']}/10 · caro (1,50%): {caro['nota']}/10")

pequenio = scoring_bolsa.puntuar_etf("C", "ETF pequeño",
                                     {**base, "ter": 0.0007, "patrimonio": 20_000_000}, ind)
comprobar("Un fondo diminuto puntúa menos que uno grande igual de barato",
          1.0 if pequenio["nota"] < barato["nota"] else None, 1.0)

concentrado = scoring_bolsa.puntuar_etf(
    "D", "ETF concentrado",
    {**base, "ter": 0.0007,
     "top_holdings": [{"nombre": f"E{i}", "peso": 0.08} for i in range(10)]}, ind)
comprobar("Un fondo concentrado puntúa menos que uno diversificado",
          1.0 if concentrado["nota"] < barato["nota"] else None, 1.0)

comprobar("Los pesos del scoring de ETF suman 100",
          float(sum(scoring_bolsa.PESOS_ETF.values())), 100.0, 0.001)

# Sin ningún dato, no debe reventar
vacio = scoring_bolsa.puntuar_etf("E", "ETF sin datos", {}, ind)
comprobar("Un ETF sin datos devuelve nota igualmente",
          1.0 if 0 <= vacio["nota"] <= 10 else None, 1.0)

# ---------------------------------------------------------------------------
print("\nComparativa de ETFs")
# ---------------------------------------------------------------------------
comp = scoring_bolsa.comparar_etfs([barato, caro])
comprobar("Identifica la diferencia de comisión", comp["diferencia_pct"], 1.43, 0.001)
comprobar_texto("Señala el barato correctamente", comp["barato"]["simbolo"], "A")
comprobar_texto("Señala el caro correctamente", comp["caro"]["simbolo"], "B")
comprobar("Con un solo ETF no hay comparativa",
          1.0 if scoring_bolsa.comparar_etfs([barato]) is None else None, 1.0)

# ---------------------------------------------------------------------------
print("\nIndicadores de bolsa")
# ---------------------------------------------------------------------------
# La volatilidad bursátil usa 252 sesiones, no 365 días
plana_con_ruido = [100 * (1.01 if i % 2 else 0.99) for i in range(60)]
v_bolsa = indicators.volatilidad_bolsa(plana_con_ruido, 30)
v_cripto = indicators.volatilidad_anualizada(plana_con_ruido, 30)
comprobar("La volatilidad bursátil es menor que la cripto para la misma serie",
          1.0 if v_bolsa < v_cripto else None, 1.0)
comprobar("Proporción exacta raíz(252/365)", v_bolsa / v_cripto, (252/365) ** 0.5, 0.0001)

# CAGR: duplicar en exactamente 2 años son 252*2 sesiones -> +41,42% anual
dos_anios = [100 * (2 ** (i / (252 * 2 - 1))) for i in range(252 * 2)]
comprobar("CAGR de duplicar en 2 años", indicators.rentabilidad_anualizada(dos_anios),
          41.4214, 0.05)
comprobar("CAGR con serie corta devuelve None",
          indicators.rentabilidad_anualizada([100, 101, 102]), None)

ind_b = indicators.analizar_bolsa([100 + i for i in range(300)])
comprobar("En máximos, la distancia al máximo de 52s es 0",
          ind_b["dist_max52s_pct"], 0.0, 0.001)
comprobar("analizar_bolsa incluye el cambio de la sesión",
          ind_b["cambio_1d_pct"], (399/398 - 1) * 100, 0.001)

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if FALLOS:
    print(f"{len(FALLOS)} COMPROBACIÓN(ES) FALLIDA(S):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
print("Todas las comprobaciones han pasado.")
print("=" * 60)
