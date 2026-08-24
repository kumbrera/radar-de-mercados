# Radar de Mercados

Tu sistema personal de seguimiento de **bolsa y criptomonedas**. Cada mañana te
genera un informe en HTML que responde a cinco preguntas:

1. **¿Qué ha pasado hoy?** — índices (S&P 500, Nasdaq, IBEX, Euro Stoxx), VIX, EUR/USD, y el estado del mercado cripto.
2. **¿Se ha salido algo de lo normal?** — alertas con contexto, con umbrales distintos para bolsa y para cripto.
3. **¿Cómo va mi cartera?** — valor, resultado, desviación respecto a tu reparto objetivo.
4. **¿Dónde va la próxima aportación?** — rebalanceo por aportación, sin vender ni tributar.
5. **¿Qué merece que investigue?** — evaluación de tus ETFs y escaneo de 250 criptos con scoring transparente.

Todo término técnico lleva un botón **?** que despliega su explicación. La idea es
que después de leerlo 20 veces ya no lo necesites.

**¿Lo quieres en el móvil, generándose solo cada mañana sin tener el ordenador
encendido?** Sigue [PUESTA_EN_MARCHA.md](PUESTA_EN_MARCHA.md): GitHub lo ejecuta
en la nube y te queda un icono en la pantalla de inicio.

> **Esto no es asesoramiento financiero.** El sistema aplica fórmulas públicas a
> datos públicos. No predice el futuro, no conoce tu situación y no sabe qué
> comprar. Lo que hace es filtrar ruido y obligarte a mirar métricas que importan.

---

## Instalación (5 minutos)

Necesitas Python 3.10 o superior. Comprueba lo que tienes:

```bash
python3 --version
```

