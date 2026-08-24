"""
Motor de señales.

Una "señal" aquí significa: ha pasado algo estadísticamente inusual que
merece que le eches un vistazo. NO significa "compra" ni "vende".

Cada señal lleva:
  • qué ha pasado (el dato)
  • qué suele significar (el contexto)
  • qué NO significa (la trampa habitual)
"""

from __future__ import annotations

from . import config

UMB = config.UMBRALES

def _n(valor: float, decimales: int = 1, signo: bool = False) -> str:
    """Número en formato español: coma decimal."""
    fmt = f"{valor:+.{decimales}f}" if signo else f"{valor:.{decimales}f}"
    return fmt.replace(".", ",")


# ---------------------------------------------------------------------------

def _señal(
    tipo: str,
    tono: str,
    titulo: str,
    dato: str,
    significa: str,
    ojo: str,
    termino: str | None = None,
    prioridad: int = 5,
) -> dict:
    return {
        "tipo": tipo,
        "tono": tono,          # positivo | negativo | neutro | alerta
        "titulo": titulo,
        "dato": dato,
        "significa": significa,
        "ojo": ojo,
        "termino": termino,    # clave del glosario para el botón "?"
        "prioridad": prioridad,
    }


# ---------------------------------------------------------------------------
# Señales por moneda
# ---------------------------------------------------------------------------

