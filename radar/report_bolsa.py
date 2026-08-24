"""
Secciones del informe correspondientes a bolsa y cartera.

Vive aparte de report.py solo por tamaño; usa sus mismas utilidades de formato.
"""

from __future__ import annotations

from . import config
from .report import (ayuda, ayuda_suelta, clase_signo, esc, fmt_grande,
                     fmt_num, fmt_pct, fmt_precio, medidor_rsi, sparkline)

MONEDA = config.SIMBOLO_MONEDA


# ---------------------------------------------------------------------------
# Cinta de índices
# ---------------------------------------------------------------------------

def seccion_indices(lectura: dict) -> str:
    if not lectura or not lectura.get("indices"):
        return ""

    tarjetas = []
    for i in lectura["indices"]:
        ind = i["indicadores"]
        c = ind.get("cambio_1d_pct")
        es_vix = i["simbolo"] == "^VIX"
        es_divisa = i["simbolo"] == "EURUSD=X"

        # En el VIX subir es malo: los colores se invierten respecto a un índice
        signo = clase_signo(c)
        if es_vix and c is not None:
            signo = "neg" if c > 0 else "pos"
        if es_divisa:
            signo = "neutro"

        decimales = 4 if es_divisa else (1 if es_vix else 0)
        valor = fmt_num(ind.get("precio"), decimales)

        tarjetas.append(f"""<article class="indice">
      <span class="indice-nom">{esc(i['nombre'])}</span>
      <span class="indice-val mono">{valor}</span>
      <span class="indice-cambio mono {signo}">{fmt_pct(c, 2)}</span>
      <div class="indice-spark">{sparkline((ind.get('serie') or [])[-90:], tono=signo if signo != 'neutro' else 'auto', altura=28)}</div>
    </article>""")

    return f"""<section class="pulso pulso-bolsa" aria-labelledby="h-bolsa">
  <h2 id="h-bolsa" class="oculto">Estado de la bolsa</h2>
  <div class="pulso-rejilla pulso-rejilla-bolsa">
    <div class="pulso-titular tono-{esc(lectura['tono'])}">
      <span class="eyebrow">La bolsa hoy</span>
      <p class="titular">{esc(lectura['titular'])}</p>
      <p class="titular-detalle">{esc(lectura['detalle'])}</p>
    </div>
    <div class="indices">{''.join(tarjetas)}</div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# Cartera
# ---------------------------------------------------------------------------

def _bloque_avisos_csv(c: dict) -> str:
    """Problemas al leer cartera.csv. Se enseñan arriba del todo, bien visibles."""
    avisos = (c or {}).get("avisos_csv") or []
    if not avisos:
        return ""
    items = "".join(f"<li>{esc(a)}</li>" for a in avisos)
    return f"""<div class="aviso-csv">
    <p><strong>Revisa tu cartera.csv</strong> — el resto del informe se ha
    generado igual, pero estas líneas necesitan atención:</p>
    <ul>{items}</ul>
  </div>"""


def _bloque_traducciones(c: dict) -> str:
    """
    Qué ISIN o nombre se ha convertido en qué símbolo.

    Merece salir en el informe: es el punto donde el sistema toma una decisión
    por ti, y conviene que puedas comprobarla de un vistazo en vez de fiarte.
    """
    trad = (c or {}).get("traducciones") or {}
    if not trad:
        return ""

    filas = []
    for simbolo, info in trad.items():
        alternativas = ""
        if info.get("alternativas"):
            otras = "".join(
                f"<li><code>{esc(a['simbolo'])}</code> — {esc(a.get('nombre') or '')}"
                f"{' · ' + esc(a['bolsa']) if a.get('bolsa') else ''}</li>"
                for a in info["alternativas"])
            alternativas = f"""<details>
        <summary>No es este: ver otras {len(info['alternativas'])} coincidencias</summary>
        <ul class="alternativas">{otras}</ul>
      </details>"""
        filas.append(f"""<div class="traduccion">
      <div class="traduccion-linea">
        <code>{esc(info.get('buscado') or '')}</code>
        <span class="flecha" aria-hidden="true">→</span>
        <code class="destino">{esc(simbolo)}</code>
        <span class="traduccion-nombre">{esc(info.get('nombre') or '')}</span>
      </div>
      {alternativas}
    </div>""")

    return f"""<details class="traducciones">
    <summary>He traducido {len(trad)} identificador(es) a símbolos de mercado</summary>
    <p class="traducciones-txt">Escribiste un ISIN o un nombre y he buscado a qué
    activo corresponde. Comprueba que el nombre es el que esperabas: si no lo es,
    pon directamente el símbolo correcto en <code>cartera.csv</code>.</p>
    {''.join(filas)}
  </details>"""


def seccion_cartera(c: dict) -> str:
    if not c or c.get("vacia"):
        return f"""<section class="bloque-seccion">
  <h2>Tu cartera</h2>
  {_bloque_avisos_csv(c)}
  <div class="vacio-ok vacio-neutro">
    <p><strong>Todavía no has apuntado ninguna posición.</strong></p>
    <p>Abre <code>cartera.csv</code> y añade una línea por cada compra:</p>
    <pre class="ejemplo">identificador,tipo,unidades,precio_medio
