#!/usr/bin/env python3
"""
Radar de Mercados — informe diario de bolsa y criptomonedas.

Uso:
    python3 radar.py              Informe con datos reales
    python3 radar.py --demo       Informe con datos de prueba (sin internet)
    python3 radar.py --abrir      Abre el informe en el navegador al terminar
    python3 radar.py --sin-cache  Ignora la caché y pide todo de nuevo
    python3 radar.py --buscar "S&P 500"   Busca el símbolo de un ETF o acción
    python3 radar.py --web        Genera public/ lista para publicar en GitHub Pages
    python3 radar.py --silencio   No imprime nada por pantalla (para cron)

Esto NO es asesoramiento financiero. Ver la sección final del informe.
"""

from __future__ import annotations

import argparse
import sys
import traceback
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from radar import config, pipeline, report  # noqa: E402


def buscar_simbolo(texto: str, demo: bool = False) -> int:
    """
    Encuentra el símbolo de Yahoo de un ETF o acción.

    Los símbolos de los ETFs europeos son poco intuitivos (el mismo fondo puede
    ser CSPX.L en Londres y SXR8.DE en Xetra), así que en vez de adivinar,
    pregúntale al buscador y copia el resultado a config.py.
    """
    from radar.bolsa import obtener_fuente_bolsa

    fuente = obtener_fuente_bolsa(demo=demo, usar_cache=False, verbose=False)
    resultados = fuente.buscar(texto, limite=15)

    if not resultados:
        print(f"Sin resultados para «{texto}».")
        print("Prueba con menos palabras, por ejemplo solo «S&P 500» o «Vanguard All-World».")
        return 1

    print(f"\nResultados para «{texto}»:\n")
    print(f"  {'SÍMBOLO':<14}{'TIPO':<10}{'BOLSA':<20}NOMBRE")
    print("  " + "-" * 88)
    for r in resultados:
        tipo = {"ETF": "ETF", "EQUITY": "Acción", "INDEX": "Índice",
                "CURRENCY": "Divisa", "MUTUALFUND": "Fondo"}.get(r["tipo"], r["tipo"] or "?")
        print(f"  {r['simbolo']:<14}{tipo:<10}{(r['bolsa'] or '')[:18]:<20}{r['nombre'][:44]}")

    print("\nCopia el símbolo que quieras a WATCHLIST_ETFS o WATCHLIST_ACCIONES")
    print("en radar/config.py.\n")
    print("Consejo: para el mismo fondo suele haber varias cotizaciones. Elige la de")
    print("la bolsa donde vayas a comprar de verdad, y a ser posible en euros.\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Genera tu informe diario del mercado cripto.",
        epilog="Los ajustes (watchlist, umbrales, pesos) están en radar/config.py",
    )
    ap.add_argument("--demo", action="store_true",
                    help="usa datos sintéticos, sin tocar internet")
    ap.add_argument("--abrir", action="store_true",
                    help="abre el informe en el navegador al terminar")
    ap.add_argument("--sin-cache", action="store_true",
                    help="ignora la caché y vuelve a pedir todos los datos")
    ap.add_argument("--silencio", action="store_true",
                    help="no imprime progreso (útil para tareas programadas)")
    ap.add_argument("--salida", type=Path, default=None,
                    help="ruta del fichero HTML de salida")
    ap.add_argument("--buscar", metavar="TEXTO", default=None,
                    help="busca el símbolo de un ETF o acción y sale")
    ap.add_argument("--web", nargs="?", const="public", default=None,
                    metavar="CARPETA",
                    help="genera la carpeta lista para publicar (por defecto: public/)")
    ap.add_argument("--fragmento", action="store_true",
                    help="genera solo el fragmento HTML, sin <html> ni <head>")
    args = ap.parse_args()

    if args.buscar:
        return buscar_simbolo(args.buscar, demo=args.demo)

    verbose = not args.silencio

    if verbose:
        print("=" * 62)
        print("  RADAR DE MERCADOS")
        print("=" * 62)

    try:
        datos = pipeline.ejecutar(
            demo=args.demo,
            usar_cache=not args.sin_cache,
            verbose=verbose,
        )
    except Exception as e:  # noqa: BLE001
        print(f"\n[ERROR] {e}\n", file=sys.stderr)
        if verbose:
            traceback.print_exc()
        print("Prueba con:  python3 radar.py --demo", file=sys.stderr)
        return 1

    ruta = report.guardar(datos, args.salida, pagina_completa=not args.fragmento)

    publicado = None
    if args.web:
        from radar import web
        publicado = web.publicar(datos, args.web)
        borrados = web.limpiar_historico(args.web)
        if verbose:
            print("-" * 62)
            print(f"  Publicado en: {publicado['destino'].resolve()}")
            print(f"  Ficheros    : {len(publicado['escritos'])}")
            print(f"  Histórico   : {publicado['informes']} informe(s)"
                  + (f", {borrados} antiguo(s) borrado(s)" if borrados else ""))
            if publicado["sin_png"]:
                print(f"  Aviso       : sin iconos PNG ({', '.join(publicado['sin_png'])}).")
                print(f"                Instala Pillow para generarlos: pip install pillow")

    if verbose:
        n_alertas = len(datos["alertas"])
        b = datos.get("bolsa") or {}
        c = datos.get("cartera") or {}
        print("-" * 62)
        if b.get("lectura"):
            print(f"  Bolsa              : {b['lectura']['titular']}")
        print(f"  Cripto             : {datos['global']['titular']}")
        print(f"  ETFs / acciones    : {len(b.get('etfs') or [])} / {len(b.get('acciones') or [])}")
        print(f"  Criptos analizadas : {len(datos['watchlist'])}")
        print(f"  Proyectos puntuados: {len(datos['proyectos'])}")
        if not c.get("vacia"):
            # Formato español: punto de miles, coma decimal
            total = f"{c['total_actual']:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
            pct = f"{c['ganancia_pct']:+.1f}".replace(".", ",")
            print(f"  Cartera            : {total} {config.SIMBOLO_MONEDA} ({pct}%)")
        print(f"  Alertas            : {n_alertas if n_alertas else 'ninguna (día tranquilo)'}")
        print(f"  Peticiones a la API: {datos['meta']['peticiones']}")
        if datos["meta"]["fallos"]:
            print(f"  Avisos             : {len(datos['meta']['fallos'])} petición(es) fallida(s)")
        print("-" * 62)
        print(f"  Informe: {ruta}")
        print("=" * 62)

    if args.abrir or config.INFORME.abrir_navegador:
        webbrowser.open(ruta.resolve().as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
