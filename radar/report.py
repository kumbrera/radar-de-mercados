"""
Generación del informe HTML.

Produce un fichero HTML autocontenido (sin dependencias externas salvo las
tipografías de Google Fonts) que puedes abrir en cualquier navegador, guardar,
mandarte por email o publicar.

Cada término técnico lleva un botón "?" que despliega su explicación.
"""

from __future__ import annotations

import html
import json
from datetime import datetime

from . import config
from .estilos import ESTILOS
from .glossary import FAQS_GENERALES, GLOSARIO

MONEDA = config.SIMBOLO_MONEDA


# ---------------------------------------------------------------------------
# Utilidades de formato (formato español: punto de miles, coma decimal)
# ---------------------------------------------------------------------------

def fmt_num(valor: float | None, decimales: int = 2) -> str:
    if valor is None:
        return "—"
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", " ").replace(".", ",").replace(" ", ".")


def fmt_precio(valor: float | None) -> str:
    if valor is None:
        return "—"
    if valor >= 1000:
        return f"{fmt_num(valor, 0)} {MONEDA}"
    if valor >= 1:
        return f"{fmt_num(valor, 2)} {MONEDA}"
    if valor >= 0.01:
        return f"{fmt_num(valor, 4)} {MONEDA}"
    return f"{fmt_num(valor, 6)} {MONEDA}"


def fmt_grande(valor: float | None) -> str:
    if valor is None:
        return "—"
    for limite, sufijo in ((1e12, "B"), (1e9, "MM"), (1e6, "M"), (1e3, "K")):
        if abs(valor) >= limite:
            return f"{fmt_num(valor / limite, 2)} {sufijo} {MONEDA}"
    return f"{fmt_num(valor, 0)} {MONEDA}"


def fmt_pct(valor: float | None, decimales: int = 1) -> str:
    if valor is None:
        return "—"
    return f"{valor:+.{decimales}f}%".replace(".", ",")


def clase_signo(valor: float | None) -> str:
    if valor is None:
        return "neutro"
    return "pos" if valor > 0 else ("neg" if valor < 0 else "neutro")


def esc(texto) -> str:
    return html.escape(str(texto if texto is not None else ""))


# ---------------------------------------------------------------------------
# Glosario: botón "?" que despliega la explicación
# ---------------------------------------------------------------------------

def ayuda(clave: str, etiqueta: str | None = None) -> str:
    """Devuelve el término con un botón de ayuda al lado."""
    entrada = GLOSARIO.get(clave)
    if not entrada:
        return esc(etiqueta or clave)
    texto = esc(etiqueta) if etiqueta else esc(entrada["titulo"])
    return (
        f'<span class="term">{texto}'
        f'<button class="ayuda" type="button" data-glosa="{esc(clave)}" '
        f'aria-label="Qué significa {esc(entrada["titulo"])}">?</button>'
        f"</span>"
    )


def ayuda_suelta(clave: str) -> str:
    """Solo el botón "?", sin texto delante. Para cuando el término ya se ha dicho."""
    entrada = GLOSARIO.get(clave)
    if not entrada:
        return ""
    return (
        f'<button class="ayuda" type="button" data-glosa="{esc(clave)}" '
        f'aria-label="Qué significa {esc(entrada["titulo"])}">?</button>'
    )


# ---------------------------------------------------------------------------
# Gráficos SVG
# ---------------------------------------------------------------------------

