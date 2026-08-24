"""
Orquestador: recoge los datos, calcula, puntúa y devuelve todo listo
para que report.py lo dibuje.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from . import (bolsa as mod_bolsa, cartera as mod_cartera, config, indicators,
               resolver as mod_resolver, scoring, scoring_bolsa, signals,
               signals_bolsa)
from .sources import obtener_fuente

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fecha_larga(dt: datetime) -> str:
    return f"{DIAS[dt.weekday()]} {dt.day} de {MESES[dt.month - 1]} de {dt.year}, {dt:%H:%M}"


def _fecha_corta(dt: datetime) -> str:
    return f"{dt.day} de {MESES[dt.month - 1]} de {dt.year}"


# ---------------------------------------------------------------------------
# Histórico local (para poder comparar informes entre días)
# ---------------------------------------------------------------------------

def _abrir_bd() -> sqlite3.Connection:
    con = sqlite3.connect(config.FICHERO_HISTORICO)
    con.execute("""CREATE TABLE IF NOT EXISTS lecturas (
        fecha TEXT, moneda TEXT, precio REAL, rsi REAL, mcap REAL,
        volumen REAL, nota REAL,
        PRIMARY KEY (fecha, moneda))""")
    con.execute("""CREATE TABLE IF NOT EXISTS senales (
        fecha TEXT, moneda TEXT, tipo TEXT, titulo TEXT, dato TEXT)""")
    return con


def _guardar_historico(con: sqlite3.Connection, fecha: str, watchlist: list[dict],
                       proyectos: list[dict]) -> None:
    for m in watchlist:
        ind, mer = m["indicadores"], m["mercado"]
        con.execute(
            "INSERT OR REPLACE INTO lecturas VALUES (?,?,?,?,?,?,?)",
            (fecha, mer.get("id"), ind.get("precio"), ind.get("rsi"),
             mer.get("market_cap"), mer.get("total_volume"), None),
        )
        for s in m.get("señales", []):
            con.execute("INSERT INTO senales VALUES (?,?,?,?,?)",
                        (fecha, mer.get("id"), s["tipo"], s["titulo"], s["dato"]))
    for p in proyectos:
        mer = p["mercado"]
        con.execute(
            "INSERT OR REPLACE INTO lecturas VALUES (?,?,?,?,?,?,?)",
            (fecha, mer.get("id"), mer.get("current_price"), None,
             mer.get("market_cap"), mer.get("total_volume"), p["nota"]),
        )
    con.commit()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def ejecutar(
    demo: bool = False,
    usar_cache: bool = True,
    verbose: bool = True,
    max_proyectos_analizados: int = 18,
) -> dict:
    ahora = datetime.now()
    fuente = obtener_fuente(demo=demo, usar_cache=usar_cache, verbose=verbose)

    def log(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    # -- 1. Foto general del mercado ---------------------------------------
    log("→ Leyendo estado global del mercado...")
    glob = fuente.estado_global()
    fng = fuente.miedo_codicia(30)

    log(f"→ Descargando el top {config.TOP_A_ESCANEAR} por capitalización...")
    mercado: list[dict] = []
    for pagina in range(1, (config.TOP_A_ESCANEAR // 250) + 2):
        lote = fuente.mercado(por_pagina=250, pagina=pagina)
        if not lote:
            break
        mercado.extend(lote)
        if len(mercado) >= config.TOP_A_ESCANEAR:
            break
    mercado = mercado[: config.TOP_A_ESCANEAR]
    log(f"  {len(mercado)} monedas descargadas.")

    if not mercado:
        raise RuntimeError(
            "No se ha podido descargar el mercado. Comprueba tu conexión "
            "o prueba con --demo para ver el sistema funcionando sin internet."
        )

    por_id = {m["id"]: m for m in mercado}
    tendencias = fuente.tendencias()
    tendencias_ids = {t.get("id") for t in tendencias if t.get("id")}

    lectura_global = signals.leer_mercado_global(glob, fng, mercado)
    destacados = signals.destacados_del_dia(mercado, 6)

    # -- 2. Análisis profundo de tu watchlist -------------------------------
    log(f"→ Analizando tus {len(config.WATCHLIST)} criptos...")
    watchlist = []
    alertas = []
    for moneda_id in config.WATCHLIST:
        mer = por_id.get(moneda_id)
        if mer is None:
            mer = next((m for m in mercado if m.get("id") == moneda_id), None)
        if mer is None:
            log(f"  · {moneda_id}: no está en el top escaneado, se omite.")
            continue

        hist = fuente.historico(moneda_id, dias=365)
        if not hist or len(hist["precios"]) < 30:
            log(f"  · {moneda_id}: sin histórico suficiente, se omite.")
            continue

        ind = indicators.analizar(hist["precios"], hist.get("volumenes"))
        sus_señales = signals.señales_moneda(mer.get("name") or moneda_id, ind, mer)

        watchlist.append({"mercado": mer, "indicadores": ind, "señales": sus_señales})
        alertas.extend(s for s in sus_señales if s["prioridad"] <= 2)
        log(f"  · {mer.get('name')}: RSI {ind.get('rsi') or float('nan'):.0f}, "
            f"{len(sus_señales)} señal(es)")

    alertas.sort(key=lambda s: s["prioridad"])

    # -- 3. Descubrimiento y scoring de proyectos ---------------------------
    log("→ Buscando proyectos que cumplan los criterios...")
    candidatos = scoring.filtrar_candidatos(mercado)
    log(f"  {len(candidatos)} candidatos pasan el filtro de capitalización y volumen.")

    # Preordenamos por una nota rápida sin ficha, para gastar peticiones solo
    # en los que tienen alguna posibilidad de acabar en el informe.
    preliminares = [
        (scoring.puntuar_proyecto(c, None, tendencias_ids)["nota"], c)
        for c in candidatos
    ]
    preliminares.sort(key=lambda x: x[0], reverse=True)
    a_analizar = [c for _n, c in preliminares[:max_proyectos_analizados]]

    log(f"→ Pidiendo ficha completa de los {len(a_analizar)} mejor situados...")
    proyectos = []
    for c in a_analizar:
        ficha = fuente.ficha(c["id"])
        p = scoring.puntuar_proyecto(c, ficha, tendencias_ids)
        proyectos.append(p)
        log(f"  · {p['nombre']}: {p['nota']}/10 ({p['nivel']})")

    proyectos.sort(key=lambda p: p["nota"], reverse=True)
    proyectos = proyectos[: config.MAX_PROYECTOS_INFORME]

    # -- 4. Bolsa: índices, ETFs y acciones ---------------------------------
    nombres_propios = {p[0]: p[5] for p in config.POSICIONES
                       if len(p) > 5 and p[5]}
    datos_bolsa = _ejecutar_bolsa(demo=demo, usar_cache=usar_cache, verbose=verbose,
                                  nombres_propios=nombres_propios)
    alertas.extend(datos_bolsa.pop("alertas", []))

    # -- 5. Cartera ---------------------------------------------------------
    log("→ Calculando tu cartera...")

    # Si un símbolo se ha tenido que rescatar (por ejemplo, has puesto el código
    # que enseña tu bróker y no existe en Yahoo), la posición tiene que apuntar
    # al símbolo que sí ha funcionado.
    remapeos = datos_bolsa.get("remapeos") or {}
    if remapeos:
        config.POSICIONES = [
            (remapeos.get(f[0], f[0]), *f[1:]) for f in config.POSICIONES
        ]

    precios = _reunir_precios(watchlist, proyectos, datos_bolsa)
    eur_usd = datos_bolsa.get("eur_usd")
    la_cartera = mod_cartera.construir(precios, eur_usd)
    la_cartera["avisos_csv"] = (list(getattr(config, "AVISOS_CARTERA", []))
                                + list(datos_bolsa.get("avisos_resolucion") or []))
    la_cartera["traducciones"] = datos_bolsa.get("traducciones") or {}
    for aviso in la_cartera["avisos_csv"]:
        log(f"  ! cartera.csv -> {aviso}")
    alertas.extend(mod_cartera.avisos(la_cartera))
    if la_cartera.get("vacia"):
        log("  Sin posiciones apuntadas en config.POSICIONES.")
    else:
        log(f"  {len(la_cartera['posiciones'])} posiciones · "
            f"{la_cartera['total_actual']:,.2f} {config.SIMBOLO_MONEDA} · "
            f"{la_cartera['ganancia_pct']:+.1f}%".replace(",", "."))

    alertas.sort(key=lambda s: s["prioridad"])

    # -- 6. Guardar histórico ----------------------------------------------
    try:
        con = _abrir_bd()
        _guardar_historico(con, ahora.strftime("%Y-%m-%d"), watchlist, proyectos)
        _guardar_cartera(con, ahora.strftime("%Y-%m-%d"), la_cartera)
        con.close()
    except sqlite3.Error as e:
        log(f"  ! No se pudo guardar el histórico: {e}")

    peticiones = fuente.peticiones_hechas + datos_bolsa.get("peticiones", 0)
    fallos = list(fuente.fallos) + list(datos_bolsa.get("fallos", []))

    return {
        "meta": {
            "fecha_larga": _fecha_larga(ahora),
            "fecha_corta": _fecha_corta(ahora),
            "peticiones": peticiones,
            "modo": "Datos de demostración (sin conexión)" if demo else "Datos reales",
            "fallos": fallos,
        },
        "global": lectura_global,
        "alertas": alertas,
        "watchlist": watchlist,
        "proyectos": proyectos,
        "destacados": destacados,
        "tendencias": tendencias,
        "bolsa": datos_bolsa,
        "cartera": la_cartera,
    }


# ---------------------------------------------------------------------------
# Bolsa
# ---------------------------------------------------------------------------

def _ejecutar_bolsa(demo: bool, usar_cache: bool, verbose: bool,
                    nombres_propios: dict | None = None) -> dict:
    nombres_propios = dict(nombres_propios or {})
    def log(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    fuente = mod_bolsa.obtener_fuente_bolsa(demo=demo, usar_cache=usar_cache, verbose=verbose)
    alertas: list[dict] = []

    # -- traducir ISINs y nombres a símbolos --------------------------------
    #
    # En cartera.csv puedes escribir el ISIN (que es lo que ves en tu bróker) o
    # el nombre del activo. Aquí se convierte a símbolo de Yahoo antes de pedir
    # nada, y la traducción se guarda para no repetirla cada día.
    traducciones: dict = {}
    avisos_resolucion: list[str] = []
    remapeos: dict = {}
    if config.POSICIONES:
        pendientes = [p for p in config.POSICIONES
                      if p[1] != "cripto" and not mod_resolver.parece_simbolo(p[0])]
        if pendientes:
            log(f"→ Traduciendo {len(pendientes)} identificador(es) a símbolos...")
        config.POSICIONES, traducciones, avisos_resolucion = \
            mod_resolver.resolver_posiciones(config.POSICIONES, fuente, verbose)

        # Tras la traducción, los nombres que escribiste hay que reindexarlos
        # por el símbolo ya resuelto, no por el ISIN original.
        nombres_propios = dict(nombres_propios or {})
        for fila in config.POSICIONES:
            if len(fila) > 5 and fila[5]:
                nombres_propios[fila[0]] = fila[5]

        # Que lo que sigues coincida con lo que tienes, sin duplicados
        for simbolo, tipo, *_ in config.POSICIONES:
            destino = (config.WATCHLIST_ETFS if tipo == "etf"
                       else config.WATCHLIST_ACCIONES if tipo == "accion" else None)
            if destino is not None and simbolo not in destino:
                destino.append(simbolo)

    # -- índices de referencia ---------------------------------------------
    log(f"→ Leyendo los {len(config.INDICES)} índices de referencia...")
    indices = []
    for simbolo, nombre in config.INDICES:
        hist = fuente.historico(simbolo, rango="2y")
        if not hist:
            log(f"  · {nombre}: sin datos, se omite.")
            continue
        ind = indicators.analizar_bolsa(hist["precios"], hist.get("volumenes"))
        indices.append({"simbolo": simbolo, "nombre": nombre,
                        "indicadores": ind, "meta": hist})

    lectura = signals_bolsa.leer_bolsa(indices) if indices else None
    eur_usd = (lectura or {}).get("eur_usd")

    # Un índice que se mueve mucho también es una alerta
    for i in indices:
        if i["simbolo"] in ("^VIX", "EURUSD=X"):
            continue
        for s in signals_bolsa.señales_valor(i["nombre"], i["indicadores"], {}, es_etf=True):
            if s["prioridad"] <= 2:
                alertas.append(s)

    # -- ETFs ---------------------------------------------------------------
    log(f"→ Analizando tus {len(config.WATCHLIST_ETFS)} ETFs...")
    etfs = []
    for simbolo in config.WATCHLIST_ETFS:
        hist = fuente.historico(simbolo, rango="5y")
        if not hist:
            nuevo, hist = _rescatar(simbolo, fuente, nombres_propios, log, rango="5y")
            if hist:
                remapeos[simbolo] = nuevo
                nombres_propios[nuevo] = nombres_propios.get(simbolo, "")
                simbolo = nuevo
        if not hist:
            continue
        ficha = fuente.ficha(simbolo) or {}
        oficial = ficha.get("nombre") or hist.get("nombre") or simbolo
        nombre = (nombres_propios or {}).get(simbolo) or oficial
        ind = indicators.analizar_bolsa(
            hist["precios"], hist.get("volumenes"),
            ficha.get("max_52s"), ficha.get("min_52s"))
        if not ficha.get("divisa"):
            ficha["divisa"] = hist.get("divisa")

        # La evaluación mira el nombre para detectar si el ETF está cubierto,
        # así que ahí usamos siempre el nombre oficial.
        evaluacion = scoring_bolsa.puntuar_etf(simbolo, oficial, ficha, ind)
        sus = signals_bolsa.señales_valor(nombre, ind, ficha, es_etf=True)
        etfs.append({"simbolo": simbolo, "nombre": nombre, "indicadores": ind,
                     "ficha": ficha, "evaluacion": evaluacion, "señales": sus})
        alertas.extend(s for s in sus if s["prioridad"] <= 2)
        log(f"  · {nombre[:46]}: {evaluacion['nota']}/10")

    comparativa = scoring_bolsa.comparar_etfs([e["evaluacion"] for e in etfs])

    # -- acciones -----------------------------------------------------------
    log(f"→ Analizando tus {len(config.WATCHLIST_ACCIONES)} acciones...")
    acciones = []
    for simbolo in config.WATCHLIST_ACCIONES:
        hist = fuente.historico(simbolo, rango="2y")
        if not hist:
            nuevo, hist = _rescatar(simbolo, fuente, nombres_propios, log)
            if hist:
                remapeos[simbolo] = nuevo
                nombres_propios[nuevo] = nombres_propios.get(simbolo, "")
                simbolo = nuevo
        if not hist:
            continue
        ficha = fuente.ficha(simbolo) or {}
        nombre = ficha.get("nombre") or hist.get("nombre") or simbolo
        ind = indicators.analizar_bolsa(
            hist["precios"], hist.get("volumenes"),
            ficha.get("max_52s"), ficha.get("min_52s"))
        if not ficha.get("divisa"):
            ficha["divisa"] = hist.get("divisa")

        sus = signals_bolsa.señales_valor(nombre, ind, ficha, es_etf=False)
        acciones.append({"simbolo": simbolo, "nombre": nombre, "indicadores": ind,
                         "ficha": ficha, "señales": sus})
        alertas.extend(s for s in sus if s["prioridad"] <= 2)
        log(f"  · {nombre[:46]}: {ind.get('cambio_1d_pct') or 0:+.2f}% sesión")

    return {
        "lectura": lectura,
        "indices": indices,
        "etfs": etfs,
        "acciones": acciones,
        "comparativa": comparativa,
        "alertas": alertas,
        "eur_usd": eur_usd,
        "traducciones": traducciones,
        "avisos_resolucion": avisos_resolucion,
        "remapeos": remapeos,
        "peticiones": fuente.peticiones_hechas,
        "fallos": fuente.fallos,
    }



def _rescatar(simbolo: str, fuente, nombres_propios: dict | None,
              log, rango: str = "2y") -> tuple[str, dict | None]:
    """
    Segundo intento cuando un símbolo no devuelve datos.

    El caso típico: has copiado el código que enseña tu bróker. Trade Republic
    muestra "B1B" para PUIG Brands, que es el código de la bolsa alemana y no
    existe en Yahoo Finance. Aquí lo buscamos (por el nombre que hayas escrito,
    o por el propio código) y reintentamos con lo que salga.
    """
    consulta = (nombres_propios or {}).get(simbolo) or simbolo
    avisos: list[str] = []
    alternativo, info = mod_resolver.resolver_uno(
        consulta, fuente, {}, avisos, forzar=True)

    if alternativo and alternativo.upper() != simbolo.upper():
        hist = fuente.historico(alternativo, rango=rango)
        if hist:
            log(f"  · {simbolo}: sin datos en Yahoo. Encontrado como "
                f"{alternativo} ({(info or {}).get('nombre', '')[:38]}).")
            log(f"    Cambia «{simbolo}» por «{alternativo}» en cartera.csv "
                "para que no haya que buscarlo cada día.")
            return alternativo, hist

    log(f"  · {simbolo}: sin datos y no he encontrado equivalente. "
        f"Pruébalo con: python3 radar.py --buscar \"{consulta}\"")
    return simbolo, None


def _reunir_precios(watchlist: list[dict], proyectos: list[dict],
                    datos_bolsa: dict) -> dict[str, dict]:
    """Junta en un solo diccionario los precios de todo lo que hemos descargado."""
    precios: dict[str, dict] = {}

    for m in watchlist:
        mer, ind = m["mercado"], m["indicadores"]
        precios[mer["id"]] = {
            "precio": ind.get("precio"),
            "divisa": config.MONEDA.upper(),   # CoinGecko ya devuelve en tu moneda
            "nombre": mer.get("name"),
            "cambio_24h_pct": mer.get("price_change_percentage_24h"),
        }
    for p in proyectos:
        mer = p["mercado"]
        precios.setdefault(mer["id"], {
            "precio": mer.get("current_price"),
            "divisa": config.MONEDA.upper(),
            "nombre": mer.get("name"),
            "cambio_24h_pct": mer.get("price_change_percentage_24h"),
        })
    for grupo in ("etfs", "acciones"):
        for v in datos_bolsa.get(grupo) or []:
            precios[v["simbolo"]] = {
                "precio": v["indicadores"].get("precio"),
                "divisa": (v.get("ficha") or {}).get("divisa"),
                "nombre": v["nombre"],
                "cambio_24h_pct": v["indicadores"].get("cambio_1d_pct"),
            }
    return precios


def _guardar_cartera(con: sqlite3.Connection, fecha: str, cartera: dict) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS cartera (
        fecha TEXT PRIMARY KEY, valor REAL, invertido REAL,
        ganancia REAL, ganancia_pct REAL)""")
    if cartera.get("vacia"):
        return
    con.execute("INSERT OR REPLACE INTO cartera VALUES (?,?,?,?,?)",
                (fecha, cartera["total_actual"], cartera["total_invertido"],
                 cartera["ganancia"], cartera["ganancia_pct"]))
    con.commit()
