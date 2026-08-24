# Puesta en marcha: del cero al icono en el móvil

Guía completa. Unos 20 minutos la primera vez; después no vuelves a tocar nada.

Al terminar tendrás:

- Un informe que se genera **solo, cada mañana, en los servidores de GitHub**. Tu ordenador puede estar apagado.
- Una página web privada con un icono en la pantalla de inicio del móvil, que se abre como una app.
- La posibilidad de apuntar una compra desde el móvil en 20 segundos.

Coste: **0 €**. GitHub Actions da 2.000 minutos gratis al mes en repositorios privados y esto gasta unos 60.

---

## Paso 1 — Comprueba el ISIN de tu ETF (2 minutos)

`cartera.csv` usa **ISINs**, no símbolos de bolsa. El ISIN es un código de 12
caracteres que identifica al activo en todo el mundo y que tu bróker sí te
enseña. En Trade Republic: entra en el activo, baja hasta «Perfil» o
«Información», y ahí está.

Los tres que he puesto son:

| Activo | ISIN que he puesto |
|---|---|
| ETF S&P 500 EUR (Acc) | `IE00B5BMR087` ← **verifica este** |
| Constellation Energy | `US21037T1097` |
| PUIG Brands | `ES0105630315` |

Los dos últimos son seguros. El del ETF es mi mejor conjetura: hay varios S&P
500 en euros y los 131,37 € que pagaste no me cuadran con ninguno que conozca.

**Ábrelo en Trade Republic y compara.** Si el ISIN que ves ahí es otro,
cámbialo en `cartera.csv`. Es un copia y pega.

Después, comprueba que todo cuadra:

```bash
pip install -r requirements.txt
python3 radar.py --abrir
```

En la sección **Tu cartera** verás un desplegable que dice a qué activo se ha
traducido cada ISIN: confirma que los nombres son los que esperabas. Y mira que
el valor total se parezca a los 295 € que llevas invertidos.

> Red de seguridad: si el precio actual se aleja más de 4 veces del que pagaste,
> el informe te avisa de que el identificador puede estar mal. No te fíes solo de
> eso: una diferencia del 50% no salta y también sería un error.

---

## Paso 2 — Sube el proyecto a GitHub (5 minutos)

### Crea el repositorio