def sparkline(serie: list[float], tono: str = "auto", altura: int = 56) -> str:
    """Minigráfico de línea con relleno y punto final destacado."""
    puntos = [float(p) for p in serie if p is not None]
    if len(puntos) < 2:
        return '<div class="spark-vacio">Sin datos suficientes</div>'

    ancho = 300.0
    minimo, maximo = min(puntos), max(puntos)
    rango = (maximo - minimo) or (maximo or 1) * 0.01
    n = len(puntos)
    margen = 4.0
    util = altura - margen * 2

    coords = [
        (i / (n - 1) * ancho, margen + (1 - (p - minimo) / rango) * util)
        for i, p in enumerate(puntos)
    ]
    linea = " ".join(f"{x:.2f},{y:.2f}" for x, y in coords)
    area = (f"M{coords[0][0]:.2f},{altura} "
            + " ".join(f"L{x:.2f},{y:.2f}" for x, y in coords)
            + f" L{coords[-1][0]:.2f},{altura} Z")

    if tono == "auto":
        tono = "pos" if puntos[-1] >= puntos[0] else "neg"
    fx, fy = coords[-1]
    uid = abs(hash(linea)) % 10_000_000

    return f"""<svg class="spark spark-{tono}" viewBox="0 0 {ancho:.0f} {altura}" \
preserveAspectRatio="none" role="img" aria-label="Evolución del precio">
  <defs><linearGradient id="g{uid}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="currentColor" stop-opacity="0.26"/>
    <stop offset="100%" stop-color="currentColor" stop-opacity="0"/>
  </linearGradient></defs>
  <path d="{area}" fill="url(#g{uid})"/>
  <polyline points="{linea}" fill="none" stroke="currentColor" stroke-width="1.6"
    stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>
  <circle cx="{fx:.2f}" cy="{fy:.2f}" r="2.6" fill="currentColor"
    vector-effect="non-scaling-stroke"/>
</svg>"""


def medidor_rsi(valor: float | None) -> str:
    """Barra horizontal con las zonas de sobreventa y sobrecompra marcadas."""
    if valor is None:
        return '<div class="spark-vacio">RSI no disponible</div>'
    zona = "bajo" if valor < 30 else ("alto" if valor > 70 else "medio")
    etiqueta = {"bajo": "Sobrevendido", "medio": "Zona neutra", "alto": "Sobrecomprado"}[zona]
    return f"""<div class="rsi">
  <div class="rsi-cab">
    <span class="rsi-lab">{ayuda('rsi', 'RSI')}</span>
    <span class="rsi-val rsi-{zona}">{valor:.0f}<small>/100</small></span>
  </div>
  <div class="rsi-pista">
    <span class="rsi-zona rsi-zona-baja"></span>
    <span class="rsi-zona rsi-zona-alta"></span>
    <span class="rsi-aguja rsi-{zona}" style="left:{max(0.5, min(99.5, valor)):.1f}%"></span>
  </div>
  <div class="rsi-pie"><span>0</span><span class="rsi-estado rsi-{zona}">{etiqueta}</span><span>100</span></div>
</div>"""


def arco_sentimiento(valor: int | None, etiqueta: str | None) -> str:
    """Semicírculo para el índice de miedo y codicia."""
    if valor is None:
        return ""
    import math
    r, cx, cy = 52, 64, 64
    ang = math.pi * (1 - valor / 100.0)
    x, y = cx + r * math.cos(ang), cy - r * math.sin(ang)
    largo = math.pi * r
    recorrido = largo * (valor / 100.0)
    zona = ("miedo-ext" if valor < 25 else "miedo" if valor < 45 else
            "neutral" if valor < 55 else "codicia" if valor < 75 else "codicia-ext")
    return f"""<div class="fng fng-{zona}">
  <svg viewBox="0 0 128 78" role="img" aria-label="Índice de miedo y codicia: {valor} de 100">
    <path d="M12,64 A52,52 0 0 1 116,64" fill="none" stroke="var(--linea)" stroke-width="9" stroke-linecap="round"/>
    <path d="M12,64 A52,52 0 0 1 116,64" fill="none" stroke="currentColor" stroke-width="9"
      stroke-linecap="round" stroke-dasharray="{recorrido:.1f} {largo:.1f}"/>
    <circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var(--superficie)" stroke="currentColor" stroke-width="3"/>
  </svg>
  <div class="fng-num">{valor}</div>
  <div class="fng-lab">{esc(etiqueta or '')}</div>
</div>"""


