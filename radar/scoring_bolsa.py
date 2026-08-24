"""
Evaluación de ETFs.

Un ETF no se juzga como una cripto. Aquí no hay "proyecto" que investigar:
hay un producto financiero con unas características concretas que puedes
comparar objetivamente con sus alternativas.

Lo que de verdad decide el resultado a 20 años, por orden de importancia:

  1. EL COSTE (TER). Es lo único garantizado. Un 0,20% más de comisión sobre
     30 años se come en torno al 6% de tu capital final. No es una opinión,
     es aritmética.
  2. EL TAMAÑO DEL FONDO. Los fondos pequeños se cierran o se fusionan, y eso
     te fuerza a vender en un momento que no eliges (y a tributar).
  3. LA DIVERSIFICACIÓN. Cuánta concentración hay dentro.
  4. LA DIVISA. Determina si asumes riesgo de tipo de cambio además del de mercado.
"""

from __future__ import annotations

from . import config


def _n(valor: float, decimales: int = 2, signo: bool = False) -> str:
    """Formatea un número al estilo español (coma decimal), sin tocar la frase."""
    fmt = f"{valor:+.{decimales}f}" if signo else f"{valor:.{decimales}f}"
    return fmt.replace(".", ",")


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Coste
# ---------------------------------------------------------------------------

def _evaluar_coste(ter: float | None) -> dict:
    """ter viene en tanto por uno: 0.0007 = 0,07%"""
    if ter is None:
        return {"nota": 50.0, "texto": "Sin dato de comisión disponible. Búscalo en la "
                                       "ficha del fondo antes de comprar: es el dato más "
                                       "importante de todos.", "ter_pct": None}
    pct = ter * 100
    if pct <= 0.10:
        nota = 100.0
        texto = f"Comisión del {_n(pct)}% anual. Está entre lo más barato del mercado."
    elif pct <= 0.25:
        nota = 82.0
        texto = f"Comisión del {_n(pct)}% anual. Razonable para un indexado."
    elif pct <= 0.50:
        nota = 55.0
        texto = f"Comisión del {_n(pct)}% anual. Empieza a pesar a largo plazo."
    elif pct <= 1.0:
        nota = 25.0
        texto = f"Comisión del {_n(pct)}% anual. Cara para un producto indexado."
    else:
        nota = 5.0
        texto = f"Comisión del {_n(pct)}% anual. Muy cara: busca alternativas."
    return {"nota": nota, "texto": texto, "ter_pct": pct}


def coste_en_30_anios(ter_pct: float | None, capital: float = 10_000,
                      rentabilidad: float = 7.0, anios: int = 30) -> dict | None:
    """
    Cuánto te cuesta esa comisión en dinero, no en porcentaje.

    Comparamos el mismo capital creciendo con y sin la comisión. La diferencia
    es lo que paga el fondo por gestionarte un índice.
    """
    if ter_pct is None:
        return None
    bruto = capital * (1 + rentabilidad / 100) ** anios
    neto = capital * (1 + (rentabilidad - ter_pct) / 100) ** anios
    return {
        "capital": capital, "anios": anios, "rentabilidad": rentabilidad,
        "final_sin_comision": bruto, "final_con_comision": neto,
        "coste": bruto - neto, "coste_pct": (bruto - neto) / bruto * 100,
    }


# ---------------------------------------------------------------------------
# Tamaño, diversificación, divisa, trayectoria
# ---------------------------------------------------------------------------

def _evaluar_tamanio(patrimonio: float | None) -> dict:
    if not patrimonio:
        return {"nota": 50.0, "texto": "Sin dato de patrimonio del fondo."}
    if patrimonio >= 5_000_000_000:
        return {"nota": 100.0, "texto": f"Fondo muy grande ({_millones(patrimonio)}). "
                                        "Riesgo de cierre prácticamente nulo."}
    if patrimonio >= 500_000_000:
        return {"nota": 85.0, "texto": f"Fondo consolidado ({_millones(patrimonio)})."}
    if patrimonio >= 100_000_000:
        return {"nota": 60.0, "texto": f"Tamaño correcto ({_millones(patrimonio)}), "
                                       "aunque no es de los grandes."}
    return {"nota": 25.0, "texto": f"Fondo pequeño ({_millones(patrimonio)}). Los fondos "
                                   "por debajo de 100 M tienen riesgo real de cierre o "
                                   "fusión, lo que te obligaría a vender sin elegir cuándo."}


def _millones(v: float) -> str:
    if v >= 1e9:
        return f"{_n(v/1e9, 1)} MM {config.SIMBOLO_MONEDA}"
    return f"{v/1e6:.0f} M {config.SIMBOLO_MONEDA}"


def _evaluar_diversificacion(holdings: list[dict], sectores: dict) -> dict:
    if not holdings:
        return {"nota": 50.0, "texto": "Sin datos de composición.", "top10_pct": None}

    top10 = sum((h.get("peso") or 0) for h in holdings) * 100
    mayor_sector = max(sectores.values()) * 100 if sectores else None

    if top10 <= 20:
        nota, texto = 100.0, f"Muy diversificado: las 10 mayores posiciones son el {top10:.0f}% del fondo."
    elif top10 <= 35:
        nota, texto = 78.0, f"Diversificación correcta: el top 10 pesa el {top10:.0f}%."
    elif top10 <= 55:
        nota, texto = 45.0, (f"Concentrado: el top 10 pesa el {top10:.0f}%. Lo que le pase a "
                             "un puñado de empresas manda sobre el resultado.")
    else:
        nota, texto = 20.0, (f"Muy concentrado: el top 10 pesa el {top10:.0f}%. Estás comprando "
                             "unas pocas empresas con envoltorio de fondo.")

    if mayor_sector and mayor_sector > 40:
        nota = max(0, nota - 15)
        texto += f" Además, un solo sector supone el {mayor_sector:.0f}%."

    return {"nota": nota, "texto": texto, "top10_pct": top10}