def señales_moneda(nombre: str, ind: dict, mercado: dict) -> list[dict]:
    señales: list[dict] = []

    rsi = ind.get("rsi")
    precio = ind.get("precio")
    c24 = mercado.get("price_change_percentage_24h") or 0.0

    # --- RSI -------------------------------------------------------------
    if rsi is not None:
        if rsi < UMB.rsi_sobreventa:
            señales.append(_señal(
                "rsi_bajo", "positivo",
                f"{nombre} está sobrevendido",
                f"RSI en {rsi:.0f} (por debajo de 30)",
                "Ha caído rápido. Históricamente, desde estos niveles suele haber rebotes técnicos.",
                "Que algo esté sobrevendido no impide que siga cayendo. Busca la noticia antes de asumir que es una rebaja.",
                termino="rsi", prioridad=2,
            ))
        elif rsi > UMB.rsi_sobrecompra:
            señales.append(_señal(
                "rsi_alto", "alerta",
                f"{nombre} está sobrecomprado",
                f"RSI en {rsi:.0f} (por encima de 70)",
                "Ha subido rápido y el movimiento está estirado.",
                "En tendencias alcistas fuertes el RSI puede quedarse semanas por encima de 70 mientras sigue subiendo. No es una señal de venta.",
                termino="rsi", prioridad=3,
            ))

    # --- Movimiento diario fuerte ----------------------------------------
    if c24 <= UMB.caida_fuerte_24h:
        señales.append(_señal(
            "caida_fuerte", "alerta",
            f"{nombre} se ha desplomado hoy",
            f"{_n(c24, 1, True)}% en 24 horas",
            "Movimiento grande en un día. Casi siempre hay una causa concreta detrás.",
            "Lo primero es buscar la noticia. Comprar caídas sin saber por qué han caído es cómo se pierde dinero rápido.",
            prioridad=1,
        ))
    elif c24 >= UMB.subida_fuerte_24h:
        señales.append(_señal(
            "subida_fuerte", "positivo",
            f"{nombre} sube con fuerza hoy",
            f"{_n(c24, 1, True)}% en 24 horas",
            "Movimiento grande al alza. Mira el volumen para saber si hay convicción detrás.",
            "Perseguir una vela verde es la forma más común de comprar caro. Si te lo has perdido, te lo has perdido.",
            prioridad=3,
        ))

    # --- Cruce de medias --------------------------------------------------
    cruce = ind.get("cruce_medias")
    if cruce == "alcista":
        señales.append(_señal(
            "cruce_alcista", "positivo",
            f"{nombre}: cruce alcista de medias",
            "La media de 20 días ha cruzado por encima de la de 50",
            "El impulso de corto plazo está superando al de medio plazo. Suele acompañar el inicio de tramos alcistas.",
            "Genera muchas señales falsas en mercados laterales. Es contexto, no un disparador.",
            termino="cruce_medias", prioridad=3,
        ))
    elif cruce == "bajista":
        señales.append(_señal(
            "cruce_bajista", "negativo",
            f"{nombre}: cruce bajista de medias",
            "La media de 20 días ha cruzado por debajo de la de 50",
            "El impulso de corto plazo se está deteriorando.",
            "Igual que el alcista: en lateral falla mucho. No vendas solo por esto.",
            termino="cruce_medias", prioridad=4,
        ))

    # --- Tendencia de fondo (SMA 200) ------------------------------------
    dist200 = ind.get("dist_sma200_pct")
    if dist200 is not None:
        if -3 <= dist200 <= 3:
            señales.append(_señal(
                "toca_sma200", "neutro",
                f"{nombre} está tocando su media de 200 días",
                f"A un {_n(dist200, 1, True)}% de la SMA 200",
                "La media de 200 días es la referencia de tendencia de largo plazo más vigilada del mercado. Que el precio la toque suele generar reacción.",
                "Que reaccione no dice en qué dirección. Es un nivel donde pasan cosas, no una predicción.",
                termino="sma", prioridad=2,
            ))
        elif dist200 < -25:
            señales.append(_señal(
                "bajo_sma200", "negativo",
                f"{nombre} muy por debajo de su tendencia de largo plazo",
                f"A un {_n(dist200, 0)}% de la SMA 200",
                "La tendencia de fondo es bajista con claridad.",
                "Lejos de la media también significa que un rebote hacia ella sería grande. No implica que vaya a ocurrir.",
                termino="sma", prioridad=4,
            ))

    # --- Volumen anómalo --------------------------------------------------
    volrel = ind.get("volumen_relativo")
    if volrel and volrel >= UMB.volumen_anomalo:
        señales.append(_señal(
            "volumen_anomalo", "neutro",
            f"{nombre}: volumen inusual",
            f"{_n(volrel, 1)}× el volumen medio del último mes",
            "Ha entrado dinero de verdad. Los movimientos con volumen alto tienden a sostenerse; los que van sin volumen suelen revertirse.",
            "El volumen alto no dice la dirección. Solo dice que hay convicción, sea de compradores o de vendedores.",
            termino="volumen_relativo", prioridad=2,
        ))

    # --- Posición en el rango --------------------------------------------
    niveles = ind.get("niveles")
    if niveles:
        pos = niveles["posicion_en_rango_pct"]
        if pos <= 12:
            señales.append(_señal(
                "cerca_soporte", "positivo",
                f"{nombre} cerca del suelo de su rango de 90 días",
                f"Posición {_n(pos, 0)}% del rango (soporte {_n(niveles['soporte'], 2)} {config.SIMBOLO_MONEDA})",
                "Está en la zona baja de los últimos tres meses, donde históricamente han aparecido compradores.",
                "Los soportes se rompen constantemente. Que haya frenado ahí antes no obliga a que frene ahora.",
                termino="soporte_resistencia", prioridad=2,
            ))
        elif pos >= 92:
            señales.append(_señal(
                "cerca_resistencia", "alerta",
                f"{nombre} cerca del techo de su rango de 90 días",
                f"Posición {_n(pos, 0)}% del rango (resistencia {_n(niveles['resistencia'], 2)} {config.SIMBOLO_MONEDA})",
                "Está en la zona alta de los últimos tres meses, donde suele aparecer papel vendedor.",
                "Si la rompe con volumen, la resistencia pasa a ser soporte y el movimiento puede acelerar. Funciona en los dos sentidos.",
                termino="soporte_resistencia", prioridad=3,
            ))

    # --- MACD -------------------------------------------------------------
    macd = ind.get("macd") or {}
    if macd.get("cruce_reciente") == "alcista":
        señales.append(_señal(
            "macd_alcista", "positivo",
            f"{nombre}: MACD gira al alza",
            "La línea MACD ha cruzado por encima de su señal",
            "El impulso está mejorando en el corto plazo.",
            "El MACD llega tarde por construcción: usa medias, y las medias miran al pasado.",
            termino="macd", prioridad=4,
        ))
    elif macd.get("cruce_reciente") == "bajista":
        señales.append(_señal(
            "macd_bajista", "negativo",
            f"{nombre}: MACD gira a la baja",
            "La línea MACD ha cruzado por debajo de su señal",
            "El impulso de corto plazo se está apagando.",
            "Igual de retrasado que el alcista. Contexto, no orden.",
            termino="macd", prioridad=4,
        ))

    # --- Volatilidad ------------------------------------------------------
    vol = ind.get("volatilidad_pct")
    if vol and vol > UMB.volatilidad_alta:
        señales.append(_señal(
            "volatilidad_alta", "alerta",
            f"{nombre} está muy volátil",
            f"Volatilidad anualizada del {_n(vol, 0)}%",
            "Con esta volatilidad, movimientos diarios del 8-10% entran dentro de lo normal.",
            "Esto es lo que debería determinar cuánto dinero metes, más que ninguna señal técnica.",
            termino="volatilidad", prioridad=3,
        ))

    señales.sort(key=lambda s: s["prioridad"])
    return señales