1. Entra en [github.com/new](https://github.com/new)
2. Nombre: `radar-de-mercados`
3. **Marca «Private»** — importante, tu cartera va dentro
4. No marques nada más (ni README, ni .gitignore, ni licencia)
5. **Create repository**

### Sube los ficheros

En tu ordenador, dentro de la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Radar de Mercados"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/radar-de-mercados.git
git push -u origin main
```

Sustituye `TU_USUARIO` por el tuyo. Si te pide contraseña, GitHub ya no acepta
la de la cuenta: necesitas un *token*. Se crea en
Settings → Developer settings → Personal access tokens → Tokens (classic) →
Generate new token, con el permiso `repo` marcado. Ese token es la contraseña.

---

## Paso 3 — Activa Pages y los permisos (3 minutos)

Dos ajustes en el repositorio. Los dos son necesarios; si falta uno, falla.

**Activar Pages:**

1. En tu repositorio → pestaña **Settings**
2. Menú izquierdo → **Pages**
3. En «Source», elige **GitHub Actions** (no «Deploy from a branch»)

**Dar permiso de escritura al workflow:**

1. Settings → **Actions** → **General**
2. Abajo del todo, «Workflow permissions»
3. Marca **Read and write permissions**
4. **Save**

> Este segundo paso es el que más gente se salta. Sin él, el informe se genera
> pero no puede guardar el histórico, y verás un error en rojo cada día.

---

## Paso 4 — Lánzalo por primera vez (3 minutos)

1. Pestaña **Actions**
2. Si te pide confirmar que quieres habilitar los workflows, acepta
3. En la izquierda, **Informe diario**
4. Botón **Run workflow** → **Run workflow**

Tarda entre 2 y 4 minutos. Cuando el círculo se ponga verde, tu página está en:

```
https://TU_USUARIO.github.io/radar-de-mercados/
```

Si sale un 404, espera un minuto más: la primera publicación tarda.

### Si sale en rojo

Pincha en la ejecución fallida y mira qué paso falló:

| Paso que falla | Qué pasa | Solución |
|---|---|---|
| Comprobar que los cálculos... | Un test no pasa | Cópiame el error |
| Generar el informe | Yahoo o CoinGecko no responden | Reintenta en un rato |
| Guardar el histórico | Faltan permisos | Repite el paso 3, segunda parte |
| Publicar en Pages | Pages sin activar | Repite el paso 3, primera parte |

---

## Paso 5 — Ponlo en la pantalla de inicio (1 minuto)

**iPhone (Safari, y tiene que ser Safari):**

1. Abre la URL
2. Botón compartir (el cuadrado con la flecha hacia arriba)
3. **Añadir a pantalla de inicio**
4. Nombre: Radar → **Añadir**

**Android (Chrome):**

1. Abre la URL
2. Menú de los tres puntos
3. **Añadir a pantalla de inicio** o **Instalar aplicación**

Ya tienes el icono. Al abrirlo se ve a pantalla completa, sin barra de
navegador, como una app cualquiera.

> Al ser un repositorio privado la página no sale en Google (lleva `noindex`),
> pero la URL en sí es pública para quien la conozca. Si prefieres que nadie
> más pueda verla, en Settings → Pages puedes restringir la visibilidad
> (requiere una cuenta de pago) o quitar `cartera.csv` del repositorio.

---

## El día a día

**Regla única: nunca borres ni corrijas líneas. Solo añade al final.**

El sistema hace las cuentas: suma unidades, calcula el precio medio ponderado y
resta lo vendido.

### Cómo se añade una línea (móvil, sin ordenador)

1. Abre tu repositorio en GitHub (app o navegador)
2. Toca `cartera.csv`
3. Toca el lápiz de editar
4. Añade la línea al final
5. **Commit changes**

En 2-3 minutos la página se ha regenerado. Refresca y ya está.

### Qué línea escribir exactamente

El formato siempre es el mismo, seis datos separados por comas:

```
nombre,isin,tipo,unidades,precio_por_unidad,EUR
```

**Has comprado.** Unidades en positivo:

```
Vanguard All-World,IE00BK5BQT80,etf,0.750000,134.20,EUR
```

**Has comprado más de algo que ya tienes.** No toques la línea vieja, añade otra:

```
S&P 500 EUR (Acc),IE00B5BMR087,etf,1.370175,131.37,EUR     <- la que ya estaba
S&P 500 EUR (Acc),IE00B5BMR087,etf,0.750000,134.20,EUR     <- la nueva
```

Ahora tienes 2,120175 participaciones a un precio medio de 132,37 €. Calculado solo.

**Has comprado cripto.** El ticker es el nombre en inglés y minúscula:

```
Bitcoin,bitcoin,cripto,0.001712,58400,EUR
Ethereum,ethereum,cripto,0.033784,2960,EUR
```

**Has vendido una parte.** Unidades en **negativo**, con el precio al que vendiste:

```
PUIG Brands,ES0105630315,accion,-1.60698,19.40,EUR
```

**Has vendido todo.** En negativo, todas las unidades que te quedaban. La posición
desaparece del informe:

```
PUIG Brands,ES0105630315,accion,-3.21396,19.40,EUR
```

### De dónde saco cada dato

| Dato | De dónde lo sacas |
|---|---|
| **nombre** | Lo eliges tú. Es lo que verás en el informe. |
| **isin** | Trade Republic → entra en el activo → «Perfil» o «Información» |
| **unidades** | Tu posición en el bróker, con todos los decimales |
| **precio por unidad** | Si no sale, divide lo que pagaste entre las unidades: 180 € ÷ 1,370175 = 131,37 |
| **tipo** | Lo pones tú: `etf`, `accion`, `cripto` o `renta_fija` |
| **EUR** | Siempre EUR con Trade Republic, aunque el activo cotice en dólares |

### Usa el ISIN, no el ticker

Es la única parte donde es fácil equivocarse.

El **ticker cambia según la bolsa**. PUIG Brands es `PUIG` en Madrid y `B1B` en
Alemania: el mismo papel con dos nombres. Trade Republic te enseña el código
alemán, que Yahoo Finance no conoce.

El **ISIN es el mismo en todo el mundo**. `ES0105630315` es PUIG en Madrid, en
Fráncfort y en cualquier bróker del planeta. Por eso el sistema usa ISINs: no
hay ambigüedad posible.

Si aun así pones un ticker que no funciona, el sistema lo busca solo y te dice
en el informe por cuál sustituirlo. Pero es un rodeo evitable.

> Si el nombre lleva comas, no pasa nada: van entre comillas.
> `"Berkshire Hathaway, Inc.",US0846707026,accion,1,400,EUR`

Los ejemplos también están comentados al final de tu `cartera.csv`: quítales la
almohadilla y adapta los números.

### Consultar días anteriores

En la página, `historico/` guarda los últimos 90 informes.

### Cambiar la hora del informe

En `.github/workflows/informe.yml`, la línea del `cron`. Está en **UTC**:

| Quieres verlo a las | Pon |
|---|---|
| 08:10 (invierno) | `10 7 * * *` |
| 09:10 (verano) | `10 7 * * *` |
| 07:00 todo el año en invierno | `0 6 * * *` |
| Solo de lunes a viernes | `10 7 * * 1-5` |

GitHub no entiende de cambios de hora, así que en verano el informe te llega una
hora más tarde. Si te molesta, ajusta el cron en marzo y en octubre.

> Las tareas programadas de GitHub pueden retrasarse entre 5 y 30 minutos cuando
> hay mucha carga. No es un fallo.

---

## Preguntas que te van a surgir

**¿Puede verlo alguien más?**
El repositorio es privado, así que el código y tu `cartera.csv` no. La página
publicada sí es accesible para quien tenga la URL exacta, aunque no aparece en
buscadores.

**¿Y si un día falla?**
La página se queda con el último informe correcto. No se rompe ni se queda en
blanco. Al día siguiente lo reintenta solo.

**¿Gasta mucho de la cuota gratuita?**
Unos 2 minutos por ejecución, 60 al mes. El límite gratuito en repositorios
privados es de 2.000.

**¿Puedo seguir usándolo en el ordenador?**
Sí, `python3 radar.py --abrir` sigue funcionando igual.

**¿Y si quiero dejar de recibirlo?**
Actions → Informe diario → menú «...» → Disable workflow.

---

## Recordatorio

Esto no es asesoramiento financiero. El sistema aplica fórmulas públicas a datos
públicos: no predice nada, no sabe qué comprar y no conoce tu situación. Lo que
hace es ahorrarte tiempo y ponerte delante las métricas que importan.
