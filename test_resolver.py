#!/usr/bin/env python3
"""
Comprobaciones del resolutor de identificadores.

Aquí se decide qué activo real hay detrás de lo que escribes en cartera.csv.
Si se equivoca, todas las cifras de esa posición son falsas pero creíbles, así
que conviene que esté bien atado.

    python3 test_resolver.py
"""

from __future__ import annotations

import sys

from radar import resolver

FALLOS: list[str] = []


def comprobar(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"  [{'OK  ' if ok else 'FALLO'}] {nombre}")
    if not ok:
        print(f"         obtenido: {obtenido!r}   esperado: {esperado!r}")
        FALLOS.append(nombre)


# ---------------------------------------------------------------------------
print("\nReconocer un ISIN")
# ---------------------------------------------------------------------------
for texto, esperado in [
    ("IE00B5BMR087", True),    # iShares Core S&P 500
    ("IE00B3ZW0K18", True),    # el cubierto en euros
    ("ES0105630315", True),    # PUIG
    ("US21037T1097", True),    # Constellation Energy
    ("ie00b5bmr087", True),    # en minúsculas
    ("  IE00B5BMR087  ", True),
    ("CEG", False),
    ("SXR8.DE", False),
    ("bitcoin", False),
    ("IE00B5BMR08", False),    # once caracteres
    ("IE00B5BMR087X", False),  # trece
    ("1E00B5BMR087", False),   # no empieza por dos letras
    ("", False),
]:
    comprobar(f"es_isin({texto!r})", resolver.es_isin(texto), esperado)

# ---------------------------------------------------------------------------
print("\nDistinguir un símbolo de lo que no lo es")
# ---------------------------------------------------------------------------
for texto, esperado in [
    ("CEG", True), ("AAPL", True), ("SXR8.DE", True), ("PUIG.MC", True),
    ("VWCE.DE", True), ("^GSPC", True), ("EURUSD=X", True),
    ("Constellation Energy", False),
    ("iShares Core S&P 500", False),
    ("S&P 500 EUR (Acc)", False),
]:
    comprobar(f"parece_simbolo({texto!r})", resolver.parece_simbolo(texto), esperado)

# El ISIN cumple el patrón de "letras y números", así que hay que asegurarse
# de que el resolutor no lo confunde con un símbolo y se salta la traducción.
isin = "IE00B5BMR087"
comprobar("Un ISIN no se toma por símbolo ya resuelto",
          resolver.parece_simbolo(isin) and not resolver.es_isin(isin), False)


# ---------------------------------------------------------------------------
print("\nElegir entre varias cotizaciones del mismo fondo")
# ---------------------------------------------------------------------------
class FuenteFalsa:
    """Imita al buscador de Yahoo con respuestas controladas."""

    def __init__(self, resultados):
        self.resultados = resultados
        self.consultas = []

    def buscar(self, texto, limite=15):
        self.consultas.append(texto)
        return self.resultados


# El mismo ETF cotiza en Londres (USD) y en Xetra (EUR): debe ganar el euro
fuente = FuenteFalsa([
    {"simbolo": "CSPX.L", "nombre": "iShares Core S&P 500", "tipo": "ETF", "bolsa": "LSE"},
    {"simbolo": "SXR8.DE", "nombre": "iShares Core S&P 500", "tipo": "ETF", "bolsa": "XETRA"},
])
simbolo, info = resolver.resolver_uno("IE00B5BMR087", fuente, {}, [])
comprobar("Entre Londres y Xetra elige Xetra (euros)", simbolo, "SXR8.DE")
comprobar("Guarda las alternativas para poder revisarlas",
          len(info["alternativas"]) >= 1, True)

# Los fondos de inversión no cotizan intradía: se descartan
fuente = FuenteFalsa([
    {"simbolo": "0P0001ABCD.F", "nombre": "Fondo raro", "tipo": "MUTUALFUND", "bolsa": "—"},
    {"simbolo": "CEG", "nombre": "Constellation Energy", "tipo": "EQUITY", "bolsa": "NasdaqGS"},
])
simbolo, _ = resolver.resolver_uno("Constellation Energy", fuente, {}, [])
comprobar("Descarta los fondos y elige la acción", simbolo, "CEG")

# Si lo que escribes coincide exactamente con un símbolo, ese gana
fuente = FuenteFalsa([
    {"simbolo": "CEG.DE", "nombre": "Constellation (Xetra)", "tipo": "EQUITY", "bolsa": "XETRA"},
    {"simbolo": "CEG", "nombre": "Constellation Energy", "tipo": "EQUITY", "bolsa": "NasdaqGS"},
])
simbolo, _ = resolver.resolver_uno("CEG", fuente, {}, [])
comprobar("Un símbolo exacto se respeta aunque haya versión europea", simbolo, "CEG")

# ---------------------------------------------------------------------------
print("\nCuándo NO se consulta a la red")
# ---------------------------------------------------------------------------
fuente = FuenteFalsa([])
resolver.resolver_uno("PUIG.MC", fuente, {}, [])
comprobar("Un símbolo válido no genera consulta", fuente.consultas, [])

fuente = FuenteFalsa([{"simbolo": "X", "nombre": "X", "tipo": "EQUITY", "bolsa": "—"}])
cache = {"IE00B5BMR087": {"simbolo": "SXR8.DE", "nombre": "cacheado"}}
simbolo, _ = resolver.resolver_uno("IE00B5BMR087", fuente, cache, [])
comprobar("Lo ya traducido sale de la caché", simbolo, "SXR8.DE")
comprobar("...y no consulta a la red", fuente.consultas, [])