VWCE.DE,etf,0.78,127.90
bitcoin,cripto,0.000572,60100</pre>
    <p>Puedes editarlo desde el móvil, en GitHub, sin tocar nada de código. A partir
    de ahí el informe te calculará ganancias, desviación respecto a tu reparto
    objetivo y hacia dónde dirigir la próxima aportación.</p>
  </div>
</section>"""

    hoy = c.get("cambio_hoy")
    linea_hoy = ""
    if hoy:
        linea_hoy = (f'<span class="cartera-hoy {clase_signo(hoy["pct"])}">'
                     f'{fmt_pct(hoy["pct"], 2)} hoy '
                     f'({fmt_num(hoy["importe"], 2)} {MONEDA})</span>')

    filas = "".join(f"""<tr>
      <td>
        <span class="fila-nom">{esc(p['nombre'])}</span>
        <span class="ticker">{esc(p['id'])}</span>
        <span class="etiqueta-tipo etiqueta-{esc(p['tipo'])}">{esc(_nombre_tipo(p['tipo']))}</span>
      </td>
      <td class="mono num">{fmt_num(p['unidades'], _dec_unidades(p['unidades']))}</td>
      <td class="mono num tenue">{fmt_precio(p['precio_medio'])}</td>
      <td class="mono num">{fmt_precio(p['precio_actual'])}</td>
      <td class="mono num"><strong>{fmt_num(p['valor'], 2)} {MONEDA}</strong></td>
      <td class="mono num {clase_signo(p['ganancia'])}">{fmt_num(p['ganancia'], 2)} {MONEDA}</td>
      <td class="mono num {clase_signo(p['ganancia_pct'])}">{fmt_pct(p['ganancia_pct'])}</td>
      <td class="mono num tenue">{fmt_num(p.get('peso_pct'), 1)}%</td>
    </tr>""" for p in c["posiciones"])

    aviso_divisa = ""
    if c.get("conversion_incompleta"):
        aviso_divisa = ("<p class=\"nota-pie\">Aviso: hay posiciones en otra divisa y no se "
                        "ha podido obtener el tipo de cambio, así que el total mezcla "
                        "monedas. Revísalo antes de fiarte de la cifra global.</p>")

    sin_datos = ""
    if c.get("sin_datos"):
        nombres = ", ".join(esc(p["id"]) for p in c["sin_datos"])
        sin_datos = (f'<p class="nota-pie">Sin precio disponible para: {nombres}. '
                     "Comprueba que el identificador es correcto.</p>")

    return f"""<section class="bloque-seccion">
  <h2>Tu cartera</h2>
  {_bloque_avisos_csv(c)}
  {_bloque_traducciones(c)}
  <div class="cartera-resumen">
    <div class="cartera-cifra">
      <span class="dato-lab">Valor actual</span>
      <span class="cartera-total mono">{fmt_num(c['total_actual'], 2)} {MONEDA}</span>
      {linea_hoy}
    </div>
    <div class="cartera-cifra">
      <span class="dato-lab">Invertido</span>
      <span class="cartera-sub mono">{fmt_num(c['total_invertido'], 2)} {MONEDA}</span>
    </div>
    <div class="cartera-cifra">
      <span class="dato-lab">Resultado</span>
      <span class="cartera-sub mono {clase_signo(c['ganancia'])}">
        {fmt_num(c['ganancia'], 2)} {MONEDA}</span>
      <span class="cartera-pct {clase_signo(c['ganancia_pct'])}">{fmt_pct(c['ganancia_pct'])}</span>
    </div>
  </div>

  <div class="tabla-caja">
    <div class="tabla-scroll"><table>
      <thead><tr>
        <th>Posición</th><th class="num">Unidades</th><th class="num">P. medio</th>
        <th class="num">P. actual</th><th class="num">Valor</th>
        <th class="num">Resultado</th><th class="num">%</th><th class="num">Peso</th>
      </tr></thead>
      <tbody>{filas}</tbody>
    </table></div>
  </div>
  {aviso_divisa}{sin_datos}

  {_bloque_reparto(c['reparto'])}
  {_bloque_aportacion(c.get('aportacion'))}