def barra_bloques(bloques: dict, pesos: dict) -> str:
    """Desglose del scoring: una barra por bloque, con su peso y su explicación."""
    nombres = {
        "liquidez": ("Liquidez", "ratio_volumen_mcap"),
        "desarrollo": ("Desarrollo", "desarrollo"),
        "comunidad": ("Comunidad", None),
        "momento": ("Momento", None),
        "valoracion": ("Valoración", "ath"),
        "tokenomics": ("Tokenomics", "tokenomics"),
    }
    filas = []
    for clave, (etiqueta, glosa) in nombres.items():
        b = bloques.get(clave)
        if not b:
            continue
        nota = b["nota"]
        calidad = "alta" if nota >= 70 else ("media" if nota >= 45 else "baja")
        titulo = ayuda(glosa, etiqueta) if glosa else esc(etiqueta)
        filas.append(f"""<div class="bloque">
  <div class="bloque-cab">
    <span class="bloque-nom">{titulo}<span class="peso">{pesos[clave]}%</span></span>
    <span class="bloque-nota nota-{calidad}">{nota:.0f}</span>
  </div>
  <div class="bloque-pista"><span class="bloque-relleno nota-{calidad}" style="width:{nota:.0f}%"></span></div>
  <p class="bloque-txt">{esc(b['texto'])}</p>
</div>""")
    return '<div class="bloques">' + "".join(filas) + "</div>"


# ---------------------------------------------------------------------------
# Secciones del informe
# ---------------------------------------------------------------------------

def _seccion_pulso(g: dict) -> str:
    amplitud = g.get("amplitud")
    barra_amplitud = ""
    if amplitud is not None:
        barra_amplitud = f"""<div class="amplitud">
  <div class="amplitud-pista">
    <span class="amplitud-sube" style="width:{amplitud:.0f}%"></span>
  </div>
  <div class="amplitud-pie"><span class="pos">{amplitud:.0f}% sube</span><span class="neg">{100-amplitud:.0f}% baja</span></div>
</div>"""

    return f"""<section class="pulso" aria-labelledby="h-pulso">
  <h2 id="h-pulso" class="oculto">Estado del mercado</h2>
  <div class="pulso-rejilla">
    <div class="pulso-titular tono-{esc(g['tono'])}">
      <span class="eyebrow">Estado del mercado</span>
      <p class="titular">{esc(g['titular'])}</p>
      <p class="titular-detalle">{esc(g['detalle'])}</p>
    </div>
    <div class="instrumentos">
      <div class="instr">
        <span class="instr-lab">{ayuda('market_cap', 'Capitalización total')}</span>
        <span class="instr-val">{fmt_grande(g.get('cap_total'))}</span>
        <span class="instr-sub {clase_signo(g.get('cambio_24h'))}">{fmt_pct(g.get('cambio_24h'), 2)} en 24 h</span>
      </div>
      <div class="instr">
        <span class="instr-lab">{ayuda('dominancia_btc', 'Dominancia BTC')}</span>
        <span class="instr-val">{fmt_num(g.get('dominancia_btc'), 1)}%</span>
        <span class="instr-sub">del mercado total</span>
      </div>
      <div class="instr instr-amplitud">
        <span class="instr-lab">Amplitud del mercado</span>
        {barra_amplitud or '<span class="instr-val">—</span>'}
      </div>
      <div class="instr instr-fng">
        <span class="instr-lab">{ayuda('fear_greed', 'Miedo y codicia')}</span>
        {arco_sentimiento(g.get('fng_valor'), g.get('fng_etiqueta'))}
      </div>
    </div>
  </div>
</section>"""


def _tarjeta_señal(s: dict) -> str:
    icono = {"positivo": "▲", "negativo": "▼", "alerta": "!", "neutro": "•"}.get(s["tono"], "•")
    glosa = ayuda_suelta(s["termino"]) if s.get("termino") else ""
    return f"""<article class="senal senal-{esc(s['tono'])}">
  <div class="senal-marca" aria-hidden="true">{icono}</div>
  <div class="senal-cuerpo">
    <h3 class="senal-tit">{esc(s['titulo'])}</h3>
    <p class="senal-dato">{esc(s['dato'])}{glosa}</p>
    <p class="senal-txt"><strong>Qué suele significar:</strong> {esc(s['significa'])}</p>
    <p class="senal-ojo"><strong>Ojo:</strong> {esc(s['ojo'])}</p>
  </div>
</article>"""


