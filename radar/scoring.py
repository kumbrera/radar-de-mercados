"""
Scoring de proyectos cripto.

Filosofía: nada de cajas negras. Cada punto que suma o resta lleva su
explicación en texto plano, para que puedas discrepar del sistema con
argumentos en vez de fiarte de un número.

La nota final NO es una recomendación de compra. Es un filtro: convierte
"250 monedas que no puedo revisar" en "10 monedas que merecen una tarde
de investigación".
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import config


def _clamp(valor: float, minimo: float = 0.0, maximo: float = 100.0) -> float:
    return max(minimo, min(maximo, valor))


def _escala(valor: float, malo: float, bueno: float) -> float:
    """Convierte un valor a una nota 0-100 interpolando entre 'malo' y 'bueno'."""
    if bueno == malo:
        return 50.0
    return _clamp((valor - malo) / (bueno - malo) * 100.0)


# ---------------------------------------------------------------------------
# Bloques del scoring
# ---------------------------------------------------------------------------

def _puntuar_liquidez(mercado: dict) -> dict:
    mcap = mercado.get("market_cap") or 0
    volumen = mercado.get("total_volume") or 0
    ratio = (volumen / mcap * 100) if mcap else 0.0

    # Lo sano está entre el 2% y el 20%. Ni muerto ni frenesí.
    if ratio < 0.5:
        nota = _escala(ratio, 0, 0.5) * 0.35
        texto = f"Muy poca actividad: solo el {ratio:.2f}% del proyecto se mueve al día. Cuesta entrar y salir."
    elif ratio <= 20:
        nota = 55 + _escala(min(ratio, 8), 0.5, 8) * 0.45
        texto = f"Liquidez sana: el {ratio:.1f}% de la capitalización se negocia cada día."
    elif ratio <= 60:
        nota = 65.0
        texto = f"Actividad muy alta ({ratio:.0f}% al día). Hay mucho especulador dentro."
    else:
        nota = 25.0
        texto = f"Volumen anómalo: {ratio:.0f}% de la capitalización al día. Sospechoso."

    # Un volumen absoluto minúsculo es un problema aunque el ratio esté bien
    if volumen < config.VOLUMEN_MIN_24H:
        nota *= 0.5
        texto += " Volumen absoluto demasiado bajo para operar con comodidad."

    return {"nota": _clamp(nota), "texto": texto, "ratio_vol_mcap": ratio}


def _puntuar_desarrollo(ficha: dict | None) -> dict:
    dev = (ficha or {}).get("developer_data") or {}

    commits = dev.get("commit_count_4_weeks")
    estrellas = dev.get("stars") or 0
    contribuidores = dev.get("pull_request_contributors") or 0
    issues_total = dev.get("total_issues") or 0
    issues_cerrados = dev.get("closed_issues") or 0

    if not any([commits, estrellas, contribuidores]):
        return {
            "nota": 50.0,
            "texto": "Sin datos de GitHub. Puede que el repositorio no esté enlazado en CoinGecko, no que el proyecto esté muerto.",
            "sin_datos": True,
            "commits_4s": None,
        }

    # Commits del último mes: el indicador más directo de si hay vida
    nota_commits = _escala(commits or 0, 0, 60)
    nota_contrib = _escala(contribuidores, 0, 60)
    nota_estrellas = _escala(estrellas, 0, 8000)
    ratio_issues = (issues_cerrados / issues_total * 100) if issues_total else 50.0
    nota_issues = _escala(ratio_issues, 30, 90)

    nota = (nota_commits * 0.45 + nota_contrib * 0.25
            + nota_estrellas * 0.20 + nota_issues * 0.10)

    if commits == 0:
        texto = "Cero commits en las últimas 4 semanas. O está terminado y estable, o está abandonado."
    elif (commits or 0) < 10:
        texto = f"Desarrollo lento: {commits} commits en 4 semanas, {contribuidores} contribuidores."
    else:
        texto = f"Desarrollo activo: {commits} commits en 4 semanas, {contribuidores} contribuidores, {estrellas:,} estrellas."

    return {
        "nota": _clamp(nota),
        "texto": texto.replace(",", "."),
        "sin_datos": False,
        "commits_4s": commits,
    }


def _puntuar_comunidad(ficha: dict | None) -> dict:
    com = (ficha or {}).get("community_data") or {}
    twitter = com.get("twitter_followers") or 0
    reddit = com.get("reddit_subscribers") or 0
    telegram = com.get("telegram_channel_user_count") or 0

    if not any([twitter, reddit, telegram]):
        return {"nota": 50.0, "texto": "Sin datos de comunidad disponibles."}

    nota = (
        _escala(twitter, 0, 400_000) * 0.5
        + _escala(reddit, 0, 150_000) * 0.3
        + _escala(telegram, 0, 60_000) * 0.2
    )
    texto = (f"Comunidad: {twitter:,} en X, {reddit:,} en Reddit."
             .replace(",", "."))
    if nota < 30:
        texto += " Base de seguidores pequeña."
    return {"nota": _clamp(nota), "texto": texto}


def _puntuar_momento(mercado: dict, tendencias_ids: set[str]) -> dict:
    c7 = mercado.get("price_change_percentage_7d_in_currency") or 0.0
    c30 = mercado.get("price_change_percentage_30d_in_currency") or 0.0

    # Buscamos impulso positivo pero NO parabólico: lo parabólico ya se ha ido
    if c30 > 150:
        nota = 20.0
        texto = f"Ha subido un {c30:+.0f}% en 30 días. Comprar después de esto suele ser comprar el techo."
    elif c30 > 60:
        nota = 55.0
        texto = f"Impulso fuerte ({c30:+.0f}% en 30 días). Llega tarde, pero la tendencia es clara."
    elif c30 > 5:
        nota = 85.0
        texto = f"Impulso sano y sostenible: {c30:+.0f}% en 30 días."
    elif c30 > -25:
        nota = 60.0
        texto = f"Lateral o corrigiendo ({c30:+.0f}% en 30 días). Ni frío ni calor."
    else:
        nota = 40.0
        texto = f"Cayendo con fuerza ({c30:+.0f}% en 30 días). Puede ser rebaja o puede ser deterioro real."

    # La aceleración de última semana matiza
    if c7 > 0 and c30 < 0:
        nota += 10
        texto += " Pero la última semana ha girado al alza."

    if mercado.get("id") in tendencias_ids:
        nota += 5
        texto += " Está entre lo más buscado en CoinGecko ahora mismo."

    return {"nota": _clamp(nota), "texto": texto}


def _puntuar_valoracion(mercado: dict) -> dict:
    desde_ath = mercado.get("ath_change_percentage")
    if desde_ath is None:
        return {"nota": 50.0, "texto": "Sin dato de máximo histórico."}

    # Cuanto más lejos del ATH, más margen teórico. Pero el extremo también avisa.
    if desde_ath > -15:
        nota = 30.0
        texto = f"A un {abs(desde_ath):.0f}% de su máximo histórico. Poco margen y mucha gente en ganancias esperando vender."
    elif desde_ath > -50:
        nota = 65.0
        texto = f"Un {abs(desde_ath):.0f}% por debajo de su máximo histórico. Corrección normal."
    elif desde_ath > -85:
        nota = 85.0
        texto = f"Un {abs(desde_ath):.0f}% por debajo de máximos. De rebajas, si el proyecto sigue vivo."
    else:
        nota = 45.0
        texto = f"Un {abs(desde_ath):.0f}% por debajo de máximos. Recuperar eso exigiría un x{1/(1+desde_ath/100):.0f}. Suele indicar que el mercado ha pasado página."

    return {"nota": _clamp(nota), "texto": texto, "desde_ath": desde_ath}


def _puntuar_tokenomics(mercado: dict, ficha: dict | None) -> dict:
    circulante = mercado.get("circulating_supply") or 0
    total = mercado.get("total_supply") or 0
    if not total and ficha:
        total = ((ficha.get("market_data") or {}).get("total_supply")) or 0

    if not circulante or not total:
        return {"nota": 50.0, "texto": "Sin datos de supply suficientes.", "pct_circulante": None}

    pct = circulante / total * 100

    if pct >= 90:
        nota, texto = 95.0, f"El {pct:.0f}% del supply ya circula. Casi no queda dilución pendiente."
    elif pct >= 70:
        nota, texto = 78.0, f"Circula el {pct:.0f}%. Queda algo de dilución, pero controlada."
    elif pct >= 45:
        nota, texto = 52.0, f"Solo circula el {pct:.0f}%. Habrá desbloqueos relevantes en los próximos años."
    elif pct >= 25:
        nota, texto = 30.0, f"Solo circula el {pct:.0f}%. Presión vendedora futura importante."
    else:
        nota, texto = 12.0, f"Solo circula el {pct:.0f}%. El {100-pct:.0f}% restante entrará al mercado con el tiempo: dilución muy fuerte."

    return {"nota": nota, "texto": texto, "pct_circulante": pct}


# ---------------------------------------------------------------------------
# Red flags
# ---------------------------------------------------------------------------

def _detectar_red_flags(mercado: dict, ficha: dict | None, bloques: dict) -> list[dict]:
    flags = []
    rf = config.RED_FLAGS

    ratio = bloques["liquidez"].get("ratio_vol_mcap", 0)
    if ratio > rf.ratio_volumen_mcap_sospechoso * 100:
        flags.append({
            "tipo": "Volumen sospechoso",
            "penalizacion": 15,
            "detalle": (f"El volumen diario es {ratio/100:.1f} veces la capitalización. "
                        "Puede ser wash trading (volumen inflado artificialmente)."),
        })

    pct = bloques["tokenomics"].get("pct_circulante")
    if pct is not None and pct < rf.circulante_minimo_pct:
        flags.append({
            "tipo": "Poco supply circulante",
            "penalizacion": 12,
            "detalle": (f"Solo circula el {pct:.0f}%. Los desbloqueos futuros son oferta "
                        "nueva que presiona el precio a la baja."),
        })

    c30 = mercado.get("price_change_percentage_30d_in_currency") or 0
    if c30 > rf.pump_30d_peligroso:
        flags.append({
            "tipo": "Subida parabólica",
            "penalizacion": 15,
            "detalle": (f"{c30:+.0f}% en 30 días. Estadísticamente, entrar después de un "
                        "movimiento así acaba mal más veces de las que acaba bien."),
        })

    dev = bloques["desarrollo"]
    if not dev.get("sin_datos") and dev.get("commits_4s") == 0:
        flags.append({
            "tipo": "Desarrollo parado",
            "penalizacion": 12,
            "detalle": "Cero commits en 4 semanas. Comprueba si el proyecto sigue mantenido.",
        })

    mcap = mercado.get("market_cap") or 0
    if 0 < mcap < config.MCAP_MIN:
        flags.append({
            "tipo": "Capitalización muy pequeña",
            "penalizacion": 8,
            "detalle": "Por debajo de 40 M el precio se manipula con relativamente poco dinero.",
        })

    return flags


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------

def puntuar_proyecto(
    mercado: dict,
    ficha: dict | None = None,
    tendencias_ids: set[str] | None = None,
) -> dict:
    """
    Devuelve la nota (0-10) y el desglose completo y explicado de un proyecto.
    """
    tendencias_ids = tendencias_ids or set()

    bloques = {
        "liquidez": _puntuar_liquidez(mercado),
        "desarrollo": _puntuar_desarrollo(ficha),
        "comunidad": _puntuar_comunidad(ficha),
        "momento": _puntuar_momento(mercado, tendencias_ids),
        "valoracion": _puntuar_valoracion(mercado),
        "tokenomics": _puntuar_tokenomics(mercado, ficha),
    }

    bruto = sum(bloques[k]["nota"] * config.PESOS_SCORING[k] for k in bloques) / 100.0

    flags = _detectar_red_flags(mercado, ficha, bloques)
    penalizacion = sum(f["penalizacion"] for f in flags)
    final = _clamp(bruto - penalizacion)

    nota10 = round(final / 10.0, 1)

    if nota10 >= 7.0:
        nivel, color = "Merece investigación", "verde"
    elif nota10 >= 5.5:
        nivel, color = "Interesante con reservas", "ambar"
    elif nota10 >= 4.0:
        nivel, color = "Riesgo alto", "naranja"
    else:
        nivel, color = "Descartado por ahora", "rojo"

    return {
        "id": mercado.get("id"),
        "nombre": mercado.get("name"),
        "simbolo": (mercado.get("symbol") or "").upper(),
        "nota": nota10,
        "nota_bruta": round(bruto / 10.0, 1),
        "nivel": nivel,
        "color": color,
        "bloques": bloques,
        "red_flags": flags,
        "penalizacion_total": penalizacion,
        "categorias": (ficha or {}).get("categories") or [],
        "edad_dias": _edad_en_dias(ficha),
        "mercado": mercado,
    }


def _edad_en_dias(ficha: dict | None) -> int | None:
    genesis = (ficha or {}).get("genesis_date")
    if not genesis:
        return None
    try:
        fecha = datetime.strptime(genesis, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - fecha).days
    except ValueError:
        return None


def filtrar_candidatos(mercado: list[dict]) -> list[dict]:
    """
    Primer filtro, antes de gastar peticiones a la API pidiendo fichas.

    Se queda con lo que está en el rango de capitalización que nos interesa y
    tiene volumen suficiente para poder operar.
    """
    salida = []
    for m in mercado:
        mcap = m.get("market_cap") or 0
        vol = m.get("total_volume") or 0
        if not (config.MCAP_MIN <= mcap <= config.MCAP_MAX):
            continue
        if vol < config.VOLUMEN_MIN_24H:
            continue
        salida.append(m)
    return salida
