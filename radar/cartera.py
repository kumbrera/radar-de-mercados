"""
Seguimiento de cartera.

Responde a las preguntas que de verdad importan cuando ya has invertido:
  • ¿Cuánto tengo y cuánto he ganado o perdido?
  • ¿Me he desviado del reparto que había decidido?
  • ¿Dónde debería ir la próxima aportación?

Nota sobre las divisas: si tienes activos en dólares y otros en euros, el
sistema convierte todo a tu moneda usando el tipo de cambio EUR/USD del día.
Sin ese ajuste, sumar posiciones en distintas divisas da un total sin sentido.
"""

from __future__ import annotations

from . import config

NOMBRES_TIPO = {
    "etf": "ETFs y fondos",
    "accion": "Acciones",
    "cripto": "Criptomonedas",
    "renta_fija": "Renta fija",
}


# ---------------------------------------------------------------------------

def _convertir(importe: float, divisa: str | None, eur_usd: float | None) -> float:
    """Pasa un importe a la moneda de la cartera (por defecto, euros)."""
    if importe is None:
        return 0.0
    if not divisa or divisa.upper() == config.MONEDA.upper():
        return importe
    if divisa.upper() == "USD" and config.MONEDA.upper() == "EUR":
        if not eur_usd:
            return importe          # sin tipo de cambio, mejor no inventar
        return importe / eur_usd
    if divisa.upper() == "EUR" and config.MONEDA.upper() == "USD":
        if not eur_usd:
            return importe
        return importe * eur_usd
    return importe


def construir(
    precios_actuales: dict[str, dict],
    eur_usd: float | None = None,
) -> dict:
    """
    precios_actuales: {identificador: {"precio": float, "divisa": str,
                                       "nombre": str, "cambio_24h_pct": float}}
    """
    posiciones = []
    total_actual = 0.0
    total_invertido = 0.0
    conversion_incompleta = False

    for fila in config.POSICIONES:
        # La quinta columna (divisa de compra) es opcional
        identificador, tipo, unidades, precio_medio = fila[:4]
        divisa_compra = fila[4] if len(fila) > 4 else None
        # El nombre que hayas escrito tú en cartera.csv manda sobre el nombre
        # oficial: «S&P 500 EUR (Acc)» se lee mejor que el nombre completo del
        # folleto del fondo.
        nombre_propio = fila[5] if len(fila) > 5 else None

        datos = precios_actuales.get(identificador)
        if not datos or not datos.get("precio"):
            posiciones.append({
                "id": identificador, "tipo": tipo, "unidades": unidades,
                "precio_medio": precio_medio, "sin_datos": True,
                "nombre": nombre_propio or identificador,
            })
            continue

        divisa = datos.get("divisa")

        # El precio actual viene en la divisa en que cotiza el activo. Tu precio
        # de compra puede estar en otra: Trade Republic te cobra en euros
        # acciones que cotizan en dólares. Si no lo distinguimos, convertimos
        # dos veces y el coste sale mal.
        divisa_coste = divisa_compra or divisa

        for d in (divisa, divisa_coste):
            if d and d.upper() != config.MONEDA.upper() and not eur_usd:
                conversion_incompleta = True

        valor = _convertir(datos["precio"] * unidades, divisa, eur_usd)
        coste = _convertir(precio_medio * unidades, divisa_coste, eur_usd)
        ganancia = valor - coste
        ganancia_pct = (ganancia / coste * 100) if coste else 0.0

        total_actual += valor
        total_invertido += coste

        posiciones.append({
            "id": identificador,
            "nombre": nombre_propio or datos.get("nombre") or identificador,
            "nombre_oficial": datos.get("nombre"),
            "tipo": tipo,
            "unidades": unidades,
            "precio_medio": precio_medio,
            "precio_actual": datos["precio"],
            "divisa": divisa,
            "valor": valor,
            "coste": coste,
            "ganancia": ganancia,
            "ganancia_pct": ganancia_pct,
            "cambio_24h_pct": datos.get("cambio_24h_pct"),
            "divisa_compra": divisa_compra,
            "sin_datos": False,
        })

    for p in posiciones:
        if not p.get("sin_datos"):
            p["peso_pct"] = (p["valor"] / total_actual * 100) if total_actual else 0.0

    ganancia_total = total_actual - total_invertido
    ganancia_pct = (ganancia_total / total_invertido * 100) if total_invertido else 0.0

    reparto = _analizar_reparto(posiciones, total_actual)
    aportacion = _plan_aportacion(reparto, total_actual)

    return {
        "posiciones": sorted(
            [p for p in posiciones if not p.get("sin_datos")],
            key=lambda p: p["valor"], reverse=True,
        ),
        "sin_datos": [p for p in posiciones if p.get("sin_datos")],
        "total_actual": total_actual,
        "total_invertido": total_invertido,
        "ganancia": ganancia_total,
        "ganancia_pct": ganancia_pct,
        "cambio_hoy": _cambio_hoy(posiciones, total_actual),
        "reparto": reparto,
        "aportacion": aportacion,
        "conversion_incompleta": conversion_incompleta,
        "vacia": not any(not p.get("sin_datos") for p in posiciones),
    }