</section>"""


def _nombre_tipo(tipo: str) -> str:
    return {"etf": "ETF", "accion": "Acción", "cripto": "Cripto",
            "renta_fija": "R. fija"}.get(tipo, tipo)


def _dec_unidades(u: float) -> int:
    if u >= 100:
        return 2
    if u >= 1:
        return 4
    return 6


def _bloque_reparto(reparto: list[dict]) -> str:
    if not reparto:
        return ""
    filas = []
    for r in reparto:
        estado = r["estado"]
        filas.append(f"""<div class="reparto-fila reparto-{esc(estado)}">
      <div class="reparto-cab">
        <span class="reparto-nom">{esc(r['nombre'])}</span>
        <span class="reparto-cifras mono">
          <strong>{fmt_num(r['real_pct'], 1)}%</strong>
          <span class="tenue">objetivo {fmt_num(r['objetivo_pct'], 0)}%</span>
        </span>
      </div>
      <div class="reparto-pista">
        <span class="reparto-real" style="width:{min(r['real_pct'], 100):.1f}%"></span>
        <span class="reparto-objetivo" style="left:{min(r['objetivo_pct'], 100):.1f}%"></span>
      </div>
      <p class="reparto-txt">{esc(r['mensaje'])}</p>
    </div>""")

    return f"""<div class="sub-bloque">
    <h3 class="sub">Reparto frente a tu objetivo {ayuda_suelta('rebalanceo')}</h3>
    <p class="seccion-intro">La línea vertical marca tu objetivo; la barra, dónde estás.
    Las desviaciones de menos de {fmt_num(config.DESVIACION_AVISO_PCT, 0)} puntos no
    merecen que hagas nada.</p>
    <div class="reparto">{''.join(filas)}</div>
  </div>"""


def _bloque_aportacion(ap: dict | None) -> str:
    if not ap:
        return ""
    filas = "".join(f"""<div class="aport-fila">
      <span class="aport-nom">{esc(r['nombre'])}</span>
      <div class="aport-pista"><span style="width:{r['pct']:.1f}%"></span></div>
      <span class="aport-importe mono">{fmt_num(r['importe'], 2)} {MONEDA}</span>
    </div>""" for r in ap["reparto"])

    return f"""<div class="sub-bloque">
    <h3 class="sub">Tu próxima aportación de {fmt_num(ap['importe'], 0)} {MONEDA} {ayuda_suelta('dca')}</h3>
    <div class="aportacion">{filas}</div>
    <p class="nota-pie">{esc(ap['nota'])}</p>
  </div>"""


# ---------------------------------------------------------------------------
# ETFs
# ---------------------------------------------------------------------------

def seccion_etfs(etfs: list[dict], comparativa: dict | None) -> str:
    if not etfs:
        return ""
    tarjetas = "".join(_tarjeta_etf(e) for e in etfs)
    return f"""<section class="bloque-seccion">
  <h2>Tus ETFs y fondos</h2>
  <p class="seccion-intro">
    Un ETF no se juzga como una cripto: aquí no hay proyecto que investigar, hay un
    producto con características que puedes comparar objetivamente. El peso principal
    de la nota se lo lleva {ayuda('ter', 'la comisión')}, porque es lo único
    garantizado: la rentabilidad futura no la conoce nadie, la comisión la sabes desde
    el primer día.
  </p>
  {_bloque_comparativa(comparativa)}
  <div class="etfs">{tarjetas}</div>
