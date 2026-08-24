"""
Señales y lectura de mercado para renta variable.

Va aparte de signals.py a propósito: la bolsa y las criptos no se leen igual.

  • Los umbrales son mucho más estrechos. Una caída del 3% en el S&P 500 es
    portada de periódico; en cripto es un martes.
  • En un ETF indexado el RSI importa poco. Nadie debería vender su fondo del
    S&P 500 porque el RSI marque 72. Lo que sí importa es el contexto para la
    próxima aportación.
  • Hay indicadores que aquí sí existen y en cripto no: el VIX, los tipos de
    cambio, el PER, el dividendo.
"""

from __future__ import annotations

from . import config

UMB = config.UMBRALES_BOLSA


def _n(valor: float, decimales: int = 1, signo: bool = False) -> str:
    fmt = f"{valor:+.{decimales}f}" if signo else f"{valor:.{decimales}f}"
    return fmt.replace(".", ",")


def _señal(tipo, tono, titulo, dato, significa, ojo, termino=None, prioridad=5) -> dict:
    return {"tipo": tipo, "tono": tono, "titulo": titulo, "dato": dato,
            "significa": significa, "ojo": ojo, "termino": termino,
            "prioridad": prioridad}


# ---------------------------------------------------------------------------
# Señales sobre un valor concreto (ETF, acción o índice)
# ---------------------------------------------------------------------------