def _cambio_hoy(posiciones: list[dict], total: float) -> dict | None:
    """Cuánto se ha movido la cartera hoy, ponderando cada posición por su peso."""
    if not total:
        return None
    mueve = 0.0
    cubierto = 0.0
    for p in posiciones:
        if p.get("sin_datos") or p.get("cambio_24h_pct") is None:
            continue
        mueve += p["valor"] * p["cambio_24h_pct"] / 100
        cubierto += p["valor"]
    if not cubierto:
        return None
    return {
        "importe": mueve,
        "pct": mueve / cubierto * 100,
        "cobertura_pct": cubierto / total * 100,
    }


def _analizar_reparto(posiciones: list[dict], total: float) -> list[dict]:
    """Compara el peso real de cada tipo de activo con el objetivo."""
    actual: dict[str, float] = {}
    for p in posiciones:
        if p.get("sin_datos"):
            continue
        actual[p["tipo"]] = actual.get(p["tipo"], 0.0) + p["valor"]

    tipos = set(actual) | set(config.REPARTO_OBJETIVO)
    salida = []
    for tipo in sorted(tipos, key=lambda t: -config.REPARTO_OBJETIVO.get(t, 0)):
        valor = actual.get(tipo, 0.0)
        real_pct = (valor / total * 100) if total else 0.0
        objetivo_pct = float(config.REPARTO_OBJETIVO.get(tipo, 0))
        desviacion = real_pct - objetivo_pct
        objetivo_valor = total * objetivo_pct / 100

        if abs(desviacion) < config.DESVIACION_AVISO_PCT:
            estado, mensaje = "ok", "Dentro de lo previsto."
        elif desviacion > 0:
            estado = "sobre"
            mensaje = (f"Pesa {desviacion:.1f} puntos más de lo que querías. "
                       f"Son {valor - objetivo_valor:,.0f} {config.SIMBOLO_MONEDA} de más."
                       ).replace(",", ".")
        else:
            estado = "bajo"
            mensaje = (f"Pesa {abs(desviacion):.1f} puntos menos de lo que querías. "
                       f"Faltan {objetivo_valor - valor:,.0f} {config.SIMBOLO_MONEDA}."
                       ).replace(",", ".")

        salida.append({
            "tipo": tipo,
            "nombre": NOMBRES_TIPO.get(tipo, tipo.title()),
            "valor": valor,
            "real_pct": real_pct,
            "objetivo_pct": objetivo_pct,
            "desviacion": desviacion,
            "diferencia_valor": valor - objetivo_valor,
            "estado": estado,
            "mensaje": mensaje,
        })
    return salida