# ---------------------------------------------------------------------------
print("\nCuando no se encuentra nada")
# ---------------------------------------------------------------------------
avisos = []
fuente = FuenteFalsa([])
simbolo, info = resolver.resolver_uno("Empresa Que No Existe SL", fuente, {}, avisos)
comprobar("Devuelve el texto original sin romper", simbolo, "Empresa Que No Existe SL")
comprobar("No inventa una traducción", info, None)
comprobar("Avisa de que no ha encontrado nada", len(avisos), 1)


class FuenteRota:
    def buscar(self, texto, limite=15):
        raise ConnectionError("sin red")


avisos = []
simbolo, info = resolver.resolver_uno("IE00B5BMR087", FuenteRota(), {}, avisos)
comprobar("Si la búsqueda falla, no revienta", simbolo, "IE00B5BMR087")
comprobar("Y deja constancia del fallo", len(avisos), 1)

# ---------------------------------------------------------------------------
print("\nResolución de una cartera completa")
# ---------------------------------------------------------------------------
fuente = FuenteFalsa([
    {"simbolo": "SXR8.DE", "nombre": "iShares Core S&P 500", "tipo": "ETF", "bolsa": "XETRA"},
])
posiciones = [
    ("IE00B5BMR087", "etf", 1.37, 131.37, "EUR"),
    ("PUIG.MC", "accion", 3.21, 17.18, "EUR"),
    ("bitcoin", "cripto", 0.0005, 60000, None),
]
resueltas, traducciones, avisos = resolver.resolver_posiciones(
    posiciones, fuente, verbose=False)

comprobar("No se pierde ninguna posición", len(resueltas), 3)
comprobar("El ISIN queda traducido", resueltas[0][0], "SXR8.DE")
comprobar("El símbolo que ya era válido no cambia", resueltas[1][0], "PUIG.MC")
comprobar("La cripto se deja en paz", resueltas[2][0], "bitcoin")
comprobar("Las unidades y precios se conservan", resueltas[0][2:], (1.37, 131.37, "EUR"))
comprobar("Se registra la traducción para el informe", "SXR8.DE" in traducciones, True)
comprobar("La cripto no consulta al buscador de bolsa",
          "bitcoin" not in fuente.consultas, True)


# ---------------------------------------------------------------------------
print("\nRescate: el código del bróker no es el símbolo de Yahoo")
# ---------------------------------------------------------------------------
# Trade Republic enseña "B1B" para PUIG Brands: es el código de la bolsa
# alemana y Yahoo no lo conoce. Sin forzar, el resolutor lo daría por bueno
# porque "parece" un símbolo, y la posición se quedaría sin datos.
comprobar("«B1B» parece un símbolo válido", resolver.parece_simbolo("B1B"), True)

fuente = FuenteFalsa([
    {"simbolo": "PUIG.MC", "nombre": "PUIG Brands, S.A.", "tipo": "EQUITY",
     "bolsa": "Madrid"},
])
simbolo, info = resolver.resolver_uno("B1B", fuente, {}, [])
comprobar("Sin forzar, se deja tal cual y no se busca", (simbolo, fuente.consultas),
          ("B1B", []))

simbolo, info = resolver.resolver_uno("B1B", fuente, {}, [], forzar=True)
comprobar("Forzando, sí se busca y se encuentra", simbolo, "PUIG.MC")
comprobar("Y se registra a qué se ha traducido", info["nombre"], "PUIG Brands, S.A.")

# Buscando por el nombre que escribió el usuario en vez de por el código
fuente = FuenteFalsa([
    {"simbolo": "PUIG.MC", "nombre": "PUIG Brands, S.A.", "tipo": "EQUITY",
     "bolsa": "Madrid"},
])
simbolo, _ = resolver.resolver_uno("PUIG Brands", fuente, {}, [], forzar=True)
comprobar("También funciona buscando por el nombre", simbolo, "PUIG.MC")

# Forzar ignora la caché: si la traducción guardada era mala, se rehace
cache = {"B1B": {"simbolo": "MALO.XX", "nombre": "traducción vieja"}}
fuente = FuenteFalsa([
    {"simbolo": "PUIG.MC", "nombre": "PUIG Brands, S.A.", "tipo": "EQUITY",
     "bolsa": "Madrid"},
])
simbolo, _ = resolver.resolver_uno("B1B", fuente, cache, [], forzar=True)
comprobar("Forzar ignora una traducción guardada mala", simbolo, "PUIG.MC")

# Y el ISIN, que es lo recomendado, no necesita forzar nada
fuente = FuenteFalsa([
    {"simbolo": "PUIG.MC", "nombre": "PUIG Brands, S.A.", "tipo": "EQUITY",
     "bolsa": "Madrid"},
])
simbolo, _ = resolver.resolver_uno("ES0105630315", fuente, {}, [])
comprobar("El ISIN se resuelve sin trucos", simbolo, "PUIG.MC")
comprobar("El ISIN sí genera consulta", len(fuente.consultas), 1)

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if FALLOS:
    print(f"{len(FALLOS)} COMPROBACIÓN(ES) FALLIDA(S):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
print("Todas las comprobaciones han pasado.")
print("=" * 60)