def _evaluar_divisa(divisa: str | None, nombre: str) -> dict:
    n = (nombre or "").lower()
    cubierto = any(x in n for x in ("hedged", "cubierto", "eur hedged", "eur-hedged"))
    propia = (divisa or "").upper() == config.MONEDA.upper()

    if cubierto:
        return {"nota": 75.0, "cubierto": True,
                "texto": ("Cubierto frente a divisa. Solo ganas o pierdes con el mercado, "
                          "no con el tipo de cambio. A cambio pagas algo más de comisión y, "
                          "a muy largo plazo, la cobertura suele restar rentabilidad.")}
    if propia:
        return {"nota": 85.0, "cubierto": False,
                "texto": f"Cotiza en {divisa}, tu propia moneda. Sin fricción de cambio al operar."}
    return {"nota": 65.0, "cubierto": False,
            "texto": (f"Cotiza en {divisa or 'otra divisa'} y no está cubierto: asumes también "
                      "el riesgo de tipo de cambio. A largo plazo esto tiende a compensarse, "
                      "y evitas el coste de la cobertura; a corto plazo añade vaivenes.")}


def _evaluar_trayectoria(ind: dict) -> dict:
    cagr = ind.get("rentabilidad_anualizada_pct")
    vol = ind.get("volatilidad_1a_pct") or ind.get("volatilidad_pct")

    if cagr is None:
        return {"nota": 50.0, "texto": "Histórico insuficiente para valorar la trayectoria."}

    # Rentabilidad ajustada al riesgo, al estilo de un Sharpe simplificado
    ratio = (cagr / vol) if vol and vol > 0 else None
    texto = f"Ha rentado un {_n(cagr, 1, signo=True)}% anualizado en el periodo analizado"
    if vol:
        texto += f", con una volatilidad del {vol:.0f}%."
    else:
        texto += "."

    if ratio is None:
        nota = 55.0
    elif ratio >= 1.0:
        nota, texto = 95.0, texto + " Excelente relación entre lo que renta y lo que se mueve."
    elif ratio >= 0.5:
        nota, texto = 78.0, texto + " Buena relación rentabilidad/riesgo."
    elif ratio >= 0.2:
        nota = 55.0
    elif ratio >= 0:
        nota, texto = 35.0, texto + " Renta poco para lo que se mueve."
    else:
        nota, texto = 20.0, texto + " Pierde dinero en el periodo analizado."

    return {"nota": _clamp(nota), "texto": texto, "cagr": cagr, "ratio": ratio}


# ---------------------------------------------------------------------------
# Nota final
# ---------------------------------------------------------------------------

PESOS_ETF = {
    "coste": 35,            # lo único garantizado
    "tamanio": 15,
    "diversificacion": 20,
    "divisa": 10,
    "trayectoria": 20,
}


def puntuar_etf(simbolo: str, nombre: str, ficha: dict, ind: dict) -> dict:
    bloques = {
        "coste": _evaluar_coste(ficha.get("ter")),
        "tamanio": _evaluar_tamanio(ficha.get("patrimonio")),
        "diversificacion": _evaluar_diversificacion(
            ficha.get("top_holdings") or [], ficha.get("sectores") or {}),
        "divisa": _evaluar_divisa(ficha.get("divisa"), nombre),
        "trayectoria": _evaluar_trayectoria(ind),
    }
    total = sum(bloques[k]["nota"] * PESOS_ETF[k] for k in bloques) / 100.0
    nota10 = round(total / 10.0, 1)

    if nota10 >= 8.0:
        nivel, color = "Producto sólido", "verde"
    elif nota10 >= 6.5:
        nivel, color = "Correcto", "ambar"
    elif nota10 >= 5.0:
        nivel, color = "Revisar alternativas", "naranja"
    else:
        nivel, color = "Hay opciones mejores", "rojo"

    return {
        "simbolo": simbolo,
        "nombre": nombre,
        "nota": nota10,
        "nivel": nivel,
        "color": color,
        "bloques": bloques,
        "pesos": PESOS_ETF,
        "ter_pct": bloques["coste"].get("ter_pct"),
        "coste_30a": coste_en_30_anios(bloques["coste"].get("ter_pct")),
        "cubierto": bloques["divisa"].get("cubierto"),
    }


def comparar_etfs(evaluados: list[dict]) -> dict | None:
    """
    Si sigues varios ETFs del mismo tipo, la comparación de comisiones es la
    información más accionable del informe entero.
    """
    con_ter = [e for e in evaluados if e.get("ter_pct") is not None]
    if len(con_ter) < 2:
        return None

    barato = min(con_ter, key=lambda e: e["ter_pct"])
    caro = max(con_ter, key=lambda e: e["ter_pct"])
    if barato["simbolo"] == caro["simbolo"]:
        return None

    diferencia = caro["ter_pct"] - barato["ter_pct"]
    impacto = coste_en_30_anios(diferencia)

    return {
        "barato": barato,
        "caro": caro,
        "diferencia_pct": diferencia,
        "impacto": impacto,
        "aviso": ("Ojo: comparar comisiones solo tiene sentido entre fondos que siguen "
                  "el mismo índice. Un ETF global y uno sectorial no son intercambiables "
                  "aunque uno sea más barato."),
    }
