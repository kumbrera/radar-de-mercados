"""
Glosario y FAQs.

Cada término que aparece en el informe puede llevar un "?" al lado. Al pulsarlo
se despliega la explicación que hay aquí. La idea es que después de leer el
informe 20 veces ya no necesites el glosario.
"""

from __future__ import annotations

GLOSARIO: dict[str, dict[str, str]] = {
    # -- Indicadores técnicos ------------------------------------------------
    "rsi": {
        "titulo": "RSI (Índice de Fuerza Relativa)",
        "corto": "De 0 a 100. Mide si algo ha subido o bajado demasiado rápido.",
        "largo": (
            "El RSI compara la fuerza media de las subidas contra la de las bajadas "
            "de los últimos 14 días.\n\n"
            "• Por debajo de 30: ha caído mucho y rápido. Se llama 'sobrevendido'.\n"
            "• Entre 30 y 70: zona normal, ni frío ni calor.\n"
            "• Por encima de 70: ha subido mucho y rápido. 'Sobrecomprado'.\n\n"
            "TRAMPA CLÁSICA: un RSI de 80 no significa 'vende ya'. En una tendencia "
            "alcista fuerte el RSI puede pasarse semanas por encima de 70 mientras el "
            "precio sigue subiendo. Y un RSI de 20 puede seguir cayendo. El RSI te dice "
            "que el movimiento ha sido rápido, no que se vaya a dar la vuelta."
        ),
    },
    "sma": {
        "titulo": "SMA (Media móvil simple)",
        "corto": "El precio medio de los últimos N días.",
        "largo": (
            "La SMA 50 es el precio medio de los últimos 50 días. La SMA 200, de los "
            "últimos 200.\n\n"
            "Sirve para dos cosas:\n"
            "1. Suavizar el ruido. El precio del día a día salta mucho; la media te "
            "enseña la dirección de fondo.\n"
            "2. Como referencia. Si el precio está por encima de su media de 200 días, "
            "la tendencia de largo plazo es alcista. Por debajo, bajista.\n\n"
            "No es una bola de cristal: la media va SIEMPRE por detrás del precio, "
            "porque se calcula con datos del pasado."
        ),
    },
    "cruce_medias": {
        "titulo": "Cruce de medias (cruz dorada / cruz de la muerte)",
        "corto": "Cuando la media corta cruza a la media larga.",
        "largo": (
            "Cuando la media de 20 días cruza POR ENCIMA de la de 50, se llama cruce "
            "alcista o 'cruz dorada': el precio reciente está tirando hacia arriba más "
            "fuerte que el de medio plazo.\n\n"
            "Cuando cruza POR DEBAJO, 'cruz de la muerte'.\n\n"
            "Es de los indicadores más famosos y también de los más sobrevalorados: "
            "genera muchísimas señales falsas en mercados laterales. Úsalo como contexto, "
            "nunca como único motivo para hacer algo."
        ),
    },
    "macd": {
        "titulo": "MACD",
        "corto": "Mide si el impulso del precio está acelerando o frenando.",
        "largo": (
            "El MACD resta dos medias exponenciales (12 y 26 días) y compara el "
            "resultado con su propia media de 9 días, la 'línea de señal'.\n\n"
            "• MACD cruza por encima de la señal: el impulso está mejorando.\n"
            "• MACD cruza por debajo: el impulso se está apagando.\n\n"
            "El histograma es la distancia entre ambas líneas: cuanto más grande, más "
            "fuerte el impulso en esa dirección."
        ),
    },
    "volatilidad": {
        "titulo": "Volatilidad anualizada",
        "corto": "Cuánto se mueve normalmente este activo.",
        "largo": (
            "Se calcula midiendo cuánto varía el precio cada día y escalándolo a un año.\n\n"
            "• Menos del 40%: tranquilo, para lo que es cripto.\n"
            "• 40-80%: normal en cripto.\n"
            "• Más del 100%: caídas del 20% en un solo día entran dentro de lo esperado.\n\n"
            "Para comparar: el S&P 500 suele estar entre el 12% y el 20%. Bitcoin, entre "
            "el 40% y el 70%. Una altcoin pequeña puede pasar del 150%.\n\n"
            "Esto es lo que de verdad determina cuánto dinero puedes meter sin dormir mal."
        ),
    },
    "drawdown": {
        "titulo": "Drawdown (caída desde máximos)",
        "corto": "Cuánto ha caído desde su punto más alto.",
        "largo": (
            "Si algo valía 100 y ahora vale 40, el drawdown es del -60%.\n\n"
            "Es útil por dos motivos opuestos:\n"
            "• Un drawdown grande puede significar 'está de rebajas'.\n"
            "• O puede significar 'el mercado ha decidido que esto no vale nada'.\n\n"
            "El dato por sí solo no distingue entre las dos cosas. Por eso el sistema "
            "lo cruza con desarrollo, liquidez y comunidad: un proyecto con -80% y "
            "desarrolladores activos es una historia; con -80% y GitHub muerto es otra.\n\n"
            "Y la matemática dolorosa: recuperarse de un -50% exige un +100%. De un "
            "-80%, un +400%."
        ),
    },
    "soporte_resistencia": {
        "titulo": "Soporte y resistencia",
        "corto": "El suelo y el techo del precio en los últimos meses.",
        "largo": (
            "Aquí se calculan de la forma más honesta posible: el mínimo y el máximo "
            "de los últimos 90 días. Ni más ni menos.\n\n"
            "La idea es que en esos niveles suele haber gente esperando (compradores "
            "abajo, vendedores arriba), así que el precio tiende a frenar ahí. Funciona "
            "hasta que deja de funcionar.\n\n"
            "El dato de 'posición en el rango' te dice dónde estás: 0% es pegado al "
            "suelo del rango, 100% pegado al techo."
        ),
    },
    "volumen_relativo": {
        "titulo": "Volumen relativo",
        "corto": "El volumen de hoy comparado con el mes normal.",
        "largo": (
            "Si vale 3.0, hoy se ha movido el triple de dinero que un día normal del "
            "último mes.\n\n"
            "Esto importa mucho más de lo que parece: un movimiento de precio SIN "
            "volumen suele ser ruido y revertirse. Un movimiento CON mucho volumen "
            "significa que hay convicción detrás, sea en la dirección que sea.\n\n"
            "Volumen anormalmente alto = ha pasado algo. Merece la pena buscar qué."
        ),
    },

    # -- Datos de mercado ----------------------------------------------------
    "market_cap": {
        "titulo": "Capitalización de mercado (market cap)",
        "corto": "Precio × monedas en circulación. El 'tamaño' del proyecto.",
        "largo": (
            "Es la métrica correcta para comparar proyectos, no el precio.\n\n"
            "Una moneda que vale 0,01 € no es 'barata' y una que vale 3.000 € no es "
            "'cara'. Lo que importa es cuánto vale el proyecto ENTERO.\n\n"
            "Ejemplo: si algo capitaliza 100 M y quieres que haga x10, tiene que llegar "
            "a 1.000 M. ¿Es realista para lo que hace? Esa es la pregunta útil.\n\n"
            "Ojo con el market cap 'diluido' (FDV): usa el total de monedas que existirán "
            "algún día, no las que circulan hoy. Si la diferencia es enorme, te van a "
            "diluir."
        ),
    },
    "volumen_24h": {
        "titulo": "Volumen 24h",
        "corto": "Cuánto dinero se ha intercambiado en un día.",
        "largo": (
            "Es la medida de liquidez: si hay poco volumen y quieres vender una posición "
            "grande, tú mismo hundes el precio al hacerlo.\n\n"
            "Regla práctica: no metas más dinero del que puedas sacar sin ser el 1% del "
            "volumen diario."
        ),
    },
    "ratio_volumen_mcap": {
        "titulo": "Ratio volumen / capitalización",
        "corto": "Qué porcentaje del proyecto cambia de manos cada día.",
        "largo": (
            "Volumen diario dividido entre capitalización.\n\n"
            "• Por debajo del 1%: muy poca actividad, cuesta entrar y salir.\n"
            "• Entre 2% y 20%: sano, hay mercado de verdad.\n"
            "• Por encima del 100%: sospechoso. Que el proyecto entero cambie de manos "
            "cada día no es normal. A menudo es wash trading (volumen inflado "
            "artificialmente por el propio exchange o el equipo) o una moneda en pleno "
            "frenesí especulativo."
        ),
    },
    "supply_circulante": {
        "titulo": "Supply circulante vs total",
        "corto": "Cuántas monedas existen ya frente a cuántas existirán.",
        "largo": (
            "Este es EL dato que más gente ignora y más dinero cuesta.\n\n"
            "Si solo circula el 15% de las monedas, el 85% restante está en manos del "
            "equipo, los inversores privados y la fundación, y se irá desbloqueando "
            "durante los próximos años.\n\n"
            "Cada desbloqueo es oferta nueva entrando al mercado. Para que el precio no "
            "baje, tiene que entrar demanda nueva al mismo ritmo. Muchas veces no entra.\n\n"
            "Por eso el sistema penaliza fuerte los proyectos con poco circulante: no "
            "porque sean estafas, sino porque compras sabiendo que te van a diluir."
        ),
    },
    "ath": {
        "titulo": "ATH (All-Time High)",
        "corto": "El precio más alto de su historia.",
        "largo": (
            "Sirve de referencia para saber cuánto ha caído algo. Pero cuidado con el "
            "razonamiento 'si volviera a su ATH ganaría x5': el ATH se marcó en unas "
            "condiciones de mercado concretas que puede que no vuelvan, y muchas monedas "
            "del ciclo anterior nunca recuperaron su máximo."
        ),
    },
    "dominancia_btc": {
        "titulo": "Dominancia de Bitcoin",
        "corto": "Qué porcentaje de todo el mercado cripto es Bitcoin.",
        "largo": (
            "Cuando la dominancia SUBE, el dinero se está refugiando en Bitcoin y las "
            "altcoins suelen sufrir.\n\n"
            "Cuando BAJA con el mercado subiendo, es la señal clásica de que el dinero "
            "está rotando hacia altcoins (lo que la gente llama 'altseason').\n\n"
            "Cuando baja con el mercado cayendo, simplemente todo se está desplomando y "
            "las altcoins caen más rápido."
        ),
    },
    "fear_greed": {
        "titulo": "Índice de Miedo y Codicia",
        "corto": "De 0 (pánico) a 100 (euforia). Mide el sentimiento del mercado.",
        "largo": (
            "Combina volatilidad, volumen, redes sociales, dominancia y tendencias de "
            "búsqueda en un solo número.\n\n"
            "• 0-25 (Miedo extremo): la gente está vendiendo por pánico.\n"
            "• 25-45 (Miedo)\n"
            "• 45-55 (Neutral)\n"
            "• 55-75 (Codicia)\n"
            "• 75-100 (Codicia extrema): euforia, todo el mundo está seguro de que sube.\n\n"
            "La lectura contraria es la famosa: históricamente los mejores momentos de "
            "compra han coincidido con miedo extremo, y los peores con codicia extrema. "
            "Históricamente. Lo cual no es lo mismo que siempre."
        ),
    },

    # -- Scoring -------------------------------------------------------------
    "score": {
        "titulo": "Puntuación del proyecto (0-10)",
        "corto": "Una nota calculada con datos objetivos, no una recomendación.",
        "largo": (
            "El sistema puntúa seis bloques y los suma con pesos:\n\n"
            "• Liquidez (18%): ¿puedes entrar y salir de verdad?\n"
            "• Desarrollo (20%): ¿hay gente escribiendo código?\n"
            "• Comunidad (12%): ¿hay alguien ahí fuera?\n"
            "• Momento (15%): ¿el mercado le presta atención ahora?\n"
            "• Valoración (15%): ¿está caro respecto a su propia historia?\n"
            "• Tokenomics (20%): ¿te van a diluir?\n\n"
            "Después restan las red flags.\n\n"
            "IMPORTANTE: una nota alta significa 'este proyecto merece que dediques una "
            "tarde a investigarlo'. No significa 'compra'. El sistema no ha leído el "
            "whitepaper, no conoce al equipo y no sabe si el caso de uso tiene sentido. "
            "Eso lo tienes que hacer tú."
        ),
    },
    "desarrollo": {
        "titulo": "Actividad de desarrollo",
        "corto": "Commits, estrellas y contribuidores en GitHub.",
        "largo": (
            "Un proyecto cripto es, al final, software. Si nadie escribe código, no hay "
            "proyecto: hay un token con una web bonita.\n\n"
            "El sistema mira commits recientes, número de contribuidores, estrellas y "
            "issues cerrados frente a abiertos.\n\n"
            "Límite honesto: no todos los proyectos publican su código en GitHub, y "
            "algunos tienen el repositorio mal enlazado en CoinGecko. Un 0 aquí puede "
            "significar 'abandonado' o simplemente 'no hay datos'. El informe distingue "
            "entre ambos casos."
        ),
    },
    "tokenomics": {
        "titulo": "Tokenomics",
        "corto": "Cómo se reparten y se emiten las monedas.",
        "largo": (
            "Las reglas del juego económico del token: cuántas hay, cuántas habrá, quién "
            "las tiene y cuándo se desbloquean.\n\n"
            "Un proyecto tecnológicamente brillante con una tokenomics mala es una mala "
            "inversión, porque la dilución se come tu rentabilidad aunque el proyecto "
            "triunfe.\n\n"
            "Lo que más pesa: el porcentaje que ya circula. Cuanto más alto, menos sorpresas."
        ),
    },
    "red_flag": {
        "titulo": "Red flags",
        "corto": "Señales de alarma que restan puntos automáticamente.",
        "largo": (
            "El sistema detecta cuatro:\n\n"
            "1. Volumen sospechoso: el volumen supera 1,5 veces la capitalización. "
            "Posible wash trading.\n"
            "2. Poco circulante: menos del 25% del supply en circulación. Dilución futura "
            "asegurada.\n"
            "3. Pump peligroso: +150% en 30 días. Comprar después de eso suele ser comprar "
            "el techo.\n"
            "4. Desarrollo parado: sin commits en 60 días.\n\n"
            "Una red flag no significa estafa. Significa 'antes de meter dinero aquí, "
            "entiende por qué pasa esto'."
        ),
    },

    # -- Conceptos generales -------------------------------------------------
    "dca": {
        "titulo": "DCA (Dollar Cost Averaging)",
        "corto": "Comprar una cantidad fija cada X tiempo, pase lo que pase.",
        "largo": (
            "En vez de meter 400 € de golpe, metes 50 € cada mes durante ocho meses.\n\n"
            "Ventajas: eliminas el problema de acertar el momento, compras más unidades "
            "cuando está barato y menos cuando está caro, y sobre todo eliminas el estrés "
            "de '¿y si compro justo antes de una caída?'.\n\n"
            "Desventaja: si el mercado sube en línea recta, habrías ganado más metiéndolo "
            "todo el primer día.\n\n"
            "Para alguien que empieza, el DCA gana casi siempre por la parte psicológica: "
            "el mayor riesgo cuando empiezas no es elegir mal el activo, es entrar en "
            "pánico y vender abajo."
        ),
    },
    "stablecoin": {
        "titulo": "Stablecoin",
        "corto": "Cripto diseñada para valer siempre 1 dólar o 1 euro.",
        "largo": (
            "USDT, USDC, DAI. Sirven para tener el dinero 'dentro' del mundo cripto sin "
            "exposición a la volatilidad.\n\n"
            "No son mágicas: dependen de que quien las emite tenga de verdad las reservas "
            "que dice. Ha habido stablecoins que se han ido a cero (Terra/UST, 2022, unos "
            "40.000 millones evaporados en una semana)."
        ),
    },
    "layer2": {
        "titulo": "Layer 2 (L2)",
        "corto": "Una red construida encima de otra para hacerla más rápida y barata.",
        "largo": (
            "Ethereum es seguro pero lento y caro. Las L2 (Arbitrum, Optimism, Base) "
            "procesan las transacciones aparte y luego las 'resumen' en Ethereum.\n\n"
            "Resultado: comisiones de céntimos en vez de euros, heredando la seguridad de "
            "Ethereum."
        ),
    },
    "staking": {
        "titulo": "Staking",
        "corto": "Bloquear tus monedas para ayudar a la red y cobrar por ello.",
        "largo": (
            "En redes de prueba de participación, bloqueas tus monedas como garantía y "
            "cobras un porcentaje anual (típicamente 3-8%).\n\n"
            "Riesgos reales: el dinero queda bloqueado un tiempo (no puedes vender si cae), "
            "y si delegas en un validador que se porta mal puedes perder parte del "
            "depósito.\n\n"
            "Y lo más importante: si cobras un 5% anual en una moneda que cae un 40%, has "
            "perdido dinero. El interés se paga en la propia moneda."
        ),
    },
    "custodia": {
        "titulo": "Custodia: quién tiene de verdad tus criptos",
        "corto": "Si no tienes las claves, no son tuyas.",
        "largo": (
            "Cuando compras cripto en un bróker o exchange, normalmente el que las guarda "
            "es ellos. Tú tienes una anotación en su base de datos.\n\n"
            "Funciona bien... hasta que el sitio quiebra (FTX, 2022) o te bloquea la "
            "cuenta.\n\n"
            "Una hardware wallet (Ledger, Trezor, Tangem) guarda las claves en un aparato "
            "físico que nunca las expone a internet. La contrapartida es que la "
            "responsabilidad pasa a ser 100% tuya: si pierdes las 24 palabras de "
            "recuperación, no hay servicio de atención al cliente que te salve.\n\n"
            "Regla práctica: cantidades pequeñas y operativa, en el bróker. Cantidades que "
            "te dolerían de verdad, en hardware wallet."
        ),
    },
    # -- Bolsa: ETFs y fondos ------------------------------------------------
    "ter": {
        "titulo": "TER (comisión anual del fondo)",
        "corto": "Lo que te cobra el fondo cada año. El dato más importante de todos.",
        "largo": (
            "Total Expense Ratio: el porcentaje anual que el fondo se queda por "
            "gestionarte el dinero. Se descuenta del valor del fondo día a día, así que "
            "no lo ves salir de tu cuenta, pero lo pagas igual.\n\n"
            "Por qué es el dato más importante: es lo ÚNICO garantizado. La rentabilidad "
            "futura no la conoce nadie; la comisión la sabes con certeza desde el primer "
            "día.\n\n"
            "La aritmética: 10.000 € al 7% anual durante 30 años son 76.123 € sin "
            "comisiones. Con un TER del 0,20% quedan 71.968 €. Con un TER del 1,20% "
            "quedan 54.271 €. Ese punto porcentual de más te ha costado 17.696 €, casi "
            "el doble de lo que invertiste.\n\n"
            "Referencia: un indexado amplio decente está entre el 0,05% y el 0,25%. Por "
            "encima del 0,50% en un producto indexado, busca alternativas."
        ),
    },
    "acumulacion": {
        "titulo": "Acumulación (Acc) vs Distribución (Dist)",
        "corto": "Si el fondo reinvierte los dividendos o te los paga.",
        "largo": (
            "Un ETF de **acumulación** (verás 'Acc' o 'C' en el nombre) coge los "
            "dividendos que pagan las empresas y los reinvierte automáticamente dentro "
            "del fondo. No ves nada llegar a tu cuenta; el valor de tu participación "
            "sube.\n\n"
            "Uno de **distribución** ('Dist' o 'D') te ingresa esos dividendos en "
            "efectivo cada trimestre o semestre.\n\n"
            "Cuál conviene en España: normalmente el de acumulación, y por un motivo "
            "fiscal concreto. Cada dividendo que cobras tributa en el IRPF ese mismo año, "
            "aunque lo reinviertas a mano. En el de acumulación no hay reparto, así que "
            "no hay nada que declarar hasta que vendas. Difieres el impuesto años o "
            "décadas, y mientras tanto ese dinero sigue componiendo.\n\n"
            "El de distribución tiene sentido si quieres una renta periódica de verdad "
            "para gastarla."
        ),
    },
    "cobertura_divisa": {
        "titulo": "Cobertura de divisa (hedged)",
        "corto": "Elimina el efecto del tipo de cambio, a cambio de un coste.",
        "largo": (
            "Si compras un ETF del S&P 500 sin cobertura, tu resultado depende de dos "
            "cosas: cómo va el índice Y cómo se mueve el euro frente al dólar. El índice "
            "puede subir un 7% y tú ganar un 4% porque el dólar se ha debilitado.\n\n"
            "Un ETF cubierto ('EUR Hedged') neutraliza esa segunda parte con contratos de "
            "cambio. Ganas o pierdes solo con el mercado.\n\n"
            "Lo que cuesta: más comisión (típicamente 0,10-0,15% adicional) más el coste "
            "implícito de la cobertura, que depende de la diferencia de tipos de interés "
            "entre las dos zonas y puede ser bastante mayor que el TER.\n\n"
            "Qué suele recomendarse: para renta variable a largo plazo, sin cobertura. "
            "Las divisas oscilan pero no tienen tendencia a largo plazo, así que pagas "
            "todos los años por eliminar un riesgo que se diluye solo con el tiempo. "
            "Para renta fija, o para plazos cortos, la cobertura sí suele compensar.\n\n"
            "El matiz honesto: sin cobertura la cartera se mueve más, y si eso te lleva a "
            "vender en el peor momento, la cobertura te habrá salido barata."
        ),
    },
    "indexado": {
        "titulo": "Gestión indexada vs gestión activa",
        "corto": "Copiar el índice frente a intentar batirlo.",
        "largo": (
            "Un fondo indexado compra simplemente todas las empresas del índice, en la "
            "misma proporción. No hay gestor decidiendo nada, así que cuesta muy poco.\n\n"
            "Un fondo de gestión activa tiene un equipo eligiendo qué comprar para "
            "intentar batir al índice. Cobra bastante más por ello.\n\n"
            "El dato incómodo para la gestión activa: los informes SPIVA de S&P llevan "
            "dos décadas midiéndolo, y a 10-15 años vista en torno al 85-95% de los "
            "fondos activos rinden por debajo de su índice de referencia, una vez "
            "descontadas comisiones.\n\n"
            "No es que los gestores sean malos: es que tienen que batir al mercado por un "
            "margen suficiente para cubrir su propia comisión, todos los años, y eso es "
            "muy difícil de sostener."
        ),
    },
    "replica": {
        "titulo": "Réplica física vs sintética",
        "corto": "Si el fondo compra las acciones de verdad o usa derivados.",
        "largo": (
            "**Física**: el fondo compra realmente las acciones del índice. Es lo más "
            "sencillo de entender y no añade riesgos raros.\n\n"
            "**Sintética**: el fondo no compra las acciones; firma un contrato (swap) con "
            "un banco que se compromete a pagarle la rentabilidad del índice.\n\n"
            "La sintética puede seguir el índice con más precisión y a veces tiene ventajas "
            "fiscales en índices de EE. UU., pero añade riesgo de contrapartida: dependes "
            "de que el banco cumpla. Está regulado y limitado, pero existe.\n\n"
            "Para empezar, la réplica física es la opción tranquila."
        ),
    },
    "ucits": {
        "titulo": "UCITS",
        "corto": "Sello europeo de fondo regulado. Búscalo siempre.",
        "largo": (
            "Es la normativa europea que regula los fondos de inversión minoristas. Un "
            "ETF con UCITS en el nombre cumple reglas estrictas de diversificación, "
            "liquidez, custodia separada del patrimonio y transparencia.\n\n"
            "En la práctica, desde España solo puedes comprar ETFs UCITS: los ETFs "
            "estadounidenses (como el SPY o el VOO originales) no están disponibles "
            "porque no cumplen los requisitos de documentación europea. Por eso compras "
            "las versiones UCITS equivalentes, que replican los mismos índices."
        ),
    },

    # -- Bolsa: acciones -----------------------------------------------------
    "per": {
        "titulo": "PER (precio / beneficio)",
        "corto": "Cuántos años de beneficio actual estás pagando por la acción.",
        "largo": (
            "Si una empresa gana 2 € por acción y la acción cuesta 30 €, su PER es 15: "
            "pagas 15 años de beneficios actuales.\n\n"
            "Referencias: la media histórica del mercado ronda el 15-20. Empresas que "
            "crecen rápido cotizan a 30-50 o más. Empresas maduras o en problemas, por "
            "debajo de 10.\n\n"
            "Los dos errores clásicos:\n"
            "• Creer que PER alto = caro. Puede estar plenamente justificado si los "
            "beneficios van a multiplicarse. Lo que dice un PER alto es que el mercado ya "
            "descuenta ese crecimiento, y que si no llega, la caída es fuerte.\n"
            "• Creer que PER bajo = barato. Muchas veces está bajo porque el mercado "
            "espera que los beneficios caigan. Es la 'trampa de valor'.\n\n"
            "Solo tiene sentido comparar el PER entre empresas del mismo sector."
        ),
    },
    "dividendo": {
        "titulo": "Rentabilidad por dividendo",
        "corto": "Qué porcentaje del precio te devuelve la empresa cada año.",
        "largo": (
            "Si una acción cuesta 100 € y reparte 4 € al año, su rentabilidad por "
            "dividendo es del 4%.\n\n"
            "Lo que casi nadie te cuenta: el día que se paga el dividendo, la acción baja "
            "aproximadamente esa misma cantidad. No es dinero que aparece de la nada: es "
            "dinero que sale de la empresa y por tanto de su valor. Cobrar un dividendo "
            "del 4% no te hace un 4% más rico.\n\n"
            "Y en España tributa en el IRPF el año que lo cobras, desde el primer euro.\n\n"
            "Cuidado con los dividendos muy altos (más del 7-8%): a menudo el porcentaje "
            "es alto porque el precio se ha desplomado, no porque paguen más. Y un "
            "dividendo que la empresa no puede permitirse acaba recortándose."
        ),
    },
    "beta": {
        "titulo": "Beta",
        "corto": "Cuánto se mueve una acción respecto al mercado.",
        "largo": (
            "Beta 1 significa que se mueve igual que el índice. Beta 1,5, que amplifica "
            "los movimientos un 50% en ambas direcciones. Beta 0,6, que es más tranquila "
            "que el mercado.\n\n"
            "Una beta alta no es mala ni buena: es más riesgo y más recorrido. Lo que no "
            "puedes es tener una cartera llena de betas altas y esperar dormir tranquilo "
            "cuando el mercado corrija."
        ),
    },
    "vix": {
        "titulo": "VIX (índice del miedo)",
        "corto": "Cuánta turbulencia espera el mercado en las próximas semanas.",
        "largo": (
            "Mide la volatilidad que los inversores están pagando por protegerse en "
            "opciones sobre el S&P 500. Es el equivalente bursátil del índice de miedo y "
            "codicia de las criptos.\n\n"
            "• Por debajo de 15: calma, quizá demasiada complacencia.\n"
            "• Entre 15 y 20: normal.\n"
            "• Entre 20 y 30: nerviosismo.\n"
            "• Por encima de 30: miedo de verdad. Se alcanzó por encima de 80 en marzo "
            "de 2020 y en la crisis de 2008.\n\n"
            "El VIX y la bolsa se mueven casi siempre en direcciones opuestas. "
            "Históricamente, los picos altos de VIX han coincidido con suelos de mercado, "
            "no con techos: cuando todo el mundo está aterrorizado, lo peor suele estar "
            "ya en el precio."
        ),
    },
    "correccion": {
        "titulo": "Corrección y mercado bajista",
        "corto": "-10% es corrección. -20% es mercado bajista.",
        "largo": (
            "Son definiciones convencionales pero universalmente usadas:\n\n"
            "• **Corrección**: caída del 10% o más desde el máximo. Ocurre de media una "
            "vez al año. Es rutina.\n"
            "• **Mercado bajista**: caída del 20% o más. Ocurre cada 4-6 años de media.\n\n"
            "Datos históricos del S&P 500: ha habido más de 25 mercados bajistas desde "
            "1928. Han durado de media entre 9 y 18 meses. Y todos, sin excepción, han "
            "acabado en un máximo nuevo.\n\n"
            "Eso no garantiza absolutamente nada sobre el próximo. Pero sí explica por "
            "qué el consejo estándar es no vender en mitad de uno: quien vendió en marzo "
            "de 2009 o en marzo de 2020 convirtió una caída temporal en una pérdida "
            "definitiva."
        ),
    },

    # -- Cartera -------------------------------------------------------------
    "rebalanceo": {
        "titulo": "Rebalanceo",
        "corto": "Devolver la cartera a los porcentajes que habías decidido.",
        "largo": (
            "Con el tiempo, lo que sube pesa cada vez más. Si empezaste con 70% ETFs y "
            "15% cripto y la cripto se dispara, puedes acabar con un 40% en cripto sin "
            "haber comprado nada: el riesgo de tu cartera ha cambiado sin que lo decidas "
            "tú.\n\n"
            "Hay dos formas de corregirlo:\n\n"
            "1. **Vendiendo lo que sobra** y comprando lo que falta. Directo, pero en "
            "España cada venta con ganancia tributa, y pagas comisiones dos veces.\n\n"
            "2. **Aportando a lo que falta.** Diriges la aportación mensual hacia lo que "
            "se ha quedado corto. No vendes nada, no tributas, no pagas comisiones de "
            "venta. Es lo que hace este sistema por defecto, y para carteras pequeñas es "
            "claramente superior.\n\n"
            "Cada cuánto: una o dos veces al año es suficiente. Rebalancear cada mes "
            "genera costes que se comen el beneficio del propio rebalanceo."
        ),
    },
    "diversificacion": {
        "titulo": "Diversificación",
        "corto": "No depender de que una sola cosa salga bien.",
        "largo": (
            "La idea no es maximizar la rentabilidad: es que ningún error individual "
            "pueda hundirte.\n\n"
            "Diversificar de verdad significa repartir entre cosas que NO se mueven "
            "juntas. Tener diez acciones tecnológicas americanas no es diversificar: "
            "cuando cae el sector, caen las diez a la vez.\n\n"
            "Un detalle poco intuitivo: un ETF del S&P 500 parece muy diversificado (500 "
            "empresas), pero las 7 mayores pesan más del 30% del índice, y casi todas son "
            "tecnológicas. Estás más concentrado de lo que parece.\n\n"
            "Regla práctica razonable: que ninguna posición individual supere el 20-25% "
            "de la cartera, salvo que sea un fondo global amplio."
        ),
    },
    "coste_hundido": {
        "titulo": "El precio al que compraste no importa",
        "corto": "El mercado no sabe cuánto pagaste tú.",
        "largo": (
            "Es probablemente el sesgo que más dinero cuesta a los inversores "
            "particulares.\n\n"
            "Si compraste algo a 100 y ahora vale 60, es tentador pensar «no vendo hasta "
            "recuperar». Pero al mercado le da exactamente igual lo que pagaste tú: el "
            "activo vale 60 y subirá o bajará por sus propios motivos.\n\n"
            "La pregunta correcta no es «¿cuánto llevo perdido?». Es: **«si hoy tuviera "
            "60 € en efectivo, ¿compraría esto?»**. Si la respuesta es no, mantenerlo "
            "solo porque lo compraste caro es dejar el dinero en tu peor idea.\n\n"
            "El reverso también aplica: no vendas algo que va bien solo porque «ya ha "
            "subido mucho»."
        ),
    },
    "impuestos_es": {
        "titulo": "Impuestos en España",
        "corto": "Solo tributas cuando vendes, y por la ganancia.",
        "largo": (
            "Las ganancias patrimoniales van a la base del ahorro del IRPF. Los tramos "
            "empiezan en el 19% y suben por escalones según el importe de la ganancia.\n\n"
            "Lo que SÍ genera impuesto:\n"
            "• Vender con ganancia (acciones, ETFs, cripto).\n"
            "• Cambiar una cripto por otra. Cambiar BTC por ETH tributa aunque no hayas "
            "visto un euro: fiscalmente es una venta y una compra.\n"
            "• Cobrar dividendos, desde el primer euro.\n\n"
            "Lo que NO genera impuesto:\n"
            "• Comprar y mantener, suba lo que suba.\n"
            "• Que un ETF de acumulación reinvierta dividendos dentro del fondo.\n\n"
            "Regla FIFO: si compraste el mismo valor en varias fechas, Hacienda considera "
            "que vendes primero las participaciones más antiguas.\n\n"
            "Traspasos: los fondos de inversión españoles se pueden traspasar entre sí "
            "sin tributar. Los ETFs no disfrutan de esa ventaja. Es un punto real a favor "
            "de los fondos indexados frente a los ETFs si prevés cambiar de producto.\n\n"
            "Esto es información general, no asesoramiento fiscal. Si el volumen crece, "
            "habla con un gestor."
        ),
    },
    "horizonte": {
        "titulo": "Horizonte temporal",
        "corto": "Cuándo vas a necesitar el dinero. Lo determina casi todo.",
        "largo": (
            "Es la variable que más debería condicionar tus decisiones, y la que menos se "
            "menciona.\n\n"
            "Datos del S&P 500 desde 1928: en cualquier ventana de 1 año, has perdido "
            "dinero en torno al 26% de las veces. En ventanas de 10 años, alrededor del "
            "6%. En ventanas de 20 años, ninguna ha terminado en pérdidas.\n\n"
            "Traducción práctica: el dinero que puedas necesitar en menos de 3-5 años no "
            "debería estar en renta variable, por muy buena que parezca la oportunidad. Y "
            "el dinero que no vas a tocar en 20 años no debería estar en efectivo, por "
            "mucho miedo que dé el mercado."
        ),
    },

    "no_es_consejo": {
        "titulo": "Por qué esto no son consejos de inversión",
        "corto": "El sistema procesa datos. Las decisiones son tuyas.",
        "largo": (
            "Todo lo que ves aquí sale de aplicar fórmulas públicas a datos públicos. "
            "El sistema no sabe nada que no sepa el mercado, no predice el futuro y no "
            "tiene ni idea de tu situación personal.\n\n"
            "Lo que SÍ hace bien: ahorrarte dos horas al día de mirar gráficos, avisarte "
            "cuando pasa algo estadísticamente inusual, y obligarte a mirar métricas que "
            "importan (liquidez, dilución, desarrollo) en vez de solo el precio.\n\n"
            "Lo que NO hace: decirte qué comprar. Ninguna herramienta puede, y la que "
            "diga que sí te está vendiendo algo."
        ),
    },
}