def _seccion_alertas(alertas: list[dict]) -> str:
    if not alertas:
        return """<section class="bloque-seccion">
  <h2>Alertas de hoy</h2>
  <div class="vacio-ok">
    <p><strong>Ninguna. Y eso es información, no un fallo.</strong></p>
    <p>Ninguna de tus criptos ha hecho nada estadísticamente inusual hoy. El día correcto para no tocar nada.</p>
  </div>
</section>"""
    cuerpo = "".join(_tarjeta_señal(s) for s in alertas)
    return f"""<section class="bloque-seccion">
  <h2>Alertas de hoy</h2>
  <p class="seccion-intro">Cosas que se salen de lo normal. Son motivos para <em>mirar</em>, nunca para operar automáticamente.</p>
  <div class="senales">{cuerpo}</div>
</section>"""


def _tarjeta_moneda(m: dict) -> str:
    ind, mer = m["indicadores"], m["mercado"]
    c24 = mer.get("price_change_percentage_24h")
    serie = ind.get("serie") or []

    niveles = ind.get("niveles") or {}
    fila_niveles = ""
    if niveles:
        fila_niveles = f"""<div class="dato">
      <span class="dato-lab">{ayuda('soporte_resistencia', 'Rango 90 d')}</span>
      <span class="dato-val mono">{fmt_precio(niveles['soporte'])} – {fmt_precio(niveles['resistencia'])}</span>
    </div>"""

    señales = m.get("señales") or []
    lista_señales = ""
    if señales:
        items = "".join(
            f'<li class="mini mini-{esc(s["tono"])}"><strong>{esc(s["titulo"])}</strong> — {esc(s["dato"])}</li>'
            for s in señales[:4]
        )
        lista_señales = f'<ul class="mini-lista">{items}</ul>'
    else:
        lista_señales = '<p class="sin-senal">Sin señales. Comportamiento dentro de lo normal.</p>'

    vol = ind.get("volatilidad_pct")
    return f"""<article class="moneda">
  <header class="moneda-cab">
    <div>
      <h3>{esc(mer.get('name'))} <span class="ticker">{esc((mer.get('symbol') or '').upper())}</span></h3>
      <p class="moneda-precio">{fmt_precio(ind.get('precio'))}
        <span class="delta {clase_signo(c24)}">{fmt_pct(c24)} 24 h</span></p>
    </div>
    <div class="moneda-spark">{sparkline(serie[-120:])}
      <span class="spark-pie">120 días</span>
    </div>
  </header>

  {medidor_rsi(ind.get('rsi'))}

  <div class="datos">
    <div class="dato">
      <span class="dato-lab">7 días</span>
      <span class="dato-val mono {clase_signo(ind.get('cambio_7d_pct'))}">{fmt_pct(ind.get('cambio_7d_pct'))}</span>
    </div>
    <div class="dato">
      <span class="dato-lab">30 días</span>
      <span class="dato-val mono {clase_signo(ind.get('cambio_30d_pct'))}">{fmt_pct(ind.get('cambio_30d_pct'))}</span>
    </div>
    <div class="dato">
      <span class="dato-lab">{ayuda('sma', 'vs. SMA 200')}</span>
      <span class="dato-val mono {clase_signo(ind.get('dist_sma200_pct'))}">{fmt_pct(ind.get('dist_sma200_pct'))}</span>
    </div>
    <div class="dato">
      <span class="dato-lab">{ayuda('volatilidad', 'Volatilidad')}</span>
      <span class="dato-val mono">{fmt_num(vol, 0) if vol else '—'}%</span>
    </div>
    <div class="dato">
      <span class="dato-lab">{ayuda('ath', 'Desde máximos')}</span>
      <span class="dato-val mono neg">{fmt_pct(mer.get('ath_change_percentage'), 0)}</span>
    </div>
    <div class="dato">
      <span class="dato-lab">{ayuda('volumen_relativo', 'Volumen rel.')}</span>
      <span class="dato-val mono">{fmt_num(ind.get('volumen_relativo'), 1) if ind.get('volumen_relativo') else '—'}×</span>
    </div>
    {fila_niveles}
  </div>

  {lista_señales}
</article>"""


