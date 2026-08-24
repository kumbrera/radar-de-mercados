"""Hoja de estilos del informe. Se inyecta entera en el HTML generado."""

ESTILOS = """
/* ---------------------------------------------------------------------------
   Tokens. El tema claro se define en :root; el oscuro solo redefine tokens,
   nunca componentes, para que funcione tanto con la preferencia del sistema
   como con una elección explícita.
--------------------------------------------------------------------------- */
:root {
  --ground:        #f3f5f8;
  --superficie:    #ffffff;
  --superficie-2:  #eaeef3;
  --tinta:         #161c23;
  --tinta-2:       #3c4855;
  --tenue:         #66747f;
  --linea:         #dce2e9;
  --linea-fuerte:  #c2ccd6;
  --acento:        #0d6f79;
  --acento-tinta:  #0a565e;
  --acento-suave:  #e0eff0;
  --pos:           #146b53;
  --pos-suave:     #e1f2eb;
  --neg:           #a83a29;
  --neg-suave:     #fbe8e4;
  --alerta:        #8a5c00;
  --alerta-suave:  #fbf0da;
  --sombra:        0 1px 2px rgba(22,28,35,.05), 0 10px 26px -18px rgba(22,28,35,.45);
  --radio:         12px;
  --radio-s:       7px;
  --f-display: "Bricolage Grotesque", "Trebuchet MS", Verdana, sans-serif;
  --f-texto:   "Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --f-mono:    "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground:       #0e1217;
    --superficie:   #161b22;
    --superficie-2: #1d242c;
    --tinta:        #e6ebf1;
    --tinta-2:      #b9c4d0;
    --tenue:        #85929f;
    --linea:        #29313a;
    --linea-fuerte: #3a444f;
    --acento:       #4dc3cd;
    --acento-tinta: #7ad5dd;
    --acento-suave: #123034;
    --pos:          #4fc08d;
    --pos-suave:    #12302a;
    --neg:          #ef8674;
    --neg-suave:    #331d1b;
    --alerta:       #e2ab45;
    --alerta-suave: #322611;
    --sombra:       0 1px 2px rgba(0,0,0,.4), 0 10px 26px -18px rgba(0,0,0,.9);
  }
}

:root[data-theme="dark"] {
  --ground:       #0e1217;
  --superficie:   #161b22;
  --superficie-2: #1d242c;
  --tinta:        #e6ebf1;
  --tinta-2:      #b9c4d0;
  --tenue:        #85929f;
  --linea:        #29313a;
  --linea-fuerte: #3a444f;
  --acento:       #4dc3cd;
  --acento-tinta: #7ad5dd;
  --acento-suave: #123034;
  --pos:          #4fc08d;
  --pos-suave:    #12302a;
  --neg:          #ef8674;
  --neg-suave:    #331d1b;
  --alerta:       #e2ab45;
  --alerta-suave: #322611;
  --sombra:       0 1px 2px rgba(0,0,0,.4), 0 10px 26px -18px rgba(0,0,0,.9);
}

/* ------------------------------------------------------------------ base -- */
* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--ground);
  color: var(--tinta);
  font-family: var(--f-texto);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.pagina {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 20px 80px;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

h1, h2, h3 { font-family: var(--f-display); text-wrap: balance; margin: 0; line-height: 1.15; }
h1 { font-size: clamp(2.1rem, 5vw, 3.1rem); font-weight: 700; letter-spacing: -.025em; }
h2 { font-size: clamp(1.35rem, 2.6vw, 1.75rem); font-weight: 700; letter-spacing: -.015em; }
h3 { font-size: 1.05rem; font-weight: 700; }
p { margin: 0; }
em { font-style: italic; }

.eyebrow {
  font-family: var(--f-mono);
  font-size: .69rem;
  font-weight: 500;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--tenue);
}

.mono { font-family: var(--f-mono); font-variant-numeric: tabular-nums; }
.num  { text-align: right; }
.pos  { color: var(--pos); }
.neg  { color: var(--neg); }
.neutro { color: var(--tenue); }
.tenue  { color: var(--tenue); }
.oculto {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}

a { color: var(--acento); text-underline-offset: 3px; }
:focus-visible { outline: 2px solid var(--acento); outline-offset: 2px; border-radius: 3px; }

/* -------------------------------------------------------------- cabecera -- */
.cabecera {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 24px;
  border-bottom: 2px solid var(--linea-fuerte);
}
.cabecera-txt { display: flex; flex-direction: column; gap: 8px; max-width: 62ch; }
.lema { color: var(--tinta-2); font-size: 1.02rem; }
.indice a {
  font-family: var(--f-mono); font-size: .78rem; text-decoration: none;
  border: 1px solid var(--linea-fuerte); border-radius: 999px;
  padding: 7px 15px; color: var(--tinta-2); background: var(--superficie);
  transition: border-color .15s, color .15s;
}
.indice a:hover { border-color: var(--acento); color: var(--acento); }

/* ----------------------------------------------------------------- pulso -- */
.pulso {
  background: var(--superficie);
  border: 1px solid var(--linea);
  border-radius: var(--radio);
  box-shadow: var(--sombra);
  overflow: hidden;
}
.pulso-rejilla { display: grid; grid-template-columns: minmax(0, 1fr); }
@media (min-width: 900px) { .pulso-rejilla { grid-template-columns: 1.05fr 1fr; } }

.pulso-titular {
  padding: 26px 28px;
  display: flex; flex-direction: column; gap: 10px;
  border-left: 5px solid var(--linea-fuerte);
}
.pulso-titular.tono-positivo { border-left-color: var(--pos); }
.pulso-titular.tono-negativo { border-left-color: var(--neg); }
.pulso-titular.tono-neutro   { border-left-color: var(--tenue); }
.titular { font-family: var(--f-display); font-size: 1.7rem; font-weight: 700; letter-spacing: -.02em; }
.titular-detalle { color: var(--tinta-2); font-size: .95rem; }

.instrumentos {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  border-top: 1px solid var(--linea);
}
@media (min-width: 900px) { .instrumentos { border-top: 0; border-left: 1px solid var(--linea); } }
.instr {
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 5px;
  border-bottom: 1px solid var(--linea);
}
.instr:nth-child(odd) { border-right: 1px solid var(--linea); }
.instr:nth-last-child(-n+2) { border-bottom: 0; }
.instr-lab { font-size: .75rem; color: var(--tenue); text-transform: uppercase; letter-spacing: .07em; font-family: var(--f-mono); }
.instr-val { font-family: var(--f-mono); font-size: 1.28rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.instr-sub { font-size: .82rem; color: var(--tenue); }
.instr-fng { align-items: flex-start; }

.amplitud { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
.amplitud-pista { height: 9px; border-radius: 999px; background: var(--neg-suave); overflow: hidden; }
.amplitud-sube { display: block; height: 100%; background: var(--pos); }
.amplitud-pie { display: flex; justify-content: space-between; font-size: .76rem; font-family: var(--f-mono); }

.fng { position: relative; width: 128px; }
.fng svg { width: 128px; height: 78px; display: block; }
.fng-num { font-family: var(--f-mono); font-size: 1.45rem; font-weight: 600; text-align: center; margin-top: -26px; }
.fng-lab { font-size: .78rem; text-align: center; color: var(--tenue); }
.fng-miedo-ext, .fng-miedo { color: var(--neg); }
.fng-neutral { color: var(--tenue); }
.fng-codicia, .fng-codicia-ext { color: var(--alerta); }

/* -------------------------------------------------------------- secciones -- */
.bloque-seccion { display: flex; flex-direction: column; gap: 18px; }
.seccion-intro { color: var(--tinta-2); max-width: 72ch; }
.sub { font-size: .95rem; color: var(--tenue); text-transform: uppercase; letter-spacing: .08em; font-family: var(--f-mono); font-weight: 500; }
.nota-pie { font-size: .88rem; color: var(--tenue); max-width: 78ch; }

.vacio-ok {
  background: var(--pos-suave);
  border: 1px solid var(--linea);
  border-left: 5px solid var(--pos);
  border-radius: var(--radio-s);
  padding: 18px 22px;
  display: flex; flex-direction: column; gap: 6px;
}
.vacio-ok p { color: var(--tinta-2); }
.vacio-ok strong { color: var(--tinta); }

/* --------------------------------------------------------------- señales -- */
.senales { display: flex; flex-direction: column; gap: 12px; }
.senal {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  background: var(--superficie);
  border: 1px solid var(--linea);
  border-radius: var(--radio-s);
  overflow: hidden;
}
.senal-marca {
  display: grid; place-items: center;
  font-family: var(--f-mono); font-weight: 600; font-size: .95rem;
  color: var(--superficie);
}
.senal-positivo .senal-marca { background: var(--pos); }
.senal-negativo .senal-marca { background: var(--neg); }
.senal-alerta   .senal-marca { background: var(--alerta); }
.senal-neutro   .senal-marca { background: var(--tenue); }
.senal-cuerpo { padding: 15px 18px; display: flex; flex-direction: column; gap: 5px; }
.senal-tit { font-size: 1.02rem; }
.senal-dato { font-family: var(--f-mono); font-size: .84rem; color: var(--tinta-2); }
.senal-txt, .senal-ojo { font-size: .92rem; color: var(--tinta-2); max-width: 80ch; }
.senal-ojo { color: var(--tenue); }
.senal-txt strong, .senal-ojo strong { color: var(--tinta); font-weight: 600; }

/* --------------------------------------------------------------- monedas -- */
.rejilla-monedas {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
  gap: 14px;
}
.moneda {
  background: var(--superficie);
  border: 1px solid var(--linea);
  border-radius: var(--radio);
  padding: 18px;
  display: flex; flex-direction: column; gap: 14px;
  box-shadow: var(--sombra);
}
.moneda-cab { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; }
.moneda-cab h3 { display: flex; align-items: baseline; gap: 7px; }
.ticker {
  font-family: var(--f-mono); font-size: .72rem; font-weight: 500;
  color: var(--tenue); background: var(--superficie-2);
  padding: 2px 6px; border-radius: 4px; letter-spacing: .04em;
}
.moneda-precio { font-family: var(--f-mono); font-size: 1.12rem; font-weight: 600; margin-top: 4px; font-variant-numeric: tabular-nums; }
.delta { font-size: .8rem; margin-left: 6px; font-weight: 500; }
.moneda-spark { width: 132px; flex-shrink: 0; display: flex; flex-direction: column; gap: 2px; }
.spark { width: 100%; height: 56px; display: block; }
.spark-pos { color: var(--pos); }
.spark-neg { color: var(--neg); }
.spark-pie { font-family: var(--f-mono); font-size: .66rem; color: var(--tenue); text-align: right; }
.spark-vacio { font-size: .78rem; color: var(--tenue); font-style: italic; }

/* ------------------------------------------------------------------- rsi -- */
.rsi { display: flex; flex-direction: column; gap: 5px; }
.rsi-cab { display: flex; justify-content: space-between; align-items: baseline; }
.rsi-lab { font-size: .78rem; color: var(--tenue); font-family: var(--f-mono); }
.rsi-val { font-family: var(--f-mono); font-weight: 600; font-size: 1rem; }
.rsi-val small { font-weight: 400; color: var(--tenue); font-size: .72rem; }
.rsi-pista {
  position: relative; height: 8px; border-radius: 999px;
  background: var(--superficie-2); border: 1px solid var(--linea); overflow: hidden;
}
.rsi-zona { position: absolute; top: 0; bottom: 0; }
.rsi-zona-baja { left: 0; width: 30%; background: var(--pos-suave); }
.rsi-zona-alta { right: 0; width: 30%; background: var(--alerta-suave); }
.rsi-aguja {
  position: absolute; top: -3px; width: 3px; height: 14px;
  border-radius: 2px; background: var(--tinta); transform: translateX(-50%);
}
.rsi-pie { display: flex; justify-content: space-between; font-size: .7rem; color: var(--tenue); font-family: var(--f-mono); }
.rsi-estado { font-weight: 500; }
.rsi-bajo  { color: var(--pos); }
.rsi-alto  { color: var(--alerta); }
.rsi-medio { color: var(--tenue); }
.rsi-aguja.rsi-bajo { background: var(--pos); }
.rsi-aguja.rsi-alto { background: var(--alerta); }
.rsi-aguja.rsi-medio { background: var(--tinta-2); }

/* ------------------------------------------------------------------ datos -- */
.datos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  gap: 10px 12px;
  padding-top: 12px;
  border-top: 1px solid var(--linea);
}
.dato { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.dato-lab { font-size: .7rem; color: var(--tenue); text-transform: uppercase; letter-spacing: .05em; font-family: var(--f-mono); }
.dato-val { font-size: .92rem; font-weight: 500; }

.mini-lista { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 5px; }
.mini {
  font-size: .82rem; color: var(--tinta-2);
  padding: 6px 10px; border-radius: var(--radio-s);
  border-left: 3px solid var(--tenue); background: var(--superficie-2);
}
.mini strong { color: var(--tinta); font-weight: 600; }
.mini-positivo { border-left-color: var(--pos); }
.mini-negativo { border-left-color: var(--neg); }
.mini-alerta   { border-left-color: var(--alerta); }
.sin-senal { font-size: .84rem; color: var(--tenue); font-style: italic; }

/* ------------------------------------------------------------- proyectos -- */
.proyectos { display: flex; flex-direction: column; gap: 14px; }
.proyecto {
  background: var(--superficie);
  border: 1px solid var(--linea);
  border-left: 5px solid var(--linea-fuerte);
  border-radius: var(--radio);
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 14px;
  box-shadow: var(--sombra);
}
.proyecto-verde   { border-left-color: var(--pos); }
.proyecto-ambar   { border-left-color: var(--alerta); }
.proyecto-naranja { border-left-color: var(--alerta); }
.proyecto-rojo    { border-left-color: var(--neg); }

.proyecto-cab { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 14px; }
.rango { font-size: 1.35rem; color: var(--linea-fuerte); font-weight: 600; }
.proyecto-id h3 { display: flex; align-items: baseline; gap: 7px; flex-wrap: wrap; }
.proyecto-cats { font-size: .78rem; color: var(--tenue); font-family: var(--f-mono); }
.proyecto-nota { text-align: right; display: flex; flex-direction: column; align-items: flex-end; line-height: 1.1; }
.nota-num { font-family: var(--f-mono); font-size: 1.85rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.nota-de { font-family: var(--f-mono); font-size: .72rem; color: var(--tenue); margin-top: -4px; }
.nota-nivel { font-size: .74rem; color: var(--tenue); margin-top: 3px; text-transform: uppercase; letter-spacing: .05em; font-family: var(--f-mono); }

.proyecto-cifras {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
  gap: 10px 14px;
  padding-top: 12px;
  border-top: 1px solid var(--linea);
  align-items: end;
}
.proyecto-cifras > div { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.proyecto-cifras .mono { font-size: .92rem; font-weight: 500; }
.proyecto-spark { min-width: 110px; }
.proyecto-spark .spark { height: 40px; }

.flags { display: flex; flex-wrap: wrap; gap: 6px; }
.flag {
  font-family: var(--f-mono); font-size: .72rem;
  background: var(--neg-suave); color: var(--neg);
  border: 1px solid var(--neg); border-radius: 999px;
  padding: 3px 10px;
}

details { border-top: 1px solid var(--linea); padding-top: 10px; }
summary {
  cursor: pointer; font-size: .86rem; color: var(--acento);
  font-weight: 600; list-style: none; display: flex; align-items: center; gap: 6px;
}
summary::-webkit-details-marker { display: none; }
summary::before { content: "▸"; font-size: .75rem; transition: transform .15s; }
details[open] > summary::before { transform: rotate(90deg); }
.desglose-pie { font-size: .78rem; color: var(--tenue); font-family: var(--f-mono); margin-top: 10px; }
.flags-detalle ul { margin: 8px 0 0; padding-left: 18px; font-size: .87rem; color: var(--tinta-2); display: flex; flex-direction: column; gap: 5px; }
.flags-detalle strong { color: var(--tinta); }

.bloques { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-top: 12px; }
.bloque { display: flex; flex-direction: column; gap: 4px; }
.bloque-cab { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.bloque-nom { font-size: .84rem; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.peso { font-family: var(--f-mono); font-size: .68rem; color: var(--tenue); font-weight: 400; }
.bloque-nota { font-family: var(--f-mono); font-size: .86rem; font-weight: 600; }
.bloque-pista { height: 5px; border-radius: 999px; background: var(--superficie-2); overflow: hidden; }
.bloque-relleno { display: block; height: 100%; border-radius: 999px; }
.nota-alta  { color: var(--pos); }
.nota-media { color: var(--alerta); }
.nota-baja  { color: var(--neg); }
.bloque-relleno.nota-alta  { background: var(--pos); }
.bloque-relleno.nota-media { background: var(--alerta); }
.bloque-relleno.nota-baja  { background: var(--neg); }
.bloque-txt { font-size: .82rem; color: var(--tenue); }

/* ---------------------------------------------------------------- tablas -- */
.tablas { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
.tabla-caja {
  background: var(--superficie); border: 1px solid var(--linea);
  border-radius: var(--radio); padding: 16px 18px;
  display: flex; flex-direction: column; gap: 10px;
}
.tabla-tit { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; font-family: var(--f-mono); font-weight: 600; }
.tabla-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: .87rem; }
th {
  text-align: left; font-family: var(--f-mono); font-size: .68rem;
  text-transform: uppercase; letter-spacing: .06em; color: var(--tenue);
  font-weight: 500; padding: 0 8px 7px 0; border-bottom: 1px solid var(--linea);
}
td { padding: 7px 8px 7px 0; border-bottom: 1px solid var(--linea); white-space: nowrap; }
tr:last-child td { border-bottom: 0; }
.fila-nom { font-weight: 500; }

/* -------------------------------------------------------------- glosario -- */
.dos-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 26px; align-items: start; }
.dos-col > div { display: flex; flex-direction: column; gap: 12px; }
.glosa-lista { display: flex; flex-direction: column; gap: 8px; }
.glosa-entrada {
  background: var(--superficie); border: 1px solid var(--linea);
  border-top: 1px solid var(--linea);
  border-radius: var(--radio-s); padding: 12px 15px;
}
.glosa-entrada summary { color: var(--tinta); font-size: .92rem; align-items: baseline; gap: 8px; }
.glosa-entrada summary::before { flex: none; align-self: flex-start; margin-top: .35em; }
.glosa-texto { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.glosa-corto { font-weight: 400; font-size: .8rem; color: var(--tenue); line-height: 1.45; }
.glosa-largo { display: flex; flex-direction: column; gap: 9px; margin-top: 10px; font-size: .89rem; color: var(--tinta-2); max-width: 68ch; }

/* ------------------------------------------------------- botones de ayuda -- */
.term { white-space: nowrap; }
.ayuda {
  font-family: var(--f-mono); font-size: .62rem; font-weight: 600;
  width: 15px; height: 15px; padding: 0; margin-left: 4px;
  border-radius: 50%; border: 1px solid var(--linea-fuerte);
  background: var(--superficie-2); color: var(--tenue);
  cursor: pointer; vertical-align: middle; line-height: 1;
  transition: background .15s, color .15s, border-color .15s;
}
.ayuda:hover { background: var(--acento); color: var(--superficie); border-color: var(--acento); }

.glosa-modal {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(10, 14, 18, .55);
  display: grid; place-items: center; padding: 22px;
  backdrop-filter: blur(2px);
}
.glosa-modal[hidden] { display: none; }
.glosa-panel {
  position: relative;
  background: var(--superficie); color: var(--tinta);
  border: 1px solid var(--linea-fuerte); border-radius: var(--radio);
  padding: 26px 28px; max-width: 560px; width: 100%;
  max-height: 80vh; overflow-y: auto;
  box-shadow: 0 24px 60px -20px rgba(0,0,0,.5);
  display: flex; flex-direction: column; gap: 12px;
}
.glosa-panel h3 { font-size: 1.2rem; padding-right: 30px; }
.glosa-panel p { font-size: .93rem; color: var(--tinta-2); }
.glosa-cerrar {
  position: absolute; top: 14px; right: 16px;
  width: 30px; height: 30px; border-radius: 50%;
  border: 1px solid var(--linea); background: var(--superficie-2);
  color: var(--tinta-2); font-size: 1.15rem; line-height: 1; cursor: pointer;
}
.glosa-cerrar:hover { background: var(--linea); }

/* ---------------------------------------------------------------- cierre -- */
.cierre {
  background: var(--superficie-2);
  border: 1px solid var(--linea);
  border-radius: var(--radio);
  padding: 26px 28px;
  display: flex; flex-direction: column; gap: 11px;
}
.cierre p { color: var(--tinta-2); font-size: .93rem; max-width: 76ch; }
.meta {
  font-family: var(--f-mono); font-size: .73rem; color: var(--tenue);
  border-top: 1px solid var(--linea); padding-top: 12px; margin-top: 6px;
}

/* --------------------------------------------------------------- índices -- */
.pulso-rejilla-bolsa { grid-template-columns: minmax(0, 1fr); }
@media (min-width: 980px) { .pulso-rejilla-bolsa { grid-template-columns: .9fr 1.1fr; } }

.indices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  border-top: 1px solid var(--linea);
}
@media (min-width: 980px) { .indices { border-top: 0; border-left: 1px solid var(--linea); } }
.indice {
  padding: 13px 16px;
  display: flex; flex-direction: column; gap: 1px;
  border-right: 1px solid var(--linea);
  border-bottom: 1px solid var(--linea);
  min-width: 0;
}
.indice-nom { font-size: .69rem; color: var(--tenue); font-family: var(--f-mono);
  text-transform: uppercase; letter-spacing: .06em; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.indice-val { font-size: 1.08rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.indice-cambio { font-size: .8rem; font-weight: 500; }
.indice-spark { margin-top: 5px; }
.indice-spark .spark { height: 28px; }

/* --------------------------------------------------------------- cartera -- */
.cartera-resumen {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 1px;
  background: var(--linea);
  border: 1px solid var(--linea);
  border-radius: var(--radio);
  overflow: hidden;
}
.cartera-cifra {
  background: var(--superficie);
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 3px;
}
.cartera-total { font-size: 1.85rem; font-weight: 600; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
.cartera-sub { font-size: 1.35rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.cartera-pct { font-size: .85rem; font-weight: 500; }
.cartera-hoy { font-size: .82rem; font-weight: 500; }

.etiqueta-tipo {
  font-family: var(--f-mono); font-size: .63rem; font-weight: 500;
  padding: 2px 6px; border-radius: 4px; margin-left: 6px;
  text-transform: uppercase; letter-spacing: .05em;
  border: 1px solid var(--linea-fuerte); color: var(--tenue);
}
.etiqueta-etf    { border-color: var(--acento); color: var(--acento); }
.etiqueta-cripto { border-color: var(--alerta); color: var(--alerta); }

.sub-bloque { display: flex; flex-direction: column; gap: 12px; margin-top: 22px; }

.reparto { display: flex; flex-direction: column; gap: 15px; }
.reparto-fila { display: flex; flex-direction: column; gap: 5px; }
.reparto-cab { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; }
.reparto-nom { font-weight: 600; font-size: .93rem; }
.reparto-cifras { font-size: .85rem; display: flex; gap: 9px; align-items: baseline; }
.reparto-pista {
  position: relative; height: 12px; border-radius: 4px;
  background: var(--superficie-2); border: 1px solid var(--linea); overflow: hidden;
}
.reparto-real { display: block; height: 100%; background: var(--acento); opacity: .85; }
.reparto-objetivo {
  position: absolute; top: -2px; bottom: -2px; width: 2px;
  background: var(--tinta); transform: translateX(-1px);
}
.reparto-ok    .reparto-real { background: var(--pos); }
.reparto-sobre .reparto-real { background: var(--alerta); }
.reparto-bajo  .reparto-real { background: var(--acento); }
.reparto-txt { font-size: .84rem; color: var(--tenue); }

.aportacion { display: flex; flex-direction: column; gap: 9px; }
.aport-fila {
  display: grid; grid-template-columns: minmax(110px, 150px) 1fr auto;
  align-items: center; gap: 12px;
}
.aport-nom { font-size: .88rem; font-weight: 500; }
.aport-pista { height: 9px; border-radius: 999px; background: var(--superficie-2);
  border: 1px solid var(--linea); overflow: hidden; }
.aport-pista span { display: block; height: 100%; background: var(--acento); }
.aport-importe { font-size: .92rem; font-weight: 600; font-variant-numeric: tabular-nums; }

/* ------------------------------------------------------------------ etfs -- */
.etfs { display: flex; flex-direction: column; gap: 14px; }
.etf {
  background: var(--superficie);
  border: 1px solid var(--linea);
  border-left: 5px solid var(--linea-fuerte);
  border-radius: var(--radio);
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 14px;
  box-shadow: var(--sombra);
}
.etf-verde   { border-left-color: var(--pos); }
.etf-ambar   { border-left-color: var(--alerta); }
.etf-naranja { border-left-color: var(--alerta); }
.etf-rojo    { border-left-color: var(--neg); }
.etf .proyecto-cab { grid-template-columns: minmax(0, 1fr) auto; }

.chip {
  font-family: var(--f-mono); font-size: .66rem;
  padding: 2px 8px; border-radius: 999px; margin-left: 6px;
  border: 1px solid var(--acento); color: var(--acento); background: var(--acento-suave);
}

.comparativa {
  background: var(--acento-suave);
  border: 1px solid var(--acento);
  border-radius: var(--radio);
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 7px;
}
.comparativa-txt { font-size: .92rem; color: var(--tinta); max-width: 80ch; }
.comparativa-txt strong { font-weight: 600; }
.comparativa-aviso { font-size: .82rem; color: var(--tinta-2); font-style: italic; }

.holdings { list-style: none; margin: 9px 0 0; padding: 0;
  display: flex; flex-direction: column; gap: 5px; font-size: .86rem; }
.holdings li { display: flex; justify-content: space-between; gap: 12px;
  color: var(--tinta-2); border-bottom: 1px dotted var(--linea); padding-bottom: 4px; }

.vacio-neutro { background: var(--superficie-2); border-left-color: var(--acento); }
code {
  font-family: var(--f-mono); font-size: .86em;
  background: var(--superficie-2); border: 1px solid var(--linea);
  padding: 1px 5px; border-radius: 4px;
}

.aviso-csv {
  background: var(--alerta-suave);
  border: 1px solid var(--alerta);
  border-left: 5px solid var(--alerta);
  border-radius: var(--radio-s);
  padding: 15px 18px;
  display: flex; flex-direction: column; gap: 8px;
  font-size: .9rem; color: var(--tinta-2);
}
.aviso-csv strong { color: var(--tinta); }
.aviso-csv ul { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 4px; }
.aviso-csv li { font-family: var(--f-mono); font-size: .82rem; }

.traducciones { border-top: 0; padding-top: 0; }
.traducciones-txt { font-size: .86rem; color: var(--tenue); max-width: 74ch; margin: 10px 0; }
.traduccion {
  background: var(--superficie-2); border: 1px solid var(--linea);
  border-radius: var(--radio-s); padding: 11px 14px; margin-bottom: 8px;
}
.traduccion-linea { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: .87rem; }
.traduccion-linea .flecha { color: var(--tenue); }
.traduccion-linea .destino { border-color: var(--acento); color: var(--acento); font-weight: 600; }
.traduccion-nombre { color: var(--tinta-2); }
.alternativas { list-style: none; margin: 9px 0 0; padding: 0;
  display: flex; flex-direction: column; gap: 6px; font-size: .84rem; color: var(--tinta-2); }

pre.ejemplo {
  font-family: var(--f-mono); font-size: .8rem; line-height: 1.7;
  background: var(--superficie); border: 1px solid var(--linea);
  border-radius: var(--radio-s); padding: 12px 14px; margin: 0;
  overflow-x: auto; color: var(--tinta-2);
}

/* Respiro extra abajo para el gesto de inicio del móvil */
@media (max-width: 620px) {
  .pagina { padding: 20px 14px calc(72px + env(safe-area-inset-bottom)); gap: 34px; }
  h1 { font-size: 2rem; }
  .cabecera { align-items: flex-start; }
  .titular { font-size: 1.4rem; }
  .cartera-total { font-size: 1.55rem; }
  .senal { grid-template-columns: 32px minmax(0, 1fr); }
  .senal-cuerpo { padding: 13px 14px; }
  .proyecto, .etf, .moneda { padding: 15px 16px; }
  .proyecto-cab { gap: 10px; }
  .rango { font-size: 1.1rem; }
  .nota-num { font-size: 1.5rem; }
  .aport-fila { grid-template-columns: minmax(88px, 1fr) 1.4fr auto; gap: 9px; }
  .aport-nom { font-size: .82rem; }
}

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
"""