FAQS_GENERALES: list[dict[str, str]] = [
    {
        "pregunta": "¿Cómo leo este informe sin volverme loco?",
        "respuesta": (
            "En este orden: primero el semáforo de arriba (¿cómo está el mercado en "
            "general?), después tus criptos (¿ha pasado algo raro con lo que ya tengo?), "
            "y solo al final los proyectos nuevos.\n\n"
            "Si tienes cinco minutos, lee solo las alertas. Si no hay alertas, no ha "
            "pasado nada importante y ese es el mensaje."
        ),
    },
    {
        "pregunta": "¿Debo hacer algo cada día que salga una señal?",
        "respuesta": (
            "No. Esa es probablemente la lección más cara del mundo de la inversión.\n\n"
            "La mayoría de días la respuesta correcta es no hacer nada. Las señales son "
            "para que mires, no para que operes. Operar mucho tiene tres costes: "
            "comisiones, impuestos por cada venta con ganancia, y sobre todo la "
            "probabilidad altísima de vender justo antes de una subida.\n\n"
            "Si acabas operando más de una o dos veces al mes por culpa de este sistema, "
            "el sistema te está perjudicando."
        ),
    },
    {
        "pregunta": "El sistema dice que algo está 'sobrevendido'. ¿Compro?",
        "respuesta": (
            "Significa que ha caído rápido. Nada más.\n\n"
            "Las cosas caen rápido por dos motivos muy distintos: pánico exagerado "
            "(oportunidad) o porque ha pasado algo malo de verdad (trampa). El indicador "
            "no distingue entre los dos.\n\n"
            "Lo que tienes que hacer al ver un 'sobrevendido' es buscar la noticia. Si no "
            "hay noticia, es ruido. Si la hay, léela antes de decidir nada."
        ),
    },
    {
        "pregunta": "¿Por qué el sistema no me dice directamente qué comprar?",
        "respuesta": (
            "Porque no puede saberlo, y porque cualquier herramienta que te lo diga con "
            "seguridad te está mintiendo o vendiendo algo.\n\n"
            "Lo que sí puede hacer, y hace: filtrar 250 monedas hasta dejarte 10 que "
            "cumplen criterios objetivos de liquidez, desarrollo y tokenomics, para que "
            "tú investigues esas 10 en vez de las 250."
        ),
    },
    {
        "pregunta": "¿Cada cuánto debería mirar esto?",
        "respuesta": (
            "Una vez al día por la mañana, como máximo. Idealmente, una vez a la semana.\n\n"
            "Mirar la cartera muchas veces al día está correlacionado con tomar peores "
            "decisiones: ves más ruido, sientes más las caídas y acabas operando por "
            "ansiedad."
        ),
    },
    {
        "pregunta": "¿Qué hago con los impuestos en España?",
        "respuesta": (
            "Cada venta con ganancia tributa como ganancia patrimonial en el IRPF "
            "(tramos que empiezan en el 19%). Comprar y mantener no tributa: solo tributa "
            "cuando vendes o cambias una cripto por otra.\n\n"
            "Ojo con eso último: cambiar BTC por ETH es un hecho imponible aunque no hayas "
            "sacado euros.\n\n"
            "El informe guarda el histórico de precios, pero no es un software fiscal ni "
            "yo soy asesor fiscal. Si el volumen crece, habla con un gestor."
        ),
    },
    {
        "pregunta": "¿Es mejor el ETF en dólares o el cubierto en euros?",
        "respuesta": (
            "Depende del plazo, y la respuesta habitual sorprende a la gente.\n\n"
            "Para renta variable a 15-20 años, lo que suele recomendarse es el NO "
            "cubierto. Las divisas oscilan, pero no tienen una tendencia clara a largo "
            "plazo: se compensan solas. La cobertura, en cambio, la pagas todos los años "
            "en comisión y en coste implícito.\n\n"
            "El cubierto tiene sentido si el plazo es corto, si vas a necesitar el dinero "
            "en una fecha concreta, o si la oscilación adicional te va a llevar a vender "
            "en mal momento. Esto último no es una cuestión menor: el mejor producto es "
            "el que consigues mantener.\n\n"
            "En el informe verás el TER de cada uno y la diferencia traducida a euros a "
            "30 años, que es la forma honesta de comparar."
        ),
    },
    {
        "pregunta": "El mercado está en máximos. ¿Espero a que baje?",
        "respuesta": (
            "Es la pregunta más natural del mundo y la que peor ha funcionado "
            "históricamente.\n\n"
            "Un índice está en máximos precisamente porque sube a largo plazo: es su "
            "estado normal, no una anomalía. El S&P 500 ha marcado máximos históricos en "
            "torno al 6-7% de todas las sesiones de su historia.\n\n"
            "Los estudios que comparan invertir todo de golpe frente a repartirlo en el "
            "tiempo dan ventaja a hacerlo de golpe en torno al 65-70% de los casos, "
            "simplemente porque el mercado sube más días de los que baja.\n\n"
            "Dicho esto, repartir la entrada (DCA) sigue siendo muy razonable, no porque "
            "dé más rentabilidad esperada, sino porque reduce el arrepentimiento y hace "
            "que aguantes el plan. Y aguantar el plan es lo que de verdad determina el "
            "resultado."
        ),
    },
    {
        "pregunta": "¿Cuánto dinero debería meter en cripto?",
        "respuesta": (
            "La pregunta correcta no es cuánto quieres ganar, es cuánto puedes perder "
            "sin que te cambie la vida.\n\n"
            "La referencia habitual entre gente sensata es entre el 1% y el 10% del "
            "patrimonio invertible, y solo después de tener un colchón de emergencia en "
            "efectivo.\n\n"
            "Prueba mental: si mañana tu posición vale la mitad, ¿te afecta al sueño o a "
            "tus planes? Si la respuesta es sí, es demasiado."
        ),
    },
]
