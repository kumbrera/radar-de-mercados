"""
Resolutor de identificadores.

El problema que resuelve: para poner un activo en cartera.csv hace falta su
símbolo de Yahoo (SXR8.DE, CEG, PUIG.MC), y esos símbolos no aparecen en
ninguna parte de tu bróker. Lo que sí aparece siempre es el **ISIN**, un código
de 12 caracteres tipo IE00B5BMR087 que identifica al activo de forma única en
todo el mundo.

Así que aquí aceptamos tres formas de nombrar un activo:

    IE00B5BMR087        el ISIN, tal cual lo copias de Trade Republic  <- lo más fiable
    Constellation Energy  el nombre, si no tienes el ISIN a mano
    CEG                 el símbolo de Yahoo, si ya lo sabes

Las dos primeras se traducen a símbolo consultando el buscador de Yahoo, y el
resultado se guarda en data/tickers.json para no repetir la consulta y para que
puedas revisar a qué se ha traducido cada cosa.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import config

FICHERO_TICKERS = config.DIR_DATOS / "tickers.json"

# Un ISIN son 2 letras de país + 9 alfanuméricos + 1 dígito de control
PATRON_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

# Un símbolo de Yahoo: letras/números, opcionalmente con sufijo de mercado.
# También cubrimos los índices (^GSPC) y los pares de divisas (EURUSD=X).
PATRON_SIMBOLO = re.compile(r"^[\^]?[A-Z0-9]{1,6}([.\-][A-Z]{1,4})?$|^[A-Z]{6}=X$")

# Preferimos las cotizaciones en euros: si el mismo fondo cotiza en varias
# bolsas, nos quedamos con la de la zona euro para no arrastrar tipo de cambio.
PREFERENCIA_MERCADOS = [".DE", ".MC", ".AS", ".PA", ".MI", ".L", ""]


def es_isin(texto: str) -> bool:
    return bool(PATRON_ISIN.match((texto or "").strip().upper()))


def parece_simbolo(texto: str) -> bool:
    return bool(PATRON_SIMBOLO.match((texto or "").strip().upper()))


# ---------------------------------------------------------------------------
# Caché en disco
# ---------------------------------------------------------------------------

def _cargar() -> dict:
    if not FICHERO_TICKERS.exists():
        return {}
    try:
        return json.loads(FICHERO_TICKERS.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _guardar(datos: dict) -> None:
    try:
        FICHERO_TICKERS.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Resolución
# ---------------------------------------------------------------------------

def _puntuar(candidato: dict, buscado: str) -> int:
    """Ordena los candidatos: primero euros, y fuera lo que no sea negociable."""
    simbolo = (candidato.get("simbolo") or "").upper()
    tipo = (candidato.get("tipo") or "").upper()

    if tipo in ("MUTUALFUND", "OPTION", "FUTURE"):
        return -100

    puntos = 0
    for i, sufijo in enumerate(PREFERENCIA_MERCADOS):
        if sufijo and simbolo.endswith(sufijo):
            puntos += (len(PREFERENCIA_MERCADOS) - i) * 10
            break
    else:
        if "." not in simbolo:
            puntos += 5          # mercado estadounidense

    if tipo in ("ETF", "EQUITY"):
        puntos += 20
    if simbolo == buscado.upper():
        puntos += 50
    return puntos


def resolver_uno(identificador: str, fuente, cache: dict,
                 avisos: list[str], forzar: bool = False) -> tuple[str, dict | None]:
    """
    Devuelve (simbolo_a_usar, informacion_de_la_traduccion).

    Si no consigue traducirlo, devuelve el identificador tal cual: puede que ya
    fuera un símbolo válido, y en el peor caso el informe dirá que no hay datos
    para ese activo en vez de fallar entero.
    """
    original = (identificador or "").strip()
    clave = original.upper()

    if clave in cache and not forzar:
        entrada = cache[clave]
        return entrada["simbolo"], entrada

    # Ya parece un símbolo y no es un ISIN: no hay nada que traducir.
    #
    # Con "forzar" saltamos este atajo. Se usa cuando un símbolo aparentemente
    # válido no ha devuelto datos: pasa con los códigos que enseña tu bróker
    # (Trade Republic muestra "B1B" para PUIG, que es el código de la bolsa
    # alemana y no existe en Yahoo). En ese caso hay que buscarlo igualmente.
    if parece_simbolo(clave) and not es_isin(clave) and not forzar:
        return original, None

    try:
        candidatos = fuente.buscar(original, limite=15) or []
    except Exception as e:  # noqa: BLE001
        # La búsqueda ha fallado (sin red, servicio caído). Un solo aviso:
        # decir además "no he encontrado nada" solo confundiría.
        avisos.append(
            f"No se ha podido buscar «{original}»: {e}. "
            "Se reintentará en la próxima ejecución."
        )
        return original, None

    validos = [c for c in candidatos if _puntuar(c, original) > -100]
    if not validos:
        avisos.append(
            f"No he encontrado ningún activo para «{original}». "
            "Comprueba el ISIN o prueba a escribir el nombre completo."
        )
        return original, None

    validos.sort(key=lambda c: _puntuar(c, original), reverse=True)
    elegido = validos[0]

    entrada = {
        "simbolo": elegido["simbolo"],
        "nombre": elegido.get("nombre") or elegido["simbolo"],
        "tipo": elegido.get("tipo"),
        "bolsa": elegido.get("bolsa"),
        "buscado": original,
        "alternativas": [
            {"simbolo": c["simbolo"], "nombre": c.get("nombre"), "bolsa": c.get("bolsa")}
            for c in validos[1:5]
        ],
    }
    cache[clave] = entrada
    return entrada["simbolo"], entrada


def resolver_posiciones(posiciones: list[tuple], fuente,
                        verbose: bool = True) -> tuple[list[tuple], dict, list[str]]:
    """
    Traduce los identificadores de todas las posiciones.

    Devuelve:
      • las posiciones con el símbolo ya traducido
      • un diccionario {símbolo: información de la traducción} para el informe
      • los avisos que hayan surgido
    """
    cache = _cargar()
    cache_inicial = json.dumps(cache, sort_keys=True)
    avisos: list[str] = []
    traducciones: dict[str, dict] = {}
    salida = []

    for fila in posiciones:
        identificador, tipo = fila[0], fila[1]
        resto = fila[2:]

        # Las criptos usan IDs de CoinGecko, que no tienen ISIN ni pasan por Yahoo
        if tipo == "cripto":
            salida.append(fila)
            continue

        simbolo, info = resolver_uno(identificador, fuente, cache, avisos)
        if info and simbolo.upper() != identificador.upper():
            traducciones[simbolo] = info
            if verbose:
                print(f"  · «{identificador}» → {simbolo} ({info['nombre'][:40]})",
                      flush=True)

        salida.append((simbolo, tipo, *resto))

    if json.dumps(cache, sort_keys=True) != cache_inicial:
        _guardar(cache)

    return salida, traducciones, avisos


def olvidar(identificador: str) -> bool:
    """Borra una traducción guardada, por si se resolvió mal y quieres reintentarla."""
    cache = _cargar()
    clave = (identificador or "").strip().upper()
    if clave in cache:
        del cache[clave]
        _guardar(cache)
        return True
    return False