def señales_valor(nombre: str, ind: dict, ficha: dict, es_etf: bool = False) -> list[dict]:
    señales: list[dict] = []

    rsi = ind.get("rsi")
    c1 = ind.get("cambio_1d_pct")
    precio = ind.get("precio")

    # --- Movimiento del día ------------------------------------------------
    if c1 is not None:
        if c1 <= UMB.caida_fuerte_24h:
            señales.append(_señal(
                "caida_bolsa", "alerta",
                f"{nombre} cae con fuerza",
                f"{_n(c1, 2, True)}% en la sesión",
                ("Para renta variable, un movimiento de este tamaño en un día es "
                 "significativo: suele responder a datos macro, resultados o una "
                 "noticia concreta."),
                ("Si es un ETF indexado y aportas de forma periódica, una caída no es "
                 "un problema: es que ese mes compras más participaciones con el mismo "
                 "dinero."),
                prioridad=2,
            ))
        elif c1 >= UMB.subida_fuerte_24h:
            señales.append(_señal(
                "subida_bolsa", "positivo",
                f"{nombre} sube con fuerza",
                f"{_n(c1, 2, True)}% en la sesión",
                "Movimiento fuerte al alza para lo que se mueve normalmente la bolsa.",
                ("Un día bueno no cambia nada de tu plan. Los índices hacen su "
                 "rentabilidad de largo plazo en muy pocas sesiones sueltas, y son "
                 "imposibles de anticipar: por eso estar dentro gana a intentar acertar "
                 "el momento."),
                prioridad=4,
            ))

    # --- RSI, con matices distintos según sea ETF o acción -----------------
    if rsi is not None:
        if rsi < UMB.rsi_sobreventa:
            señales.append(_señal(
                "rsi_bajo_bolsa", "positivo",
                f"{nombre} está sobrevendido",
                f"RSI en {rsi:.0f} (por debajo de {UMB.rsi_sobreventa:.0f})",
                "Ha caído deprisa respecto a su comportamiento habitual.",
                ("En un fondo indexado esto no es una señal de compra ni de venta: es "
                 "contexto. Si ibas a aportar igualmente, aportas más barato."
                 if es_etf else
                 "Que haya caído rápido no dice si la empresa está peor. Mira si ha "
                 "habido resultados o noticias antes de sacar conclusiones."),
                termino="rsi", prioridad=3,
            ))
        elif rsi > UMB.rsi_sobrecompra:
            señales.append(_señal(
                "rsi_alto_bolsa", "neutro",
                f"{nombre} está sobrecomprado",
                f"RSI en {rsi:.0f} (por encima de {UMB.rsi_sobrecompra:.0f})",
                "Ha subido deprisa y el movimiento está estirado.",
                ("Los índices bursátiles pasan meses con el RSI alto durante los "
                 "mercados alcistas. Vender un indexado por esto es de los errores más "
                 "caros que existen."),
                termino="rsi", prioridad=5,
            ))

    # --- Corrección desde máximos -----------------------------------------
    desde_max = ind.get("dist_max52s_pct")
    if desde_max is not None:
        if desde_max <= -20:
            señales.append(_señal(
                "mercado_bajista", "negativo",
                f"{nombre} en mercado bajista",
                f"{_n(desde_max, 1)}% desde su máximo de 52 semanas",
                ("Una caída del 20% o más es lo que se considera formalmente un "
                 "mercado bajista."),
                ("Un índice diversificado siempre ha acabado recuperando sus máximos, "
                 "aunque haya tardado años. Eso no garantiza nada sobre el episodio "
                 "actual, pero conviene tenerlo presente antes de vender en el peor "
                 "momento."
                 if es_etf else
                 "Cuidado con aplicar aquí el argumento de «el mercado siempre se "
                 "recupera»: eso vale para un índice diversificado, no para una empresa "
                 "concreta. Una acción individual puede no recuperarse nunca."),
                termino="correccion", prioridad=2,
            ))
        elif desde_max <= -10:
            señales.append(_señal(
                "correccion", "neutro",
                f"{nombre} en corrección",
                f"{_n(desde_max, 1)}% desde su máximo de 52 semanas",
                ("Una caída de entre el 10% y el 20% es una corrección. Ocurre de "
                 "media una vez al año."),
                ("Las correcciones son el precio de entrada de la renta variable, no "
                 "una avería. Quien no las aguanta acaba obteniendo la rentabilidad "
                 "de la renta fija asumiendo el riesgo de la variable."),
                termino="correccion", prioridad=3,
            ))
        elif desde_max >= -1:
            señales.append(_señal(
                "maximos", "positivo",
                f"{nombre} en máximos de 52 semanas",
                f"A un {_n(abs(desde_max), 1)}% de su techo anual",
                "Está en la parte alta de su rango del último año.",
                ("Estar en máximos asusta, pero un índice en máximos está en máximos "
                 "precisamente porque sube a largo plazo: es su estado natural. "
                 "Esperar a una caída para entrar suele salir más caro que entrar."),
                prioridad=5,
            ))

    # --- Tendencia de largo plazo -----------------------------------------
    dist200 = ind.get("dist_sma200_pct")
    if dist200 is not None and dist200 < -8:
        señales.append(_señal(
            "bajo_sma200_bolsa", "negativo",
            f"{nombre} por debajo de su media de 200 sesiones",
            f"A un {_n(dist200, 1)}% de la SMA 200",
            "La tendencia de fondo se ha girado a la baja.",
            ("Es la referencia de tendencia más seguida del mundo, lo que la hace "
             "importante y a la vez muy propensa a falsas señales, porque medio "
             "mercado la mira a la vez."),
            termino="sma", prioridad=4,
        ))

    # --- Fundamentales: solo tienen sentido en acciones --------------------
    if not es_etf and ficha:
        per = ficha.get("per")
        if per and per > 40:
            señales.append(_señal(
                "per_alto", "alerta",
                f"{nombre} cotiza muy caro respecto a sus beneficios",
                f"PER de {_n(per, 1)}",
                (f"Pagas {_n(per, 0)} euros por cada euro de beneficio anual. La media "
                 "histórica del mercado ronda el 15-20."),
                ("Un PER alto no significa que sea mala inversión: puede estar "
                 "justificado si los beneficios crecen rápido. Significa que el mercado "
                 "ya descuenta mucho crecimiento, y que si no llega, duele."),
                termino="per", prioridad=4,
            ))
        elif per and 0 < per < 10:
            señales.append(_señal(
                "per_bajo", "neutro",
                f"{nombre} cotiza barato respecto a sus beneficios",
                f"PER de {_n(per, 1)}",
                "Está por debajo de la media histórica del mercado.",
                ("Barato y buena inversión no son lo mismo. A veces algo cotiza barato "
                 "porque el mercado espera que sus beneficios caigan. Es la clásica "
                 "trampa de valor."),
                termino="per", prioridad=5,
            ))

        div = ficha.get("dividendo_pct")
        if div and div > 6:
            señales.append(_señal(
                "dividendo_alto", "neutro",
                f"{nombre} reparte un dividendo muy alto",
                f"Rentabilidad por dividendo del {_n(div, 1)}%",
                "Reparte una parte importante de su beneficio entre los accionistas.",
                ("Ojo con perseguir dividendos altos: muchas veces el porcentaje es alto "
                 "porque el precio ha caído, no porque paguen más. Y el dividendo se "
                 "descuenta del precio de la acción el día que se paga: no es dinero "
                 "gratis."),
                termino="dividendo", prioridad=5,
            ))

    señales.sort(key=lambda s: s["prioridad"])
    return señales


