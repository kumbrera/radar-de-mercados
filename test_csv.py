#!/usr/bin/env python3
"""
Comprobaciones del lector de cartera.csv.

Este fichero lo vas a editar tú desde el móvil, deprisa y probablemente con el
autocorrector metiendo mano. Así que el lector tiene que aguantar de todo: comas
decimales, punto y coma como separador, columnas desordenadas, espacios, tildes
y líneas mal escritas.

    python3 test_csv.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from radar import cartera_csv

FALLOS: list[str] = []


def escribir(contenido: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(contenido)
    f.close()
    return Path(f.name)


def comprobar(nombre, obtenido, esperado):
    ok = obtenido == esperado
    print(f"  [{'OK  ' if ok else 'FALLO'}] {nombre}")
    if not ok:
        print(f"         obtenido: {obtenido!r}")
        print(f"         esperado: {esperado!r}")
        FALLOS.append(nombre)


def comprobar_num(nombre, obtenido, esperado, tol=1e-6):
    ok = obtenido is not None and abs(obtenido - esperado) <= tol
    print(f"  [{'OK  ' if ok else 'FALLO'}] {nombre}: {obtenido} (esperado {esperado})")
    if not ok:
        FALLOS.append(nombre)


# ---------------------------------------------------------------------------
print("\nFormato básico")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "VWCE.DE,etf,0.78,127.90\n"
    "bitcoin,cripto,0.000572,60100\n"
))
comprobar("Lee dos posiciones", len(p), 2)
comprobar("Primera posición completa", p[0], ("VWCE.DE", "etf", 0.78, 127.90, None, None))
comprobar("Sin avisos", avisos, [])

# ---------------------------------------------------------------------------
print("\nFormato español: punto y coma + coma decimal")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(
    "identificador;tipo;unidades;precio_medio\n"
    "VWCE.DE;etf;0,78;127,90\n"
))
comprobar("Detecta el punto y coma", len(p), 1)
comprobar_num("Coma decimal en unidades", p[0][2], 0.78)
comprobar_num("Coma decimal en precio", p[0][3], 127.90)

# ---------------------------------------------------------------------------
print("\nNúmeros escritos de todas las formas posibles")
# ---------------------------------------------------------------------------
casos = [
    ("127.90", 127.90, "decimal con punto"),
    ("127,90", 127.90, "decimal con coma"),
    ("60100", 60100.0, "entero pelado"),
    ("60.100", 60.1, "un solo separador SIEMPRE es decimal"),
    ("60_100", 60100.0, "miles con guion bajo (inequívoco)"),
    ("1.234.567", 1234567.0, "varios separadores = miles"),
    ("0.178", 0.178, "decimal pequeño que antes se rompía"),
    ("0,178", 0.178, "el mismo con coma"),
    ("1.234,56", 1234.56, "formato español completo"),
    ("1,234.56", 1234.56, "formato inglés completo"),
    ("0.000572", 0.000572, "decimal muy pequeño"),
    ("0,000572", 0.000572, "decimal muy pequeño con coma"),
    (" 92.10 ", 92.10, "con espacios alrededor"),
    ("92.10 €", 92.10, "con símbolo de euro"),
]
for texto, esperado, descripcion in casos:
    try:
        obtenido = cartera_csv._a_numero(texto, "precio", 1)
        comprobar_num(f"{descripcion}: «{texto}»", obtenido, esperado)
    except cartera_csv.ErrorCartera as e:
        print(f"  [FALLO] {descripcion}: «{texto}» -> {e}")
        FALLOS.append(descripcion)

# ---------------------------------------------------------------------------
print("\nTolerancia con la cabecera")
# ---------------------------------------------------------------------------
p, _ = cartera_csv.leer(escribir(
    "Ticker,Clase,Cantidad,Precio de compra\n"
    "AAPL,Acción,0.178,221.40\n"
))
comprobar("Acepta sinónimos en la cabecera y tipo con tilde",
          p[0], ("AAPL", "accion", 0.178, 221.40, None, None))

# Columnas en otro orden
p, _ = cartera_csv.leer(escribir(
    "precio_medio,unidades,tipo,identificador\n"
    "127.90,0.78,etf,VWCE.DE\n"
))
comprobar("Acepta las columnas en cualquier orden",
          p[0], ("VWCE.DE", "etf", 0.78, 127.90, None, None))

# Columna extra que no conocemos: debe ignorarse sin molestar
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio,notas\n"
    "VWCE.DE,etf,0.78,127.90,comprado en Trade Republic\n"
))
comprobar("Ignora columnas de más", p[0], ("VWCE.DE", "etf", 0.78, 127.90, None, None))

# ---------------------------------------------------------------------------
print("\nComentarios y líneas en blanco")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(
    "# esto es un comentario\n"
    "\n"
    "identificador,tipo,unidades,precio_medio\n"
    "\n"
    "# compra de agosto\n"
    "VWCE.DE,etf,0.78,127.90\n"
    "\n"
    ",,,\n"
))
comprobar("Salta comentarios y líneas vacías", len(p), 1)
comprobar("Las líneas vacías no generan avisos", avisos, [])

# ---------------------------------------------------------------------------
print("\nVarias compras del mismo activo")
# ---------------------------------------------------------------------------
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "VWCE.DE,etf,1.0,100.00\n"
    "VWCE.DE,etf,1.0,200.00\n"
))
comprobar("Se agrupan en una sola posición", len(p), 1)
comprobar_num("Unidades sumadas", p[0][2], 2.0)
comprobar_num("Precio medio ponderado (100 y 200 -> 150)", p[0][3], 150.0)

# Ponderación desigual: 3 unidades a 100 y 1 a 200 -> (300+200)/4 = 125
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "AAPL,accion,3,100\n"
    "AAPL,accion,1,200\n"
))
comprobar_num("Ponderación desigual (3 a 100 + 1 a 200 = 125)", p[0][3], 125.0)
comprobar_num("Coste total conservado", p[0][2] * p[0][3], 500.0)



# ---------------------------------------------------------------------------
print("\nColumna «nombre» para el informe")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(
    "nombre,ticker,tipo,unidades,precio_medio,divisa\n"
    "S&P 500 EUR (Acc),SXR8.DE,etf,1.370175,131.37,EUR\n"
))
comprobar("El identificador sale del ticker", p[0][0], "SXR8.DE")
comprobar("El nombre se conserva para el informe", p[0][5], "S&P 500 EUR (Acc)")
comprobar("Las comas dentro del nombre no rompen nada", avisos, [])

# Sin ticker: el nombre hace de identificador
p, _ = cartera_csv.leer(escribir(
    "nombre,tipo,unidades,precio_medio\n"
    "Constellation Energy,accion,1,200\n"
))
comprobar("Sin ticker, el nombre identifica", p[0][0], "Constellation Energy")
comprobar("...y también se usa de nombre", p[0][5], "Constellation Energy")

# Ticker vacío pero columna presente
p, _ = cartera_csv.leer(escribir(
    "nombre,ticker,tipo,unidades,precio_medio\n"
    "Constellation Energy,,accion,1,200\n"
))
comprobar("Ticker vacío: tira del nombre", p[0][0], "Constellation Energy")

# Sin columna nombre: sigue funcionando como antes
p, _ = cartera_csv.leer(escribir(
    "ticker,tipo,unidades,precio_medio\n"
    "CEG,accion,1,200\n"
))
comprobar("Sin columna nombre, queda a None", p[0][5], None)

# Dos compras y solo la primera con nombre
p, _ = cartera_csv.leer(escribir(
    "nombre,ticker,tipo,unidades,precio_medio\n"
    "Mi ETF,VWCE.DE,etf,1,100\n"
    ",VWCE.DE,etf,1,200\n"
))
comprobar("El nombre sobrevive al agrupar compras", p[0][5], "Mi ETF")
comprobar_num("Y el precio medio sigue siendo correcto", p[0][3], 150.0)

# El mismo ticker en mayúsculas y minúsculas es el mismo activo
p, _ = cartera_csv.leer(escribir(
    "nombre,ticker,tipo,unidades,precio_medio\n"
    "Apple,AAPL,accion,1,100\n"
    "Apple,aapl,accion,1,200\n"
))
comprobar("Mayúsculas y minúsculas se agrupan igual", len(p), 1)
comprobar_num("Unidades sumadas pese al caso", p[0][2], 2.0)

# ---------------------------------------------------------------------------
print("\nVentas: unidades negativas")
# ---------------------------------------------------------------------------
# Compras 2 a 100, vendes 1 a 150. Te queda 1 unidad, y su precio medio sigue
# siendo 100: lo que ganaste al vender no cambia lo que te costó lo que queda.
p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "AAPL,accion,2,100\n"
    "AAPL,accion,-1,150\n"
))
comprobar("Queda una posición", len(p), 1)
comprobar_num("Unidades tras vender la mitad", p[0][2], 1.0)
comprobar_num("El precio medio NO cambia al vender", p[0][3], 100.0)
comprobar("Vender no genera avisos", avisos, [])

# Venta total: la posición desaparece del informe
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "AAPL,accion,2,100\n"
    "AAPL,accion,-2,150\n"
))
comprobar("Vender todo cierra la posición", len(p), 0)

# Vender más de lo que tienes no deja unidades negativas
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "AAPL,accion,1,100\n"
    "AAPL,accion,-5,150\n"
))
comprobar("Vender de más no deja unidades negativas", len(p), 0)

# Comprar, vender y volver a comprar
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "VWCE.DE,etf,1,100\n"
    "VWCE.DE,etf,-1,120\n"
    "VWCE.DE,etf,2,110\n"
))
comprobar_num("Tras cerrar y reabrir, unidades correctas", p[0][2], 2.0)
comprobar_num("Tras cerrar y reabrir, precio medio limpio", p[0][3], 110.0)

# Venta parcial con precios medios distintos:
# 3 a 100 y 1 a 200 -> medio 125. Vendes 2 -> quedan 2 al mismo medio de 125.
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "AAPL,accion,3,100\n"
    "AAPL,accion,1,200\n"
    "AAPL,accion,-2,180\n"
))
comprobar_num("Venta parcial: unidades", p[0][2], 2.0)
comprobar_num("Venta parcial: el medio ponderado se conserva", p[0][3], 125.0)

# Un precio negativo sí es un error
p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "AAPL,accion,1,-100\n"
))
comprobar("Un precio negativo se rechaza", len(p), 0)
comprobar("...y avisa", len(avisos), 1)

# ---------------------------------------------------------------------------
print("\nErrores: se salta la línea mala, no revienta el informe")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "VWCE.DE,etf,0.78,127.90\n"
    "MALA,tipo_inventado,1,100\n"
    "AAPL,accion,no_es_un_numero,100\n"
    ",etf,1,100\n"
    "bitcoin,cripto,0.001,60000\n"
))
comprobar("Las líneas buenas se leen igual", len(p), 2)
comprobar("Hay un aviso por cada línea mala", len(avisos), 3)
comprobar("El aviso dice el número de línea",
          all(l in a for l, a in zip(("3", "4", "5"), avisos)), True)
print("     avisos generados:")
for a in avisos:
    print(f"       · {a}")

# ---------------------------------------------------------------------------
print("\nCasos límite")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir("identificador,tipo,unidades,precio_medio\n"))
comprobar("Solo cabecera: cartera vacía sin error", (p, avisos), ([], []))

p, avisos = cartera_csv.leer(Path("/tmp/no_existe_este_fichero_12345.csv"))
comprobar("Fichero inexistente: cartera vacía sin error", (p, avisos), ([], []))

p, avisos = cartera_csv.leer(escribir("# solo comentarios\n\n"))
comprobar("Solo comentarios: cartera vacía", (p, avisos), ([], []))

p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "VWCE.DE,etf,0,127.90\n"
))
comprobar("Posición con 0 unidades se ignora", len(p), 0)
comprobar("...y avisa de ello", len(avisos), 1)

# Cabecera incompleta: aquí sí debe fallar con un mensaje claro
try:
    cartera_csv.leer(escribir("identificador,tipo\nVWCE.DE,etf\n"))
    print("  [FALLO] Cabecera incompleta debería lanzar error")
    FALLOS.append("cabecera incompleta")
except cartera_csv.ErrorCartera as e:
    comprobar("Cabecera incompleta lanza error explicativo", "unidades" in str(e), True)

try:
    cartera_csv.leer(escribir("a,b,c,d\n1,2,3,4\n"))
    print("  [FALLO] Cabecera irreconocible debería lanzar error")
    FALLOS.append("cabecera irreconocible")
except cartera_csv.ErrorCartera as e:
    comprobar("Cabecera irreconocible lanza error explicativo",
              "identificador" in str(e), True)

# BOM de Excel al principio del fichero
f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8-sig")
f.write("identificador,tipo,unidades,precio_medio\nVWCE.DE,etf,0.78,127.90\n")
f.close()
p, _ = cartera_csv.leer(Path(f.name))
comprobar("Aguanta el BOM que mete Excel", len(p), 1)

# ---------------------------------------------------------------------------
print("\nLa plantilla que se entrega es válida")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(cartera_csv.PLANTILLA))
comprobar("La plantilla se lee sin errores", (p, avisos), ([], []))

p, avisos = cartera_csv.leer(escribir(
    cartera_csv.PLANTILLA + "VWCE.DE,etf,0.78,127.90\n"))
comprobar("Y funciona al añadirle una línea", len(p), 1)


# ---------------------------------------------------------------------------
print("\nDivisa de compra (columna opcional)")
# ---------------------------------------------------------------------------
p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio,divisa\n"
    "CEG,accion,0.255264,235.05,EUR\n"
    "AAPL,accion,1,200,\n"
))
comprobar("Lee la divisa cuando está", p[0][4], "EUR")
comprobar("Divisa vacía queda a None", p[1][4], None)
comprobar("Sin avisos con divisa válida", avisos, [])

p, avisos = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio,divisa\n"
    "CEG,accion,1,200,DOLARES\n"
))
comprobar("Divisa inventada se ignora", p[0][4], None)
comprobar("...y avisa", len(avisos), 1)

p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio,moneda\n"
    "CEG,accion,1,200,eur\n"
))
comprobar("Acepta sinónimo «moneda» y minúsculas", p[0][4], "EUR")

# Sin la columna: todo sigue funcionando igual que antes
p, _ = cartera_csv.leer(escribir(
    "identificador,tipo,unidades,precio_medio\n"
    "VWCE.DE,etf,0.78,127.90\n"
))
comprobar("Sin columna divisa la posición queda completa",
          p[0], ("VWCE.DE", "etf", 0.78, 127.90, None, None))

# ---------------------------------------------------------------------------
print("\nLa cartera real que se entrega es válida")
# ---------------------------------------------------------------------------
from radar import resolver as _res

real, avisos_real = cartera_csv.leer(Path(__file__).parent / "cartera.csv")
comprobar("cartera.csv se lee sin avisos", avisos_real, [])
comprobar("Tiene 3 posiciones", len(real), 3)
invertido = sum(f[2] * f[3] for f in real)
comprobar_num("Total invertido", invertido, 295.22, 0.01)
for ident, _t, u, pr, div, nom in real:
    comprobar(f"{ident} declara divisa de compra", div, "EUR")
    comprobar(f"{ident} tiene nombre para el informe", bool(nom), True)
    comprobar(f"{ident} es un ISIN (no un ticker de bróker)", _res.es_isin(ident), True)

# Los ejemplos comentados del final tienen que ser válidos: si algún día les
# quita la almohadilla, deben funcionar a la primera.
texto = (Path(__file__).parent / "cartera.csv").read_text(encoding="utf-8")
# Una línea de datos comentada: exactamente 4 comas y sin espacios dentro.
# Así no confundimos la prosa de los comentarios con ejemplos reales.
ejemplos = [l[2:] for l in texto.splitlines()
            if l.startswith("# ") and l[2:].count(",") == 5
            and "nombre,isin" not in l]
comprobar("Hay ejemplos comentados que probar", len(ejemplos) >= 4, True)
descomentado = "nombre,isin,tipo,unidades,precio_medio,divisa\n" + "\n".join(ejemplos)
p_ej, avisos_ej = cartera_csv.leer(escribir(descomentado))
comprobar("Los ejemplos comentados son sintácticamente válidos", avisos_ej, [])
print(f"     ejemplos probados: {len(ejemplos)} -> {len(p_ej)} posición(es) resultante(s)")

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if FALLOS:
    print(f"{len(FALLOS)} COMPROBACIÓN(ES) FALLIDA(S):")
    for f_ in FALLOS:
        print(f"  - {f_}")
    sys.exit(1)
print("Todas las comprobaciones han pasado.")
print("=" * 60)