def _plan_aportacion(reparto: list[dict], total: float) -> dict | None:
    """
    Reparte la próxima aportación hacia lo que va por detrás del objetivo.

    Esto es rebalanceo por aportación, y para carteras pequeñas es muy superior
    a vender lo que sobra: no genera ganancias que tributen ni paga comisiones
    de venta. Simplemente compras más de lo que se ha quedado corto.
    """
    aportacion = config.APORTACION_MENSUAL
    if not aportacion or aportacion <= 0:
        return None

    nuevo_total = total + aportacion
    necesidades = []
    for r in reparto:
        objetivo_valor = nuevo_total * r["objetivo_pct"] / 100
        falta = objetivo_valor - r["valor"]
        if falta > 0:
            necesidades.append({**r, "falta": falta})

    falta_total = sum(n["falta"] for n in necesidades)

    if falta_total <= 0:
        # Todo por encima del objetivo: reparto proporcional al objetivo
        reparto_final = [
            {"tipo": r["tipo"], "nombre": r["nombre"],
             "importe": aportacion * r["objetivo_pct"] / 100,
             "pct": r["objetivo_pct"]}
            for r in reparto if r["objetivo_pct"] > 0
        ]
        nota = ("Todas las clases están en su peso o por encima. La aportación se "
                "reparte según tu objetivo, sin correcciones.")
    else:
        escala = min(1.0, aportacion / falta_total)
        reparto_final = []
        asignado = 0.0
        for n in necesidades:
            importe = n["falta"] * escala
            asignado += importe
            reparto_final.append({
                "tipo": n["tipo"], "nombre": n["nombre"],
                "importe": importe,
                "pct": importe / aportacion * 100 if aportacion else 0,
            })
        # lo que sobre (si nada se queda corto del todo) va al objetivo
        sobrante = aportacion - asignado
        if sobrante > 0.5 and reparto:
            mayor = max(reparto, key=lambda r: r["objetivo_pct"])
            existente = next((r for r in reparto_final if r["tipo"] == mayor["tipo"]), None)
            if existente:
                existente["importe"] += sobrante
                existente["pct"] = existente["importe"] / aportacion * 100
            else:
                reparto_final.append({
                    "tipo": mayor["tipo"], "nombre": mayor["nombre"],
                    "importe": sobrante, "pct": sobrante / aportacion * 100,
                })
        nota = ("La aportación va a lo que se ha quedado por detrás del objetivo. "
                "Así rebalanceas comprando, sin vender nada: no pagas comisiones de "
                "venta ni tributas por ganancias.")

    reparto_final.sort(key=lambda r: r["importe"], reverse=True)
    return {"importe": aportacion, "reparto": reparto_final, "nota": nota}


# ---------------------------------------------------------------------------
# Avisos sobre la cartera
# ---------------------------------------------------------------------------