</section>"""


def _bloque_comparativa(c: dict | None) -> str:
    if not c:
        return ""
    imp = c["impacto"]
    detalle = ""
    if imp:
        detalle = (f"Sobre {fmt_num(imp['capital'], 0)} {MONEDA} invertidos durante "
                   f"{imp['anios']} años al {fmt_num(imp['rentabilidad'], 0)}% anual, esa "
                   f"diferencia de comisión son <strong>{fmt_num(imp['coste'], 0)} "
                   f"{MONEDA}</strong> menos en tu bolsillo.")
    return f"""<div class="comparativa">
    <span class="eyebrow">Comparativa de comisiones</span>
    <p class="comparativa-txt">
      El más barato que sigues es <strong>{esc(c['barato']['nombre'])}</strong>
      ({fmt_num(c['barato']['ter_pct'], 2)}%) y el más caro
      <strong>{esc(c['caro']['nombre'])}</strong> ({fmt_num(c['caro']['ter_pct'], 2)}%).
      Diferencia: {fmt_num(c['diferencia_pct'], 2)} puntos porcentuales al año.
    </p>
    <p class="comparativa-txt">{detalle}</p>
    <p class="comparativa-aviso">{esc(c['aviso'])}</p>
  </div>"""


def _tarjeta_etf(e: dict) -> str:
    ind = e["indicadores"]
    ficha = e.get("ficha") or {}
    bloques = e["evaluacion"]["bloques"]
    pesos = e["evaluacion"]["pesos"]

    nombres = {
        "coste": ("Coste", "ter"),
        "tamanio": ("Tamaño del fondo", None),
        "diversificacion": ("Diversificación", "diversificacion"),
        "divisa": ("Divisa", "cobertura_divisa"),
        "trayectoria": ("Trayectoria", None),
    }
    barras = []
    for clave, (etiqueta, glosa) in nombres.items():
        b = bloques.get(clave)
        if not b:
            continue
        nota = b["nota"]
        calidad = "alta" if nota >= 70 else ("media" if nota >= 45 else "baja")
        titulo = ayuda(glosa, etiqueta) if glosa else esc(etiqueta)
        barras.append(f"""<div class="bloque">
      <div class="bloque-cab">
        <span class="bloque-nom">{titulo}<span class="peso">{pesos[clave]}%</span></span>
        <span class="bloque-nota nota-{calidad}">{nota:.0f}</span>
      </div>
      <div class="bloque-pista"><span class="bloque-relleno nota-{calidad}" style="width:{nota:.0f}%"></span></div>
      <p class="bloque-txt">{esc(b['texto'])}</p>
    </div>""")

    coste = e["evaluacion"].get("coste_30a")
    bloque_coste = ""
    if coste:
        bloque_coste = f"""<p class="desglose-pie">
      Traducido a dinero: {fmt_num(coste['capital'], 0)} {MONEDA} al
      {fmt_num(coste['rentabilidad'], 0)}% durante {coste['anios']} años serían
      {fmt_num(coste['final_sin_comision'], 0)} {MONEDA} sin comisiones y
      {fmt_num(coste['final_con_comision'], 0)} {MONEDA} con esta.
      La comisión se lleva {fmt_num(coste['coste'], 0)} {MONEDA}
      ({fmt_num(coste['coste_pct'], 1)}% del total).</p>"""

    señales = e.get("señales") or []
    lista = ("".join(f'<li class="mini mini-{esc(s["tono"])}"><strong>{esc(s["titulo"])}</strong> — {esc(s["dato"])}</li>'
                     for s in señales[:3]))
    lista = f'<ul class="mini-lista">{lista}</ul>' if lista else \
        '<p class="sin-senal">Sin señales. Comportamiento dentro de lo normal.</p>'

    holdings = ficha.get("top_holdings") or []
    bloque_holdings = ""
    if holdings:
        items = "".join(
            f'<li><span>{esc(h["nombre"])}</span><span class="mono">{fmt_num((h.get("peso") or 0)*100, 1)}%</span></li>'
            for h in holdings[:5] if h.get("nombre"))
        if items:
            bloque_holdings = f"""<details>
      <summary>Qué hay dentro (5 mayores posiciones)</summary>
      <ul class="holdings">{items}</ul>
    </details>"""

    ter = e["evaluacion"].get("ter_pct")
    etiqueta_cubierto = ('<span class="chip chip-info">Cubierto en '
                         f'{esc(config.MONEDA.upper())}</span>') if e["evaluacion"].get("cubierto") else ""

    return f"""<article class="etf etf-{esc(e['evaluacion']['color'])}">
  <header class="proyecto-cab">
    <div class="proyecto-id">
      <h3>{esc(e['nombre'])} <span class="ticker">{esc(e['simbolo'])}</span></h3>
      <p class="proyecto-cats">{esc(ficha.get('categoria') or ficha.get('familia') or 'ETF')}{'' if not etiqueta_cubierto else ' '}{etiqueta_cubierto}</p>
    </div>
    <div class="proyecto-nota">
      <span class="nota-num">{fmt_num(e['evaluacion']['nota'], 1)}</span>
      <span class="nota-de">/10</span>
      <span class="nota-nivel">{esc(e['evaluacion']['nivel'])}</span>
    </div>
  </header>

  <div class="proyecto-cifras">
    <div><span class="dato-lab">Precio</span><span class="mono">{fmt_precio(ind.get('precio'))}</span></div>
    <div><span class="dato-lab">{ayuda('ter', 'Comisión')}</span>
         <span class="mono">{fmt_num(ter, 2) + '%' if ter is not None else '—'}</span></div>
    <div><span class="dato-lab">1 año</span>
         <span class="mono {clase_signo(ind.get('cambio_1a_pct'))}">{fmt_pct(ind.get('cambio_1a_pct'), 1)}</span></div>
    <div><span class="dato-lab">Anualizado</span>
         <span class="mono {clase_signo(ind.get('rentabilidad_anualizada_pct'))}">{fmt_pct(ind.get('rentabilidad_anualizada_pct'), 1)}</span></div>
    <div><span class="dato-lab">{ayuda('volatilidad', 'Volatilidad')}</span>
         <span class="mono">{fmt_num(ind.get('volatilidad_1a_pct'), 0) if ind.get('volatilidad_1a_pct') else '—'}%</span></div>
    <div><span class="dato-lab">Desde máx. 52s</span>
         <span class="mono neg">{fmt_pct(ind.get('dist_max52s_pct'), 1)}</span></div>
    <div class="proyecto-spark">{sparkline((ind.get('serie') or [])[-252:], altura=40)}</div>
  </div>

  {lista}

  <details class="desglose">
    <summary>Ver cómo se ha calculado la nota</summary>
    <div class="bloques">{''.join(barras)}</div>
    {bloque_coste}
  </details>
  {bloque_holdings}