# ---------------------------------------------------------------------------
# Lectura del conjunto de la bolsa
# ---------------------------------------------------------------------------

def leer_bolsa(indices: list[dict]) -> dict:
    """Resume el estado de la renta variable a partir de los índices."""
    por_simbolo = {i["simbolo"]: i for i in indices}

    def cambio(simbolo):
        i = por_simbolo.get(simbolo)
        return (i or {}).get("indicadores", {}).get("cambio_1d_pct")

    vix = por_simbolo.get("^VIX", {}).get("indicadores", {}).get("precio")
    eur_usd = por_simbolo.get("EURUSD=X", {}).get("indicadores", {}).get("precio")

    # Los índices bursátiles de verdad, sin el VIX ni las divisas
    bursatiles = [i for i in indices if i["simbolo"] not in ("^VIX", "EURUSD=X")]
    cambios = [i["indicadores"].get("cambio_1d_pct") for i in bursatiles
               if i["indicadores"].get("cambio_1d_pct") is not None]
    medio = sum(cambios) / len(cambios) if cambios else None

    if medio is None:
        titular, tono = "Sin datos de mercado", "neutro"
    elif medio > 1.0:
        titular, tono = "Sesión claramente alcista", "positivo"
    elif medio > 0.2:
        titular, tono = "Sesión positiva", "positivo"
    elif medio > -0.2:
        titular, tono = "Sesión plana", "neutro"
    elif medio > -1.0:
        titular, tono = "Sesión negativa", "negativo"
    else:
        titular, tono = "Caída generalizada", "negativo"

    partes = []
    if vix is not None:
        if vix < 15:
            partes.append(f"El VIX está en {_n(vix, 1)}: complacencia, el mercado no "
                          "ve riesgo a corto plazo.")
        elif vix < 20:
            partes.append(f"El VIX está en {_n(vix, 1)}, en su rango normal.")
        elif vix < 30:
            partes.append(f"El VIX ha subido a {_n(vix, 1)}: hay nerviosismo.")
        else:
            partes.append(f"El VIX está en {_n(vix, 1)}: miedo de verdad. "
                          "Históricamente estos niveles han coincidido con suelos, "
                          "no con techos.")

    if eur_usd is not None:
        partes.append(
            f"El euro está a {_n(eur_usd, 4)} dólares. Esto afecta a tus ETFs "
            "sin cobertura de divisa: si el dólar se debilita, tu ETF del S&P 500 "
            "en dólares rinde menos medido en euros, aunque el índice suba."
        )

    usa = [c for s, c in [("^GSPC", cambio("^GSPC")), ("^IXIC", cambio("^IXIC"))] if c is not None]
    eur = [c for s, c in [("^IBEX", cambio("^IBEX")), ("^STOXX50E", cambio("^STOXX50E"))] if c is not None]
    if usa and eur:
        m_usa, m_eur = sum(usa)/len(usa), sum(eur)/len(eur)
        if abs(m_usa - m_eur) > 0.8:
            lider = "Estados Unidos" if m_usa > m_eur else "Europa"
            partes.append(f"{lider} se comporta bastante mejor hoy "
                          f"({_n(max(m_usa, m_eur), 2, True)}% frente a "
                          f"{_n(min(m_usa, m_eur), 2, True)}%).")

    return {
        "titular": titular,
        "tono": tono,
        "cambio_medio": medio,
        "vix": vix,
        "eur_usd": eur_usd,
        "detalle": " ".join(partes),
        "indices": indices,
    }