# ---------------------------------------------------------------------------
# Lectura del mercado global
# ---------------------------------------------------------------------------

def leer_mercado_global(glob: dict | None, fng: list[dict], mercado: list[dict]) -> dict:
    resumen = {
        "cap_total": None,
        "cambio_24h": None,
        "dominancia_btc": None,
        "fng_valor": None,
        "fng_etiqueta": None,
        "fng_serie": [],
        "titular": "",
        "detalle": "",
        "tono": "neutro",
        "amplitud": None,
    }

    if glob:
        resumen["cap_total"] = (glob.get("total_market_cap") or {}).get(config.MONEDA)
        resumen["cambio_24h"] = glob.get("market_cap_change_percentage_24h_usd")
        resumen["dominancia_btc"] = (glob.get("market_cap_percentage") or {}).get("btc")

    if fng:
        try:
            resumen["fng_valor"] = int(fng[0]["value"])
            resumen["fng_etiqueta"] = _traducir_fng(fng[0].get("value_classification", ""))
            resumen["fng_serie"] = [int(d["value"]) for d in reversed(fng[:30])]
        except (ValueError, KeyError, TypeError):
            pass

    # Amplitud: qué porcentaje del top sube hoy. Dice más que el índice.
    con_dato = [m for m in mercado if m.get("price_change_percentage_24h") is not None]
    if con_dato:
        suben = sum(1 for m in con_dato if m["price_change_percentage_24h"] > 0)
        resumen["amplitud"] = suben / len(con_dato) * 100

    cambio = resumen["cambio_24h"] or 0.0
    amplitud = resumen["amplitud"]
    fng_v = resumen["fng_valor"]

    if cambio > 3:
        resumen["titular"] = "Día claramente alcista"
        resumen["tono"] = "positivo"
    elif cambio > 0.5:
        resumen["titular"] = "Día positivo"
        resumen["tono"] = "positivo"
    elif cambio > -0.5:
        resumen["titular"] = "Mercado plano"
        resumen["tono"] = "neutro"
    elif cambio > -3:
        resumen["titular"] = "Día negativo"
        resumen["tono"] = "negativo"
    else:
        resumen["titular"] = "Caída generalizada"
        resumen["tono"] = "negativo"

    partes = []
    if amplitud is not None:
        if amplitud > 75:
            partes.append(f"Sube el {amplitud:.0f}% del top: el movimiento es de todo el mercado, no de una moneda suelta.")
        elif amplitud < 25:
            partes.append(f"Solo sube el {amplitud:.0f}% del top: la caída es generalizada.")
        else:
            partes.append(f"Sube el {amplitud:.0f}% del top: mercado dividido, cada proyecto va por su cuenta.")

    if fng_v is not None:
        if fng_v < 25:
            partes.append("El índice de miedo y codicia marca miedo extremo. Históricamente son las zonas donde a la gente le cuesta más comprar y donde mejor ha funcionado hacerlo.")
        elif fng_v > 75:
            partes.append("El índice marca codicia extrema. Históricamente son las zonas donde más fácil parece todo y peores han sido las entradas.")
        else:
            partes.append(f"El sentimiento está en {fng_v}/100, en zona intermedia.")

    dom = resumen["dominancia_btc"]
    if dom is not None:
        if dom > 58:
            partes.append(f"Bitcoin domina el {dom:.1f}% del mercado: el dinero está concentrado en BTC y las altcoins lo tienen difícil.")
        elif dom < 48:
            partes.append(f"La dominancia de Bitcoin está en el {dom:.1f}%: el dinero se está repartiendo hacia altcoins.")
        else:
            partes.append(f"Dominancia de Bitcoin en el {dom:.1f}%, en su rango habitual.")

    resumen["detalle"] = " ".join(partes)
    return resumen


def _traducir_fng(etiqueta: str) -> str:
    return {
        "Extreme Fear": "Miedo extremo",
        "Fear": "Miedo",
        "Neutral": "Neutral",
        "Greed": "Codicia",
        "Extreme Greed": "Codicia extrema",
    }.get(etiqueta, etiqueta)


def destacados_del_dia(mercado: list[dict], n: int = 5) -> dict:
    """Los que más suben y más bajan del top escaneado."""
    con_dato = [m for m in mercado if m.get("price_change_percentage_24h") is not None]
    ordenado = sorted(con_dato, key=lambda m: m["price_change_percentage_24h"], reverse=True)
    return {"suben": ordenado[:n], "bajan": list(reversed(ordenado[-n:]))}
