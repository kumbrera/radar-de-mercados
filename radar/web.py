"""
Publicación web: convierte el informe en una página instalable en el móvil.

`construir_html()` devuelve un fragmento (sin <html>, <head> ni <body>). Aquí lo
envolvemos en un documento completo con lo que hace falta para que, al añadirlo
a la pantalla de inicio del móvil, se comporte como una app: se abre a pantalla
completa, sin barra de navegador, con su icono y su color.
"""

from __future__ import annotations

import base64
import json
import shutil
from datetime import datetime
from pathlib import Path

from . import config
from .report import construir_html, esc

# Color del tema para la barra de estado del móvil. Coincide con --ground.
TEMA_CLARO = "#f3f5f8"
TEMA_OSCURO = "#0e1217"


# ---------------------------------------------------------------------------
# Icono
# ---------------------------------------------------------------------------

ICONO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="112" fill="#0d6f79"/>
  <g fill="none" stroke="#ffffff" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="256" cy="256" r="150" stroke-width="12" opacity="0.28"/>
    <circle cx="256" cy="256" r="96"  stroke-width="12" opacity="0.42"/>
    <circle cx="256" cy="256" r="42"  stroke-width="12" opacity="0.6"/>
    <polyline points="106,318 166,262 226,290 286,190 346,232 406,148"
              stroke-width="26"/>
  </g>
  <circle cx="406" cy="148" r="26" fill="#ffffff"/>
</svg>"""


def _icono_png(tamanio: int) -> bytes | None:
    """Rasteriza el icono. Si no hay librería disponible, devuelve None."""
    try:
        import cairosvg  # type: ignore
        return cairosvg.svg2png(bytestring=ICONO_SVG.encode(),
                                output_width=tamanio, output_height=tamanio)
    except Exception:  # noqa: BLE001
        pass
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except ImportError:
        return None

    # Plan B sin dependencias de SVG: dibujamos el icono directamente
    escala = 4
    lado = tamanio * escala
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radio = int(lado * 0.22)
    d.rounded_rectangle([0, 0, lado - 1, lado - 1], radius=radio, fill=(13, 111, 121, 255))

    c = lado / 2
    for r, op, gr in ((0.293, 72, 0.023), (0.1875, 107, 0.023), (0.082, 153, 0.023)):
        rr, g = lado * r, max(1, int(lado * gr))
        d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=(255, 255, 255, op), width=g)

    puntos = [(0.207, 0.621), (0.324, 0.512), (0.441, 0.566),
              (0.559, 0.371), (0.676, 0.453), (0.793, 0.289)]
    xy = [(p[0] * lado, p[1] * lado) for p in puntos]
    d.line(xy, fill=(255, 255, 255, 255), width=int(lado * 0.051), joint="curve")
    rp = lado * 0.051
    d.ellipse([xy[-1][0] - rp, xy[-1][1] - rp, xy[-1][0] + rp, xy[-1][1] + rp],
              fill=(255, 255, 255, 255))

    img = img.resize((tamanio, tamanio), Image.LANCZOS)
    import io
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Documento completo
# ---------------------------------------------------------------------------

def envolver(fragmento: str, *, para_web: bool = True) -> str:
    """Envuelve el fragmento del informe en un documento HTML completo."""
    icono_inline = ("data:image/svg+xml;base64,"
                    + base64.b64encode(ICONO_SVG.encode()).decode())

    # En la versión web enlazamos manifest e iconos como ficheros; en la versión
    # local (un HTML suelto) va todo incrustado para que funcione con doble clic.
    if para_web:
        cabecera_app = """
  <link rel="manifest" href="manifest.webmanifest">
  <link rel="icon" type="image/svg+xml" href="icono.svg">
  <link rel="apple-touch-icon" href="icono-180.png">"""
    else:
        cabecera_app = f"""
  <link rel="icon" type="image/svg+xml" href="{icono_inline}">"""

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="{TEMA_CLARO}" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="{TEMA_OSCURO}" media="(prefers-color-scheme: dark)">
  <meta name="description" content="Informe diario de bolsa y criptomonedas, con la cartera y el glosario.">
  <meta name="robots" content="noindex, nofollow">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="Radar">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <meta name="mobile-web-app-capable" content="yes">{cabecera_app}
{fragmento}
</html>"""


def _partir(fragmento: str) -> tuple[str, str]:
    """
    Separa lo que va en <head> (título, fuentes, estilos) de lo que va en <body>.

    El fragmento empieza con <title>, los <link> de fuentes y el <style>; a
    partir de ahí es contenido.
    """
    marca = '<div class="pagina">'
    corte = fragmento.find(marca)
    if corte == -1:
        return "", fragmento
    return fragmento[:corte], fragmento[corte:]