</article>"""


# ---------------------------------------------------------------------------
# Acciones
# ---------------------------------------------------------------------------

def seccion_acciones(acciones: list[dict]) -> str:
    if not acciones:
        return ""
    tarjetas = "".join(_tarjeta_accion(a) for a in acciones)
    return f"""<section class="bloque-seccion">
  <h2>Tus acciones</h2>
  <p class="seccion-intro">Empresas concretas. Aquí sí importan los fundamentales:
  {ayuda('per', 'el PER')}, {ayuda('dividendo', 'el dividendo')} y
  {ayuda('beta', 'la beta')} dicen más que cualquier indicador técnico.</p>
  <div class="rejilla-monedas">{tarjetas}</div>
</section>"""


def _tarjeta_accion(a: dict) -> str:
    ind, ficha = a["indicadores"], (a.get("ficha") or {})
    c1 = ind.get("cambio_1d_pct")

    señales = a.get("señales") or []
    lista = "".join(f'<li class="mini mini-{esc(s["tono"])}"><strong>{esc(s["titulo"])}</strong> — {esc(s["dato"])}</li>'
                    for s in señales[:3])
    lista = f'<ul class="mini-lista">{lista}</ul>' if lista else \
        '<p class="sin-senal">Sin señales. Comportamiento dentro de lo normal.</p>'

    per = ficha.get("per")
    div = ficha.get("dividendo_pct")
    beta = ficha.get("beta")

    return f"""<article class="moneda">
  <header class="moneda-cab">
    <div>
      <h3>{esc(a['nombre'])} <span class="ticker">{esc(a['simbolo'])}</span></h3>
      <p class="moneda-precio">{fmt_precio(ind.get('precio'))}
        <span class="delta {clase_signo(c1)}">{fmt_pct(c1, 2)} sesión</span></p>
      <p class="proyecto-cats">{esc(ficha.get('sector') or '')}</p>
    </div>
    <div class="moneda-spark">{sparkline((ind.get('serie') or [])[-252:])}
      <span class="spark-pie">1 año</span>
    </div>
  </header>

  {medidor_rsi(ind.get('rsi'))}

  <div class="datos">
    <div class="dato"><span class="dato-lab">{ayuda('per', 'PER')}</span>
      <span class="dato-val mono">{fmt_num(per, 1) if per else '—'}</span></div>
    <div class="dato"><span class="dato-lab">{ayuda('dividendo', 'Dividendo')}</span>
      <span class="dato-val mono">{fmt_num(div, 2) + '%' if div else '—'}</span></div>
    <div class="dato"><span class="dato-lab">{ayuda('beta', 'Beta')}</span>
      <span class="dato-val mono">{fmt_num(beta, 2) if beta else '—'}</span></div>
    <div class="dato"><span class="dato-lab">1 mes</span>
      <span class="dato-val mono {clase_signo(ind.get('cambio_1m_pct'))}">{fmt_pct(ind.get('cambio_1m_pct'))}</span></div>
    <div class="dato"><span class="dato-lab">1 año</span>
      <span class="dato-val mono {clase_signo(ind.get('cambio_1a_pct'))}">{fmt_pct(ind.get('cambio_1a_pct'))}</span></div>
    <div class="dato"><span class="dato-lab">{ayuda('correccion', 'Desde máx. 52s')}</span>
      <span class="dato-val mono neg">{fmt_pct(ind.get('dist_max52s_pct'))}</span></div>
    <div class="dato"><span class="dato-lab">{ayuda('market_cap', 'Capitalización')}</span>
      <span class="dato-val mono">{fmt_grande(ficha.get('capitalizacion'))}</span></div>
    <div class="dato"><span class="dato-lab">{ayuda('volatilidad', 'Volatilidad')}</span>
      <span class="dato-val mono">{fmt_num(ind.get('volatilidad_1a_pct'), 0) if ind.get('volatilidad_1a_pct') else '—'}%</span></div>
  </div>

  {lista}
</article>"""