def avisos(cartera: dict) -> list[dict]:
    """Cosas de la cartera que merecen que las mires. En el mismo formato que las señales."""
    salida: list[dict] = []
    if cartera.get("vacia"):
        return salida

    # 1. Desviaciones respecto al reparto objetivo
    for r in cartera["reparto"]:
        if r["estado"] == "ok":
            continue
        tono = "alerta" if r["estado"] == "sobre" else "neutro"
        salida.append({
            "tipo": "desviacion_cartera", "tono": tono,
            "titulo": f"{r['nombre']}: te has desviado del objetivo",
            "dato": f"{r['real_pct']:.1f}% real frente al {r['objetivo_pct']:.0f}% objetivo".replace(".", ","),
            "significa": r["mensaje"] + " Suele pasar simplemente porque una parte ha subido más que otra.",
            "ojo": ("Con carteras pequeñas casi nunca compensa vender para corregir: "
                    "las comisiones y los impuestos se comen la mejora. Corrígelo con "
                    "la próxima aportación."),
            "termino": "rebalanceo", "prioridad": 3,
        })

    # 2. Concentración excesiva en una sola posición.
    #
    # El umbral depende del tipo, y esto importa: que un ETF indexado global sea
    # el 50% de tu cartera es exactamente lo que debe pasar, no un problema. Que
    # lo sea una acción suelta o una cripto, sí. Avisar de lo primero sería un
    # mal consejo disfrazado de alerta.
    UMBRALES_CONCENTRACION = {"etf": 75, "accion": 25, "cripto": 25, "renta_fija": 80}

    for p in cartera["posiciones"][:5]:
        peso = p.get("peso_pct", 0)
        limite = UMBRALES_CONCENTRACION.get(p["tipo"], 30)
        if peso <= limite:
            continue

        if p["tipo"] == "etf":
            titulo = f"{p['nombre']} concentra casi toda tu cartera"
            significa = ("Aunque un ETF diversifica por dentro, tenerlo casi todo en un "
                         "único producto te expone a un solo emisor, un solo índice y "
                         "una sola divisa.")
        else:
            titulo = f"{p['nombre']} pesa demasiado para ser una posición individual"
            significa = ("Una sola posición manda sobre el resultado de todo lo demás. "
                         "Si le va mal, te va mal a ti sin que importe el resto.")

        salida.append({
            "tipo": "concentracion", "tono": "alerta",
            "titulo": titulo,
            "dato": f"{peso:.0f}% del total (límite sugerido para {p['tipo']}: {limite}%)".replace(".", ","),
            "significa": significa,
            "ojo": ("Concentrar no está prohibido, pero conviene que sea una decisión "
                    "consciente y no el resultado de no haber mirado en seis meses."),
            "termino": "diversificacion", "prioridad": 2,
        })

    # 3. Ticker probablemente equivocado.
    #
    # Si el precio actual se aleja muchísimo del que pagaste, lo más probable
    # NO es que hayas perdido el 90%: es que el símbolo apunta a otro activo.
    # Merece la pena distinguirlo, porque una cartera con un ticker mal puesto
    # da cifras completamente falsas y parecen creíbles.
    for p in cartera["posiciones"]:
        if not p.get("precio_medio") or not p.get("precio_actual"):
            continue
        ratio = p["precio_actual"] / p["precio_medio"]
        if 0.25 <= ratio <= 4.0:
            continue
        salida.append({
            "tipo": "ticker_sospechoso", "tono": "alerta",
            "titulo": f"¿Es correcto el identificador de {p['nombre']}?",
            "dato": (f"pagaste {p['precio_medio']:,.2f} y ahora cotiza a "
                     f"{p['precio_actual']:,.2f} ({ratio:.1f}× de diferencia)"
                     ).replace(",", "@").replace(".", ",").replace("@", "."),
            "significa": ("Una diferencia así entre tu precio de compra y el precio "
                          "actual casi siempre significa que el identificador apunta a "
                          "otro activo, no que hayas ganado o perdido tanto."),
            "ojo": (f"Compruébalo con: python3 radar.py --buscar \"{p['nombre'][:30]}\". "
                    "Si el símbolo está mal, todas las cifras de esta posición son "
                    "falsas aunque parezcan razonables."),
            "termino": None, "prioridad": 1,
        })

    # 4. Posiciones con pérdidas o ganancias grandes
    for p in cartera["posiciones"]:
        if p["ganancia_pct"] <= -25:
            salida.append({
                "tipo": "posicion_perdidas", "tono": "negativo",
                "titulo": f"{p['nombre']} acumula pérdidas importantes",
                "dato": f"{p['ganancia_pct']:+.1f}% desde tu precio medio".replace(".", ","),
                "significa": ("La posición está bastante por debajo de lo que pagaste."),
                "ojo": ("Lo que pagaste tú no le importa al mercado. La pregunta correcta "
                        "no es «cuánto llevo perdido», es «¿compraría esto hoy a este "
                        "precio?». Si la respuesta es no, el precio de compra no es un "
                        "motivo para mantenerlo."),
                "termino": "coste_hundido", "prioridad": 3,
            })
        elif p["ganancia_pct"] >= 60:
            salida.append({
                "tipo": "posicion_ganancias", "tono": "positivo",
                "titulo": f"{p['nombre']} acumula ganancias fuertes",
                "dato": f"{p['ganancia_pct']:+.1f}% desde tu precio medio".replace(".", ","),
                "significa": "La posición ha ido bien y probablemente pese ya más de lo previsto.",
                "ojo": ("Vender para consolidar ganancias hace tributar la plusvalía en el "
                        "IRPF ese mismo año. A veces compensa; a menudo, dejar correr lo "
                        "que funciona compensa más."),
                "termino": "impuestos_es", "prioridad": 4,
            })

    salida.sort(key=lambda s: s["prioridad"])
    return salida