def construir_pagina(datos: dict, *, para_web: bool = True) -> str:
    cabeza, cuerpo = _partir(construir_html(datos))
    return envolver(f"{cabeza}</head>\n<body>\n{cuerpo}\n</body>", para_web=para_web)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def manifest() -> str:
    return json.dumps({
        "name": "Radar de Mercados",
        "short_name": "Radar",
        "description": "Informe diario de bolsa y criptomonedas, con tu cartera.",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": TEMA_CLARO,
        "theme_color": TEMA_CLARO,
        "lang": "es",
        "icons": [
            {"src": "icono.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
            {"src": "icono-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icono-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "icono-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Publicación
# ---------------------------------------------------------------------------

def publicar(datos: dict, destino: Path | str = "public") -> dict:
    """
    Genera la carpeta lista para GitHub Pages:

        public/
          index.html              el informe de hoy
          historico/2026-08-21.html
          manifest.webmanifest
          icono.svg  icono-192.png  icono-512.png  icono-180.png
          .nojekyll

    Devuelve un resumen de lo que se ha escrito.
    """
    destino = Path(destino)
    historico = destino / "historico"
    destino.mkdir(parents=True, exist_ok=True)
    historico.mkdir(parents=True, exist_ok=True)

    pagina = construir_pagina(datos, para_web=True)
    hoy = datetime.now().strftime("%Y-%m-%d")

    escritos = []

    (destino / "index.html").write_text(pagina, encoding="utf-8")
    escritos.append("index.html")

    (historico / f"{hoy}.html").write_text(pagina, encoding="utf-8")
    escritos.append(f"historico/{hoy}.html")

    (destino / "manifest.webmanifest").write_text(manifest(), encoding="utf-8")
    escritos.append("manifest.webmanifest")

    (destino / "icono.svg").write_text(ICONO_SVG, encoding="utf-8")
    escritos.append("icono.svg")

    # GitHub Pages ignora por defecto lo que empieza por guion bajo si no está
    # este fichero. Es un clásico de "por qué no se ve mi página".
    (destino / ".nojekyll").write_text("", encoding="utf-8")

    sin_png = []
    for tamanio in (180, 192, 512):
        png = _icono_png(tamanio)
        ruta = destino / f"icono-{tamanio}.png"
        if png:
            ruta.write_bytes(png)
            escritos.append(ruta.name)
        elif not ruta.exists():
            sin_png.append(ruta.name)

    (destino / "historico" / "index.html").write_text(
        _indice_historico(historico), encoding="utf-8")
    escritos.append("historico/index.html")

    return {"destino": destino, "escritos": escritos, "sin_png": sin_png,
            "informes": len(list(historico.glob("*.html"))) - 1}


def _indice_historico(carpeta: Path) -> str:
    """Una página simple para poder volver a informes de días anteriores."""
    dias = sorted((p.stem for p in carpeta.glob("*.html") if p.stem != "index"),
                  reverse=True)
    if not dias:
        items = "<li>Todavía no hay informes anteriores.</li>"
    else:
        items = "".join(
            f'<li><a href="{esc(d)}.html">{esc(_fecha_es(d))}</a></li>' for d in dias)

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="robots" content="noindex, nofollow">
  <title>Informes anteriores</title>
  <style>
    :root {{ --f: #f3f5f8; --s: #fff; --t: #161c23; --m: #66747f; --l: #dce2e9; --a: #0d6f79; }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --f: #0e1217; --s: #161b22; --t: #e6ebf1; --m: #85929f; --l: #29313a; --a: #4dc3cd; }}
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--f); color: var(--t); padding: 32px 20px;
      font-family: -apple-system, "Segoe UI", system-ui, sans-serif; line-height: 1.6; }}
    main {{ max-width: 640px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }}
    h1 {{ font-size: 1.6rem; margin: 0; letter-spacing: -.02em; }}
    a {{ color: var(--a); }}
    ul {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }}
    li {{ background: var(--s); border: 1px solid var(--l); border-radius: 9px; }}
    li a {{ display: block; padding: 13px 16px; text-decoration: none; }}
    li a:hover {{ background: var(--l); }}
    .volver {{ font-size: .9rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Informes anteriores</h1>
    <p class="volver"><a href="../">&larr; Volver al informe de hoy</a></p>
    <ul>{items}</ul>
  </main>
</body>
</html>"""


_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_es(iso: str) -> str:
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d.day} de {_MESES[d.month - 1]} de {d.year}"
    except ValueError:
        return iso


def limpiar_historico(destino: Path | str = "public", conservar: int = 90) -> int:
    """Borra los informes más antiguos para que el repositorio no crezca sin fin."""
    carpeta = Path(destino) / "historico"
    if not carpeta.exists():
        return 0
    dias = sorted((p for p in carpeta.glob("*.html") if p.stem != "index"),
                  key=lambda p: p.stem, reverse=True)
    borrados = 0
    for viejo in dias[conservar:]:
        viejo.unlink()
        borrados += 1
    if borrados:
        (carpeta / "index.html").write_text(_indice_historico(carpeta), encoding="utf-8")
    return borrados