def _seccion_watchlist(monedas: list[dict]) -> str:
    if not monedas:
        return ""
    cuerpo = "".join(_tarjeta_moneda(m) for m in monedas)
    return f"""<section class="bloque-seccion">
  <h2>Tus criptos</h2>
  <p class="seccion-intro">Las monedas de tu watchlist, con un año de histórico detrás de cada indicador.</p>
  <div class="rejilla-monedas">{cuerpo}</div>
</section>"""


def _tarjeta_proyecto(p: dict, posicion: int) -> str:
    mer = p["mercado"]
    flags = p.get("red_flags") or []
    chips_flags = "".join(
        f'<span class="flag" title="{esc(f["detalle"])}">{esc(f["tipo"])} −{f["penalizacion"]}</span>'
        for f in flags
    )
    detalle_flags = ""
    if flags:
        items = "".join(
            f'<li><strong>{esc(f["tipo"])}:</strong> {esc(f["detalle"])}</li>' for f in flags
        )
        detalle_flags = f"""<details class="flags-detalle">
      <summary>{ayuda('red_flag', f'{len(flags)} señal{"es" if len(flags) > 1 else ""} de alarma')}</summary>
      <ul>{items}</ul>
    </details>"""

    cats = " · ".join(esc(c) for c in (p.get("categorias") or [])[:3])
    spark = sparkline((mer.get("sparkline_in_7d") or {}).get("price") or [], altura=40)

    return f"""<article class="proyecto proyecto-{esc(p['color'])}">
  <header class="proyecto-cab">
    <span class="rango mono">{posicion:02d}</span>
    <div class="proyecto-id">
      <h3>{esc(p['nombre'])} <span class="ticker">{esc(p['simbolo'])}</span></h3>
      <p class="proyecto-cats">{cats or 'Sin categoría'}</p>
    </div>
    <div class="proyecto-nota">
      <span class="nota-num">{fmt_num(p['nota'], 1)}</span>
      <span class="nota-de">/10</span>
      <span class="nota-nivel">{esc(p['nivel'])}</span>
    </div>
  </header>

  <div class="proyecto-cifras">
    <div><span class="dato-lab">Precio</span><span class="mono">{fmt_precio(mer.get('current_price'))}</span></div>
    <div><span class="dato-lab">{ayuda('market_cap', 'Cap.')}</span><span class="mono">{fmt_grande(mer.get('market_cap'))}</span></div>
    <div><span class="dato-lab">{ayuda('volumen_24h', 'Vol. 24 h')}</span><span class="mono">{fmt_grande(mer.get('total_volume'))}</span></div>
    <div><span class="dato-lab">30 días</span><span class="mono {clase_signo(mer.get('price_change_percentage_30d_in_currency'))}">{fmt_pct(mer.get('price_change_percentage_30d_in_currency'), 0)}</span></div>
    <div class="proyecto-spark">{spark}</div>
  </div>

  {f'<div class="flags">{chips_flags}</div>' if chips_flags else ''}

  <details class="desglose">
    <summary>Ver cómo se ha calculado el {ayuda('score', 'score')}</summary>
    {barra_bloques(p['bloques'], config.PESOS_SCORING)}
    <p class="desglose-pie">Nota antes de penalizaciones: {fmt_num(p['nota_bruta'], 1)}/10 · {
      f"Penalización por alarmas: −{p['penalizacion_total']} puntos"
      if p['penalizacion_total'] else "Sin penalizaciones"}</p>
  </details>

  {detalle_flags}
</article>"""


def _seccion_proyectos(proyectos: list[dict]) -> str:
    if not proyectos:
        return ""
    cuerpo = "".join(_tarjeta_proyecto(p, i + 1) for i, p in enumerate(proyectos))
    return f"""<section class="bloque-seccion">
  <h2>Proyectos que merecen una mirada</h2>
  <p class="seccion-intro">
    De las {config.TOP_A_ESCANEAR} monedas más grandes, estas son las que mejor puntúan
    en liquidez, desarrollo, tokenomics y valoración. El orden es la nota del sistema,
    no una recomendación: significa <em>«dedícale una tarde a investigar esto»</em>,
    no <em>«compra esto»</em>.
  </p>
  <div class="proyectos">{cuerpo}</div>
</section>"""


