"""
Lector de cartera.csv.

Este fichero existe para que puedas apuntar una compra desde el móvil sin tocar
código Python: abres cartera.csv en GitHub, tocas el lápiz, añades una línea y
guardas. Nada más.

Por eso el lector es deliberadamente tolerante:
  • acepta separador coma o punto y coma (Excel en España usa punto y coma)
  • acepta decimales con punto (127.90) o con coma (127,90)
  • acepta separadores de miles (60.100 o 60_100)
  • ignora líneas en blanco y comentarios que empiecen por #
  • da igual el orden de las columnas, se guía por la cabecera
  • si una línea está mal, la salta y te dice exactamente cuál y por qué,
    en vez de tumbar el informe entero
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

TIPOS_VALIDOS = {"etf", "accion", "cripto", "renta_fija"}

# Sinónimos que podrías escribir sin pensar, para que no falle por una tontería
ALIAS_TIPO = {
    "acción": "accion", "acciones": "accion", "stock": "accion", "share": "accion",
    "fondo": "etf", "fondos": "etf", "indexado": "etf", "fund": "etf",
    "crypto": "cripto", "criptomoneda": "cripto", "criptos": "cripto",
    "bono": "renta_fija", "bonos": "renta_fija", "rentafija": "renta_fija",
    "renta fija": "renta_fija",
}

ALIAS_COLUMNA = {
    "identificador": "id", "id": "id", "activo": "id", "simbolo": "id",
    "símbolo": "id", "ticker": "id", "isin": "id",
    # Opcional: cómo quieres que se llame en el informe. Si no la pones, se
    # usa el nombre oficial que devuelva la fuente de datos.
    "nombre": "nombre", "descripcion": "nombre", "descripción": "nombre",
    "tipo": "tipo", "clase": "tipo", "categoria": "tipo", "categoría": "tipo",
    "unidades": "unidades", "cantidad": "unidades", "participaciones": "unidades",
    "acciones": "unidades", "titulos": "unidades", "títulos": "unidades",
    "posiciones": "unidades", "posicion": "unidades", "posición": "unidades",
    "precio_medio": "precio", "precio medio": "precio", "precio": "precio",
    "preciomedio": "precio", "coste": "precio", "coste_medio": "precio",
    "precio_compra": "precio", "precio de compra": "precio",
    # Opcional: en qué moneda pagaste. Importa cuando el activo cotiza en una
    # divisa pero tu bróker te lo cobró en otra (Trade Republic te enseña en
    # euros acciones que cotizan en dólares).
    "divisa": "divisa", "moneda": "divisa", "moneda_precio": "divisa",
    "divisa_compra": "divisa", "currency": "divisa",
}

DIVISAS_VALIDAS = {"EUR", "USD", "GBP", "CHF", "GBX"}


class ErrorCartera(Exception):
    pass


def _normalizar_cabecera(nombre: str) -> str | None:
    limpio = (nombre or "").strip().lower().lstrip("﻿")
    return ALIAS_COLUMNA.get(limpio)


def _a_numero(texto: str, campo: str, linea: int,
              avisos: list[str] | None = None) -> float:
    """
    Convierte texto a número aceptando los formatos que la gente escribe de verdad.

    REGLA DE ORO: con un solo separador, SIEMPRE es decimal.

    Esto es deliberado. Adivinar si "60.100" son sesenta mil cien o sesenta coma
    uno es imposible, y equivocarse cuesta dinero de verdad: con la regla
    "lista" que tenía antes, "0.178" acciones de Apple se convertían en 178.
    Más vale una regla predecible que una inteligente.

    Solo se interpretan como separador de miles los casos inequívocos:
      "1.234.567" -> 1234567   (varios separadores iguales)
      "1.234,56"  -> 1234.56   (mezcla: el de la derecha es el decimal)
      "60_100"    -> 60100     (guion bajo, que nunca es decimal)

    Y cuando algo pueda haberse escrito con intención de miles ("60.100"),
    se interpreta como decimal pero se deja un aviso para que lo revises.
    """
    t = (texto or "").strip()
    for basura in (" ", " ", "_", "€", "$", "%"):
        t = t.replace(basura, "")
    if not t:
        raise ErrorCartera(f"línea {linea}: falta el valor de «{campo}»")

    n_comas, n_puntos = t.count(","), t.count(".")

    if n_comas and n_puntos:
        # Mezcla: el separador que aparece más a la derecha es el decimal
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif n_comas > 1:
        t = t.replace(",", "")            # 1,234,567
    elif n_puntos > 1:
        t = t.replace(".", "")            # 1.234.567
    elif n_comas == 1:
        entero, decimal = t.split(",")
        t = f"{entero}.{decimal}"
        if avisos is not None and len(decimal) == 3 and entero and not entero.startswith("0"):
            avisos.append(
                f"línea {linea}: he leído «{texto}» como {entero},{decimal} "
                f"(decimal). Si querías decir {entero}{decimal}, escríbelo sin "
                f"separador de miles."
            )
    elif n_puntos == 1:
        entero, decimal = t.split(".")
        if avisos is not None and len(decimal) == 3 and entero and not entero.startswith("0"):
            avisos.append(
                f"línea {linea}: he leído «{texto}» como {entero},{decimal} "
                f"(decimal). Si querías decir {entero}{decimal}, escríbelo sin "
                f"separador de miles."
            )

    try:
        valor = float(t)
    except ValueError:
        raise ErrorCartera(
            f"línea {linea}: «{texto}» no es un número válido en la columna «{campo}»"
        ) from None

    # Las unidades negativas son válidas: representan una venta.
    # Un precio negativo no tiene sentido en ningún caso.
    if valor < 0 and campo != "unidades":
        raise ErrorCartera(f"línea {linea}: «{campo}» no puede ser negativo")
    return valor


def _detectar_separador(texto: str) -> str:
    cabecera = next((l for l in texto.splitlines()
                     if l.strip() and not l.lstrip().startswith("#")), "")
    return ";" if cabecera.count(";") > cabecera.count(",") else ","


def leer(ruta: Path | str) -> tuple[list[tuple], list[str]]:
    """
    Devuelve (posiciones, avisos).

    posiciones: lista de (identificador, tipo, unidades, precio_medio)
    avisos: mensajes sobre líneas que se han saltado, para enseñártelos
    """
    ruta = Path(ruta)
    if not ruta.exists():
        return [], []

    texto = ruta.read_text(encoding="utf-8-sig")
    # Fuera comentarios y líneas vacías antes de pasárselo al lector de CSV
    utiles = [l for l in texto.splitlines()
              if l.strip() and not l.lstrip().startswith("#")]
    if not utiles:
        return [], []

    sep = _detectar_separador(texto)
    lector = csv.reader(io.StringIO("\n".join(utiles)), delimiter=sep)
    filas = list(lector)
    if not filas:
        return [], []

    cabecera = [_normalizar_cabecera(c) for c in filas[0]]

    # Si solo pones el nombre y no el ticker, el nombre hace de identificador
    # y se busca a qué activo corresponde.
    solo_nombre = "id" not in cabecera and "nombre" in cabecera

    if "id" not in cabecera and not solo_nombre:
        raise ErrorCartera(
            "cartera.csv: no encuentro la columna del identificador. La primera "
            "línea debe ser la cabecera, por ejemplo:\n"
            "    nombre,ticker,tipo,unidades,precio_medio"
        )
    for obligatoria, nombre in (("tipo", "tipo"), ("unidades", "unidades"),
                                ("precio", "precio_medio")):
        if obligatoria not in cabecera:
            raise ErrorCartera(f"cartera.csv: falta la columna «{nombre}» en la cabecera")

    idx = {c: i for i, c in enumerate(cabecera) if c}

    posiciones: list[tuple] = []
    avisos: list[str] = []

    for n, fila in enumerate(filas[1:], start=2):
        if not any(celda.strip() for celda in fila):
            continue
        try:
            if len(fila) < max(idx.values()) + 1:
                raise ErrorCartera(f"línea {n}: faltan columnas (encontradas {len(fila)})")

            nombre = ""
            if "nombre" in idx and idx["nombre"] < len(fila):
                nombre = fila[idx["nombre"]].strip()

            if solo_nombre:
                identificador = nombre
            else:
                identificador = fila[idx["id"]].strip()
                # Ticker vacío pero con nombre: tiramos del nombre
                if not identificador and nombre:
                    identificador = nombre

            if not identificador:
                raise ErrorCartera(
                    f"línea {n}: no hay ni ticker ni nombre con los que "
                    "identificar el activo"
                )

            crudo = fila[idx["tipo"]].strip().lower()
            tipo = ALIAS_TIPO.get(crudo, crudo)
            if tipo not in TIPOS_VALIDOS:
                raise ErrorCartera(
                    f"línea {n}: tipo «{fila[idx['tipo']]}» no válido. "
                    f"Usa uno de: {', '.join(sorted(TIPOS_VALIDOS))}"
                )

            unidades = _a_numero(fila[idx["unidades"]], "unidades", n, avisos)
            precio = _a_numero(fila[idx["precio"]], "precio_medio", n, avisos)

            divisa = None
            if "divisa" in idx and idx["divisa"] < len(fila):
                crudo_div = fila[idx["divisa"]].strip().upper()
                if crudo_div:
                    if crudo_div not in DIVISAS_VALIDAS:
                        avisos.append(
                            f"línea {n}: divisa «{crudo_div}» no reconocida, se ignora. "
                            f"Usa una de: {', '.join(sorted(DIVISAS_VALIDAS))}"
                        )
                    else:
                        divisa = crudo_div

            if unidades == 0:
                avisos.append(f"línea {n}: {identificador} tiene 0 unidades, se ignora")
                continue

            posiciones.append((identificador, tipo, unidades, precio, divisa, nombre))

        except ErrorCartera as e:
            avisos.append(str(e))

    return _agrupar(posiciones), avisos


def _agrupar(posiciones: list[tuple]) -> list[tuple]:
    """
    Si el mismo activo aparece varias veces, las suma calculando el precio medio
    ponderado. Así puedes añadir una línea por cada compra sin hacer cuentas:

        VWCE.DE,etf,0.78,127.90     <- primera compra
        VWCE.DE,etf,0.40,131.20     <- segunda compra, un mes después

    y el sistema entiende que tienes 1,18 participaciones a 128,02 de media.
    """
    acumulado: dict[tuple[str, str], dict] = {}
    orden: list[tuple[str, str]] = []

    for identificador, tipo, unidades, precio, divisa, nombre in posiciones:
        clave = (identificador.upper(), tipo)
        if clave not in acumulado:
            acumulado[clave] = {"unidades": 0.0, "coste": 0.0, "compras": 0,
                                "ventas": 0, "precio": precio, "divisa": divisa,
                                "nombre": nombre, "id": identificador}
            orden.append(clave)
        a = acumulado[clave]
        # El nombre de la primera línea manda, pero si aquella no lo traía y
        # esta sí, lo aprovechamos
        if nombre and not a["nombre"]:
            a["nombre"] = nombre

        if unidades >= 0:
            a["unidades"] += unidades
            a["coste"] += unidades * precio
            a["compras"] += 1
        else:
            # VENTA. Reduce las unidades, y el coste baja en proporción al
            # precio medio que llevabas, no al precio al que has vendido.
            # Así el precio medio de lo que te queda no cambia, que es como
            # funciona la contabilidad de coste medio (y como lo entiende
            # Hacienda para lo que aún no has vendido).
            vendidas = min(-unidades, a["unidades"])
            if a["unidades"] > 0:
                medio = a["coste"] / a["unidades"]
                a["coste"] -= vendidas * medio
            a["unidades"] -= vendidas
            a["ventas"] += 1

        if divisa and not a["divisa"]:
            a["divisa"] = divisa

    salida = []
    for clave in orden:
        a = acumulado[clave]

        # Posición cerrada del todo: fuera del informe
        if a["unidades"] <= 1e-12:
            continue

        if a["compras"] == 1 and a["ventas"] == 0:
            # Una sola compra: usamos su precio tal cual. Multiplicar y dividir
            # por las mismas unidades introduce ruido de coma flotante
            # (221,40 se convertía en 221,40000000000003).
            precio_medio = a["precio"]
        else:
            precio_medio = round(a["coste"] / a["unidades"], 10) if a["unidades"] else 0.0

        salida.append((a["id"], clave[1], round(a["unidades"], 10),
                       precio_medio, a["divisa"], a["nombre"] or None))
    return salida


PLANTILLA = """# Tu cartera. Una línea por compra.
#
# Cómo añadir una compra desde el móvil:
#   1. Abre este fichero en GitHub y toca el lápiz (editar)
#   2. Añade una línea al final
#   3. Guarda (Commit changes)
#   4. En 2-3 minutos la página se habrá actualizado sola
#
# identificador : para cripto, el ID de CoinGecko (bitcoin, ethereum, solana)
#                 para bolsa, el símbolo de Yahoo (VWCE.DE, AAPL, TEF.MC)
# tipo          : etf | accion | cripto | renta_fija
# unidades      : pueden ser decimales (0.78 participaciones)
# precio_medio  : a cuánto te salió cada unidad
#
# Si compras el mismo activo dos veces, añade otra línea: el sistema suma las
# unidades y calcula el precio medio ponderado por ti.
#
# Los decimales valen con punto o con coma. Las líneas que empiezan por # se
# ignoran, así que puedes usarlas para tomar notas.

identificador,tipo,unidades,precio_medio
"""