Si no lo tienes, descárgalo de [python.org](https://www.python.org/downloads/).
En Windows, marca la casilla **"Add Python to PATH"** durante la instalación.

Luego, dentro de la carpeta del proyecto:

```bash
pip install -r requirements.txt
```

Solo instala una librería (`requests`). El resto es Python estándar.

---

## Uso

**Pruébalo primero sin tocar internet**, para ver qué genera:

```bash
python3 radar.py --demo --abrir
```

Esto crea un informe con datos sintéticos y lo abre en el navegador. Sirve para
ver el formato antes de conectar nada.

**Cuando quieras datos reales:**

```bash
python3 radar.py --abrir
```

Tarda entre 1 y 3 minutos. La mayor parte del tiempo es esperar entre peticiones
para no saturar la API gratuita de CoinGecko.

El informe se guarda en `salidas/informe-AAAA-MM-DD.html`.

### Todas las opciones

| Comando | Qué hace |
|---|---|
| `python3 radar.py` | Informe con datos reales |
| `python3 radar.py --demo` | Datos sintéticos, sin internet |
| `python3 radar.py --abrir` | Abre el informe al terminar |
| `python3 radar.py --sin-cache` | Ignora la caché, vuelve a pedir todo |
| `python3 radar.py --silencio` | Sin mensajes por pantalla (para tareas programadas) |
| `python3 radar.py --salida ruta.html` | Elige dónde guardar el informe |
| `python3 radar.py --buscar "S&P 500"` | Busca el símbolo de un ETF o acción |
| `python3 radar.py --web` | Genera `public/`, lista para publicar en GitHub Pages |

---

## Personalización

Todo lo configurable está en **`radar/config.py`**, comentado línea a línea.
Lo que más te va a interesar:

### Tu watchlist

```python
WATCHLIST = [
    "bitcoin",
    "ethereum",
    "solana",
    # ...
]
```

Son los **IDs de CoinGecko**, que ves en la URL de cada moneda:
`coingecko.com/es/monedas/`**`chainlink`** → el ID es `chainlink`.

Máximo recomendado: 12-15. Cada una consume una petición a la API.


### Tus ETFs y acciones

```python
WATCHLIST_ETFS = ["CSPX.L", "VWCE.DE", "IBCF.DE"]
WATCHLIST_ACCIONES = ["AAPL", "TEF.MC", "ITX.MC"]
```

Son símbolos de Yahoo Finance. **No los adivines**: el mismo ETF puede ser
`CSPX.L` en Londres y `SXR8.DE` en Xetra. Búscalos:

```bash
python3 radar.py --buscar "iShares Core S&P 500"
python3 radar.py --buscar "Vanguard All-World"
```

Te devuelve una tabla con símbolo, tipo, bolsa y nombre. Copia el que
corresponda a la bolsa donde compras de verdad.

Sufijos habituales: `.MC` Madrid · `.DE` Xetra · `.L` Londres · `.AS` Ámsterdam
· `.PA` París · `.MI` Milán · sin sufijo, Estados Unidos.

### Tu cartera — va en `cartera.csv`, no en el código

Aquí está lo más útil del sistema, y es lo único que tocarás con frecuencia.
Una línea por compra:

```
nombre,isin,tipo,unidades,precio_medio,divisa
S&P 500 EUR (Acc),IE00B5BMR087,etf,1.370175,131.37,EUR
Constellation Energy,US21037T1097,accion,0.255264,235.05,EUR
Bitcoin,bitcoin,cripto,0.000572,60100,EUR
```

- **nombre**: cómo quieres verlo en el informe. Lo eliges tú.
- **isin**: el código de 12 caracteres de tu bróker. **Usa el ISIN, no el
  ticker**: el ticker cambia según la bolsa (PUIG es `PUIG` en Madrid y `B1B`
  en Alemania), el ISIN es el mismo en todo el mundo. Para criptos, el nombre
  en minúscula. También vale un ticker o un nombre: se resuelven buscándolos.
- **tipo**: `etf` · `accion` · `cripto` · `renta_fija`
- **unidades**: decimales, tal cual te las da el bróker. **En negativo si es una venta.**
- **precio_medio**: a cuánto te salió cada unidad
- **divisa**: en qué moneda te cobraron A TI. Con Trade Republic siempre `EUR`,
  aunque el activo cotice en dólares. Sin esto el coste se convertiría dos veces
  y las ganancias saldrían mal.

Está en un CSV a propósito: puedes editarlo **desde el móvil** en GitHub sin
tocar código. Si compras dos veces lo mismo, añade otra línea y el sistema
calcula el precio medio ponderado por ti.

El lector aguanta comas o puntos decimales, punto y coma como separador, las
columnas en cualquier orden y comentarios con `#`. Si una línea está mal, se
la salta y te lo dice en el propio informe en vez de romperse.

Y tu reparto objetivo:

```python
REPARTO_OBJETIVO = {"etf": 70, "cripto": 15, "accion": 15}
DESVIACION_AVISO_PCT = 5.0     # cuánto te puedes desviar antes del aviso
APORTACION_MENSUAL = 100.0     # 0 si no aportas de forma regular
```

Con eso, el informe te calcula cada día el valor de la cartera, el resultado, la
desviación respecto al objetivo y **cómo repartir la próxima aportación** para
volver al objetivo sin vender nada. Rebalancear comprando en vez de vendiendo
evita comisiones de venta y no genera ganancias que tributen: para carteras
pequeñas la diferencia es grande.

### Dónde busca proyectos nuevos

```python
MCAP_MIN = 40_000_000       # por debajo: demasiado pequeño, fácil de manipular
MCAP_MAX = 4_000_000_000    # por encima: ya es gigante, poco recorrido
VOLUMEN_MIN_24H = 3_000_000 # liquidez mínima para poder entrar y salir
```

### Qué te importa más al puntuar proyectos

```python
PESOS_SCORING = {
    "liquidez": 18,
    "desarrollo": 20,
    "comunidad": 12,
    "momento": 15,
    "valoracion": 15,
    "tokenomics": 20,
}
```

Deben sumar 100. Si te preocupa sobre todo la dilución, sube `tokenomics`. Si te
importa que haya código de verdad detrás, sube `desarrollo`.

### Cuándo salta cada alerta

```python
rsi_sobreventa = 30.0
rsi_sobrecompra = 70.0
caida_fuerte_24h = -7.0
volumen_anomalo = 2.0
```

Si te salen demasiadas alertas, endurece los umbrales (RSI 25/75, caídas del -10%).

---

## Ejecutarlo automáticamente cada mañana

### macOS y Linux

```bash
crontab -e
```

Añade esta línea (informe cada día a las 8:00):

```
0 8 * * * cd /ruta/a/cripto-radar && /usr/bin/python3 radar.py --silencio
```

Sustituye `/ruta/a/cripto-radar` por la ruta real (ejecuta `pwd` dentro de la
carpeta para saberla).

### Windows

Abre el **Programador de tareas** → Crear tarea básica → Diariamente →
Iniciar un programa:

- Programa: `python`
- Argumentos: `radar.py --silencio`
- Iniciar en: la carpeta del proyecto

---

## Qué APIs usa y cuánto cuestan

| Servicio | Para qué | Coste |
|---|---|---|
| [CoinGecko](https://www.coingecko.com/es/api) | Cripto: precios, capitalización, volumen, GitHub, comunidad | **Gratis**, sin registro |
| [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) | Índice de miedo y codicia | **Gratis** |
| Yahoo Finance | Bolsa: índices, ETFs, acciones, TER, PER, dividendos | **Gratis**, sin registro |
| [Stooq](https://stooq.com) | Plan B si Yahoo falla | **Gratis** |

**Coste total: 0 €.** Sin tarjeta, sin registro, sin límite de días.

El plan gratuito de CoinGecko permite del orden de 10-30 peticiones por minuto.
El sistema respeta ese límite solo: pausa entre peticiones, reintenta con espera
creciente si le dan un 429, y cachea las respuestas 30 minutos.

Un informe completo consume unas **30-35 peticiones** a CoinGecko y unas **35-40**
a Yahoo, muy lejos de los límites de ambos.

Yahoo Finance no es una API oficial con contrato de servicio: es un endpoint
público que se usa desde hace años pero que podría cambiar. Por eso el cliente
tiene Stooq como plan B y, si un símbolo falla, lo informa y sigue con el resto
en vez de tumbar el informe entero.

Si algún día quieres ir más rápido, CoinGecko regala una clave "Demo" con más
margen. Se activa sola con:

```bash
export COINGECKO_API_KEY="tu_clave"
```

---

## Qué hay dentro

```
cripto-radar/
├── radar.py                 Punto de entrada. Es el que ejecutas.
├── cartera.csv              ⭐ Tus posiciones. Lo editas desde el móvil.
├── PUESTA_EN_MARCHA.md      Guía para publicarlo y tenerlo en el móvil
├── requirements.txt
├── test_indicadores.py      Comprobaciones de los cálculos técnicos
├── test_cartera.py          Comprobaciones de la cartera y los ETFs
├── test_csv.py              Comprobaciones del lector de cartera.csv
│
├── .github/workflows/
│   └── informe.yml          Ejecución diaria en la nube y publicación
│
├── radar/
│   ├── config.py            ⭐ Lo único que necesitas tocar
│   ├── indicators.py        RSI, medias, MACD, volatilidad, CAGR, drawdown
│   │
│   ├── sources.py           Cliente de CoinGecko + datos demo
│   ├── scoring.py           Puntuación de proyectos cripto y red flags
│   ├── signals.py           Señales de cripto
│   │
│   ├── bolsa.py             Cliente de Yahoo Finance + Stooq + datos demo
│   ├── scoring_bolsa.py     Evaluación de ETFs (TER, tamaño, divisa...)
│   ├── signals_bolsa.py     Señales de bolsa, con umbrales propios
│   ├── cartera.py           Posiciones, resultado, rebalanceo, aportaciones
│   │
│   ├── cartera_csv.py       Lector tolerante de cartera.csv
│   ├── web.py               Página instalable, manifest e iconos
│   ├── glossary.py          Textos del glosario y las FAQs
│   ├── report.py            Construcción del HTML (cripto y estructura)
│   ├── report_bolsa.py      Secciones de bolsa y cartera
│   ├── estilos.py           Hoja de estilos
│   └── pipeline.py          Orquestador
│
├── salidas/                 Los informes generados
└── data/                    Caché e histórico (SQLite)
```

### El histórico

Cada ejecución guarda precios, RSI y notas en `data/historico.sqlite3`. Con el
tiempo tendrás una serie propia para comparar. Puedes consultarla con cualquier
visor de SQLite o desde Python:

```python
import sqlite3
con = sqlite3.connect("data/historico.sqlite3")
for fila in con.execute(
    "SELECT fecha, precio, rsi FROM lecturas WHERE moneda='bitcoin' ORDER BY fecha"
):
    print(fila)
```

---

## Comprobar que los cálculos son correctos

```bash
python3 test_indicadores.py    # RSI, medias, MACD, volatilidad, cruces
python3 test_cartera.py        # cartera, divisas, rebalanceo, ETFs
python3 test_csv.py            # lector de cartera.csv
```

Los tres se ejecutan también en GitHub antes de publicar cada informe: si un
cálculo se rompe, la página se queda con la versión anterior en vez de publicar
cifras equivocadas.

El RSI se valida contra la serie de referencia de J. Welles Wilder (1978) y
contra los 19 valores que publica StockCharts para esa misma serie. Si esas
comprobaciones pasan, tu RSI coincide con el que verías en TradingView.

Las medias móviles se contrastan contra pandas. La aritmética de la cartera
(conversión de divisas, pesos, desviaciones, reparto de la aportación) se
comprueba con números redondos verificables a mano, y el interés compuesto de
las comisiones con los mismos valores que aparecen en el glosario, para que el
texto y el código no puedan separarse.

---

## Cómo se puntúa un proyecto

Seis bloques, cada uno con su explicación visible en el informe:

| Bloque | Peso | Qué pregunta |
|---|---|---|
| Liquidez | 18% | ¿Puedes entrar y salir de verdad? |
| Desarrollo | 20% | ¿Hay gente escribiendo código? |
| Comunidad | 12% | ¿Hay alguien ahí fuera? |
| Momento | 15% | ¿El mercado le presta atención ahora? |
| Valoración | 15% | ¿Está caro respecto a su propia historia? |
| Tokenomics | 20% | ¿Te van a diluir con desbloqueos futuros? |

Después se restan las **red flags**:

- Volumen > 1,5× la capitalización → posible wash trading (−15)
- Menos del 25% del supply circulando → dilución futura fuerte (−12)
- +150% en 30 días → riesgo alto de comprar el techo (−15)
- Cero commits en 4 semanas → posible abandono (−12)
- Capitalización < 40 M → fácil de manipular (−8)

Una nota de 8/10 significa **"dedícale una tarde a investigar esto"**. No significa
"compra". El sistema no ha leído el whitepaper, no conoce al equipo y no sabe si
el caso de uso tiene sentido. Eso te toca a ti.

---

## Problemas frecuentes

**"No se ha podido descargar el mercado"**
Sin conexión o CoinGecko caído. Prueba `python3 radar.py --demo` para confirmar
que el sistema funciona, y reintenta más tarde.

**"rate limit alcanzado, esperando 15s..."**
Normal. El sistema espera solo y continúa. Si pasa mucho, sube
`PAUSA_ENTRE_PETICIONES` en `config.py` de 2.5 a 4.

**Una moneda de mi watchlist no aparece**
No está en el top escaneado. Sube `TOP_A_ESCANEAR` a 500, o comprueba que el ID
es exactamente el de la URL de CoinGecko.

**Las tipografías se ven distintas**
El informe carga fuentes de Google Fonts. Sin internet usa las del sistema y se
ve algo distinto, pero funciona igual.

---

## Lo que este sistema NO hace

Merece la pena decirlo claro:

- **No predice precios.** Nadie puede, y quien diga lo contrario te está vendiendo algo.
- **No opera por ti.** No se conecta a ningún exchange ni toca tu dinero.
- **No sustituye leer.** Te dice dónde mirar; entender el proyecto sigue siendo tu trabajo.
- **No sabe de noticias.** Si algo cae un 20%, el sistema ve la caída pero no el porqué. Ese porqué lo buscas tú.

Lo que sí hace bien: ahorrarte una hora al día, avisarte cuando pasa algo raro,
llevarte la cuenta de la cartera, y obligarte a mirar lo que de verdad decide el
resultado —comisiones, dilución, liquidez, diversificación— en vez de solo el
precio.