def _seccion_movimientos(destacados: dict) -> str:
    def filas(lista, signo):
        return "".join(f"""<tr>
      <td><span class="fila-nom">{esc(m.get('name'))}</span> <span class="ticker">{esc((m.get('symbol') or '').upper())}</span></td>
      <td class="mono num">{fmt_precio(m.get('current_price'))}</td>
      <td class="mono num {signo}">{fmt_pct(m.get('price_change_percentage_24h'))}</td>
      <td class="mono num tenue">{fmt_grande(m.get('total_volume'))}</td>
    </tr>""" for m in lista)

    return f"""<section class="bloque-seccion">
  <h2>Lo que más se ha movido</h2>
  <div class="tablas">
    <div class="tabla-caja">
      <h3 class="tabla-tit pos">Mayores subidas 24 h</h3>
      <div class="tabla-scroll"><table>
        <thead><tr><th>Moneda</th><th class="num">Precio</th><th class="num">24 h</th><th class="num">Volumen</th></tr></thead>
        <tbody>{filas(destacados.get('suben', []), 'pos')}</tbody>
      </table></div>
    </div>
    <div class="tabla-caja">
      <h3 class="tabla-tit neg">Mayores caídas 24 h</h3>
      <div class="tabla-scroll"><table>
        <thead><tr><th>Moneda</th><th class="num">Precio</th><th class="num">24 h</th><th class="num">Volumen</th></tr></thead>
        <tbody>{filas(destacados.get('bajan', []), 'neg')}</tbody>
      </table></div>
    </div>
  </div>
  <p class="nota-pie">Una subida grande de un día no es una oportunidad: normalmente es el momento en que ya te la has perdido. La columna útil aquí es la de volumen — sin volumen, el movimiento suele deshacerse.</p>
</section>"""


def _seccion_glosario() -> str:
    entradas = "".join(f"""<details class="glosa-entrada">
    <summary><span class="glosa-texto"><strong>{esc(v['titulo'])}</strong><span class="glosa-corto">{esc(v['corto'])}</span></span></summary>
    <div class="glosa-largo">{''.join(f'<p>{esc(par)}</p>' for par in v['largo'].split(chr(10)+chr(10)))}</div>
  </details>""" for v in GLOSARIO.values())

    faqs = "".join(f"""<details class="glosa-entrada">
    <summary><span class="glosa-texto"><strong>{esc(f['pregunta'])}</strong></span></summary>
    <div class="glosa-largo">{''.join(f'<p>{esc(par)}</p>' for par in f['respuesta'].split(chr(10)+chr(10)))}</div>
  </details>""" for f in FAQS_GENERALES)

    return f"""<section class="bloque-seccion" id="aprender">
  <h2>Aprender</h2>
  <p class="seccion-intro">Todo lo que aparece en el informe, explicado. Cuando dejes de necesitar esta sección, el sistema habrá cumplido su función.</p>
  <div class="dos-col">
    <div>
      <h3 class="sub">Preguntas frecuentes</h3>
      <div class="glosa-lista">{faqs}</div>
    </div>
    <div>
      <h3 class="sub">Glosario</h3>
      <div class="glosa-lista">{entradas}</div>
    </div>
  </div>
</section>"""


def _seccion_disclaimer(meta: dict) -> str:
    g = GLOSARIO["no_es_consejo"]
    return f"""<section class="cierre">
  <h2>{esc(g['titulo'])}</h2>
  {''.join(f'<p>{esc(par)}</p>' for par in g['largo'].split(chr(10)+chr(10)))}
  <p class="meta">
    Generado el {esc(meta['fecha_larga'])} ·
    Fuentes: CoinGecko y alternative.me ·
    {esc(meta['peticiones'])} peticiones a la API ·
    {esc(meta['modo'])}
  </p>
</section>"""


# ---------------------------------------------------------------------------
# Documento completo
# ---------------------------------------------------------------------------

def construir_html(datos: dict) -> str:
    from . import report_bolsa  # aquí para evitar una importación circular

    meta = datos["meta"]
    bolsa = datos.get("bolsa") or {}

    partes = [
        # 1. Cómo está el mundo
        report_bolsa.seccion_indices(bolsa.get("lectura")),
        _seccion_pulso(datos["global"]),
        # 2. Qué me afecta a mí
        _seccion_alertas(datos["alertas"]),
        report_bolsa.seccion_cartera(datos.get("cartera")),
        # 3. Mis posiciones en detalle
        report_bolsa.seccion_etfs(bolsa.get("etfs") or [], bolsa.get("comparativa")),
        report_bolsa.seccion_acciones(bolsa.get("acciones") or []),
        _seccion_watchlist(datos["watchlist"]),
        # 4. Ideas nuevas
        _seccion_proyectos(datos["proyectos"]),
        _seccion_movimientos(datos["destacados"]),
    ]
    if config.INFORME.incluir_glosario:
        partes.append(_seccion_glosario())
    if config.INFORME.incluir_disclaimer:
        partes.append(_seccion_disclaimer(meta))

    glosario_json = json.dumps(
        {k: {"titulo": v["titulo"], "largo": v["largo"]} for k, v in GLOSARIO.items()},
        ensure_ascii=False,
    )

    return f"""<title>Radar de Mercados</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">
<style>{ESTILOS}</style>

<div class="pagina">
  <header class="cabecera">
    <div class="cabecera-txt">
      <span class="eyebrow">Informe diario · {esc(meta['fecha_corta'])}</span>
      <h1>Radar de Mercados</h1>
      <p class="lema">Bolsa y criptomonedas. Qué ha pasado, qué se sale de lo normal, cómo va tu cartera y dónde debería ir la próxima aportación. Con todo explicado.</p>
    </div>
    <nav class="indice" aria-label="Secciones">
      <a href="#aprender">Glosario y FAQs</a>
    </nav>
  </header>

  {''.join(partes)}
</div>

<div class="glosa-modal" id="glosaModal" role="dialog" aria-modal="true" aria-labelledby="glosaTit" hidden>
  <div class="glosa-panel">
    <button class="glosa-cerrar" id="glosaCerrar" type="button" aria-label="Cerrar">×</button>
    <h3 id="glosaTit"></h3>
    <div id="glosaCuerpo"></div>
  </div>
</div>

<script>
const GLOSARIO = {glosario_json};
(function () {{
  const modal = document.getElementById('glosaModal');
  const titulo = document.getElementById('glosaTit');
  const cuerpo = document.getElementById('glosaCuerpo');
  let ultimoFoco = null;

  function abrir(clave) {{
    const entrada = GLOSARIO[clave];
    if (!entrada) return;
    ultimoFoco = document.activeElement;
    titulo.textContent = entrada.titulo;
    cuerpo.innerHTML = '';
    entrada.largo.split('\\n\\n').forEach(function (par) {{
      const p = document.createElement('p');
      p.textContent = par;
      cuerpo.appendChild(p);
    }});
    modal.hidden = false;
    document.getElementById('glosaCerrar').focus();
  }}

  function cerrar() {{
    modal.hidden = true;
    if (ultimoFoco) ultimoFoco.focus();
  }}

  document.addEventListener('click', function (e) {{
    const boton = e.target.closest('[data-glosa]');
    if (boton) {{ e.preventDefault(); abrir(boton.dataset.glosa); return; }}
    if (e.target === modal || e.target.id === 'glosaCerrar') cerrar();
  }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && !modal.hidden) cerrar();
  }});
}})();
</script>
"""


def guardar(datos: dict, ruta=None, pagina_completa: bool = True):
    """
    Escribe el informe en disco y devuelve la ruta.

    Por defecto genera un documento HTML completo, que es lo que quieres para
    abrirlo con doble clic o mandártelo. Con pagina_completa=False devuelve solo
    el fragmento (sin <html> ni <head>), que es lo que necesita el publicador
    de artefactos.
    """
    if ruta is None:
        marca = datetime.now().strftime("%Y-%m-%d")
        ruta = config.DIR_SALIDAS / f"informe-{marca}.html"

    if pagina_completa:
        from .web import construir_pagina
        contenido = construir_pagina(datos, para_web=False)
    else:
        contenido = construir_html(datos)

    ruta.write_text(contenido, encoding="utf-8")
    return ruta
