# Fermin Bot — Estrategias de trading en futuros (5 minutos)

Cinco estrategias de trading para **futuros de BTC, XRP, XAUT y SOL**, todas
operando en velas de **5 minutos**, cada una construida con **dos
indicadores técnicos sencillos como máximo**, y que generan señales claras
de **compra (BUY)** y **venta/short (SELL)**.

> ⚠️ **Aviso de riesgo**: el trading de futuros usa apalancamiento y puede
> generar pérdidas superiores al capital invertido. Este código es un punto
> de partida educativo/técnico, no es asesoramiento financiero. Verifica
> siempre las señales con gestión de riesgo (stop-loss, tamaño de posición)
> antes de operar con dinero real.

## Símbolos y timeframe

- **Símbolos**: `BTC/USDT`, `XRP/USDT`, `XAUT/USDT`, `SOL/USDT` (futuros perpetuos)
- **Timeframe**: `5m`

## Las 5 estrategias

| # | Estrategia | Indicadores | Compra | Venta |
|---|-----------|-------------|--------|-------|
| 1 | [EMA Cross](strategies/strategy_1_ema_cross.py) | EMA(9), EMA(21) | EMA rápida cruza al alza la EMA lenta | EMA rápida cruza a la baja la EMA lenta |
| 2 | [RSI + SMA](strategies/strategy_2_rsi_sma.py) | RSI(14), SMA(50) | Precio > SMA(50) y RSI sale de sobreventa (cruza sobre 30) | Precio < SMA(50) y RSI sale de sobrecompra (cruza bajo 70) |
| 3 | [Bollinger + RSI](strategies/strategy_3_bollinger_rsi.py) | Bandas de Bollinger(20,2), RSI(14) | Cierre ≤ banda inferior y RSI < 30 | Cierre ≥ banda superior y RSI > 70 |
| 4 | [MACD Cross](strategies/strategy_4_macd.py) | Línea MACD(12,26), Señal(9) | Línea MACD cruza al alza la señal | Línea MACD cruza a la baja la señal |
| 5 | [Stochastic + EMA](strategies/strategy_5_stochastic_ema.py) | %K/%D(14,3), EMA(50) | %K cruza sobre %D en sobreventa (<20) y precio > EMA(50) | %K cruza bajo %D en sobrecompra (>80) y precio < EMA(50) |

Cada estrategia expone `generate_signals(df)`, que devuelve una serie de
`Signal.BUY` / `Signal.SELL` / `Signal.HOLD` alineada al índice del
DataFrame OHLCV de entrada.

## Estructura del proyecto

```
strategies/
  base.py                       # interfaz BaseStrategy + enum Signal
  indicators.py                 # SMA, EMA, RSI, Bollinger, MACD, Estocástico
  strategy_1_ema_cross.py
  strategy_2_rsi_sma.py
  strategy_3_bollinger_rsi.py
  strategy_4_macd.py
  strategy_5_stochastic_ema.py
data.py                         # descarga OHLCV vía ccxt + datos sintéticos de prueba
main.py                         # demo: aplica las 5 estrategias a los 4 símbolos
tests/                          # pruebas unitarias con pytest (incluye Alfred)
alfred/                         # asistente personal (ver sección Alfred)
pinescript/                     # las mismas 5 estrategias en Pine Script v5 (TradingView)
```

## Versión Pine Script (TradingView)

Las mismas 5 estrategias también están disponibles en Pine Script v5, listas
para pegar en el Pine Editor de TradingView: ver [`pinescript/`](pinescript/).

## Uso

```bash
pip install -r requirements.txt

# Con datos en vivo (requiere red; usa Binance USD-M Futures vía ccxt)
python main.py

# Sin red, con datos sintéticos de prueba
python main.py --sample
```

Ejemplo de uso programático:

```python
from data import fetch_ohlcv
from strategies import EmaCrossStrategy

df = fetch_ohlcv("BTC/USDT", limit=300)   # velas de 5m
strategy = EmaCrossStrategy()
print(strategy.last_signal(df))           # Signal.BUY / SELL / HOLD

signals = strategy.generate_signals(df)   # serie completa de señales
```

## Tests

```bash
pytest tests/ -v
```

---

# 🤖 Alfred — asistente personal

Asistente personal en español (estilo Jarvis), por texto, voz o Telegram,
conectado con Claude y pensado para **ir agregándole funciones**.

## Instalación

Necesitas **Python 3.11 o superior** (python.org). En Windows, al instalarlo
marca la casilla *"Add python.exe to PATH"*.

| | Windows | Mac |
|---|---|---|
| Instalar | doble clic en `instalar_windows.bat` | doble clic en `instalar_mac.command` (si lo bloquea: clic derecho → Abrir) |
| Hablar con Alfred | doble clic en `Alfred.bat` | doble clic en `Alfred.command` |
| Con voz | `Alfred.bat --voz` | `./Alfred.command --voz` (la voz necesita [Homebrew](https://brew.sh)) |
| Claves | abre `.env` con el Bloc de notas | `open -e .env` |

El instalador crea un entorno propio (`.venv`), instala todo, crea tu `.env`
y te pregunta si quieres que Alfred **arranque solo** al encender el
computador, que es lo que hace funcionar los recordatorios, los avisos de
clases, las noticias de las 6:00 y Telegram.

### Si usas Windows y Mac a la vez

- **Los mismos datos en los dos:** en el `.env` de cada computador pon
  `ALFRED_DATA_DIR` apuntando a una carpeta sincronizada (Google Drive,
  iCloud, OneDrive o Dropbox). Así tus gastos, agenda, notas y perfil son los
  mismos en ambos.
- **El arranque automático, solo en uno:** el que pase más tiempo encendido.
  Si lo activas en los dos, recibirías las noticias dos veces y el bot de
  Telegram no puede atender a dos Alfred a la vez. En el otro computador usa
  Alfred normalmente, sin `--servicio`.
- **Cierra `gastos.xlsx` en Excel** antes de anotar gastos: en Windows un
  archivo abierto en Excel no se puede modificar (Alfred te avisa si pasa).

Comandos manuales (con el entorno activado):

```bash
python -m alfred              # modo texto
python -m alfred --voz        # modo voz
python -m alfred --servicio   # en segundo plano: avisos, noticias y Telegram
```

**Moneda:** viene en pesos chilenos (`$15.990`) y entiende "lucas" y "palos"
("gasté 5 lucas en bencina"). Para otra moneda: `ALFRED_MONEDA=USD` en el `.env`.

## Funciones

| # | Función | Ejemplos |
|---|---|---|
| 1 | **Organizar archivos** (por tipo o fecha, con confirmación y "deshacer") | "organiza mis descargas", "organiza el escritorio por fecha", "deshaz la organización", "archivos más grandes de descargas" |
| 2 | **Auditar tu tienda Shopify** (Excel de problemas) y **hacer cambios** con confirmación | "audita mi tienda"; con Claude: "mejora la descripción y el SEO del sérum", "pon el labial a 15.990" |
| 3 | **Noticias de cripto, forex y acciones por correo** cada día a las 6:00 | automático en `--servicio`; "noticias del día", "mándame las noticias" |
| 4 | **Canchas**: abre EasyCancha y agenda la reserva | "reserva una cancha" |
| 5 | **Aviso un día antes** de tus clases, con quién son, para escribirle | "tengo clase con Juan el martes a las 18", "todos los jueves clase con Sofía a las 19" |
| 6 | **Recordatorios** | "recuérdame mañana a las 9 pagar la luz", "recuérdame en 20 minutos sacar la ropa" |
| 7 | **Ayuda con tus negocios online** (Claude + tu perfil) e ideas guardadas | "dame 10 ideas de videos faceless", "guarda la idea …", "mis ideas" |
| 8 | **Calendario de torneos** (exportable a Google Calendar) | "agenda el torneo Copa Primavera el 20 de diciembre a las 10", "mis próximos torneos", "exporta mi calendario" |
| 9 | **Control desde el celular** (Telegram) y del PC | escribe a tu bot; "abre youtube", "abre spotify" |
| 10 | **Orientación de inversiones** según tu perfil de inversor (educativa) | "¿cómo debería repartir 200 dólares al mes según mi perfil?" |
| — | Gastos en Excel, reporte mensual, señales de trading | "gasté 25 en el súper", "reporte del mes", "señal de btc" |

Di **"ayuda"** para ver la lista completa. Antes de mover archivos o cambiar
la tienda, Alfred te muestra el plan y espera tu **"sí"**.

## Tu perfil (`datos_alfred/perfil.md`)

La primera vez se crea una plantilla. Rellénala con tus negocios (tienda,
influencer con IA, canal faceless, portafolio), tu **perfil de inversor**
(objetivo, horizonte, tolerancia al riesgo) y tus torneos. Claude la lee en
cada conversación para darte ayuda personalizada.

## Configuración (archivo `.env`)

Copia `.env.ejemplo` como `.env`. Todo es opcional: configura solo lo que uses.

**Claude** — `ANTHROPIC_API_KEY` desde console.anthropic.com. Sin Claude
funcionan los comandos fijos; con Claude entiende frases libres, busca en
internet y usa todas las funciones.

**Correo (Gmail)** — activa la verificación en 2 pasos en tu cuenta de Google,
crea una *contraseña de aplicación* (Cuenta de Google → Seguridad →
Contraseñas de aplicaciones) y pon `ALFRED_EMAIL_USER` y
`ALFRED_EMAIL_PASSWORD`. Hora de las noticias: `ALFRED_HORA_NOTICIAS=06:00`.

**Telegram** — en Telegram habla con @BotFather, envía `/newbot` y copia el
token en `ALFRED_TELEGRAM_TOKEN`. Escríbele algo a tu bot, ejecuta
`python -m alfred --telegram-id` y pon el número en `ALFRED_TELEGRAM_CHAT_ID`.
Alfred solo responde a ese chat. Los recordatorios y avisos también te
llegan por ahí.

**Shopify** — crea una app para tu tienda (en el admin de Shopify: Configuración
→ Apps → Desarrollar apps, o desde el Dev Dashboard de Shopify) con permisos
`read_products` y `write_products`, y copia el token de Admin API en
`ALFRED_SHOPIFY_TOKEN`. En `ALFRED_SHOPIFY_STORE` pon el nombre que va antes de
`.myshopify.com`.

**Aviso de clases y torneos** — `ALFRED_HORA_AVISO=10:00` (hora a la que te
avisa de lo que tienes mañana).

## Arranque automático

Lo configura el instalador. El registro de lo que hace queda en
`datos_alfred/alfred.log`. Para quitarlo: en Windows borra `Alfred.vbs` de la
carpeta de inicio (`Win+R` → `shell:startup`); en Mac abre
`desinstalar_inicio_automatico.command`. Si el computador estaba apagado a
las 6:00, las noticias se envían al encenderlo (hasta las 12:00).

## Cómo agregar funciones nuevas

1. Copia `alfred/commands/_plantilla.py` a `alfred/commands/mi_funcion.py`.
   Cada archivo de esa carpeta se carga solo.
2. Usa `@command` para frases fijas y `@tool` para que Claude pueda usarla:

```python
from alfred.core import command, tool

@command("saludo formal", r"^presentate$", help="Se presenta.", examples=["preséntate"])
def presentate(ctx, match, texto):
    return "Soy Alfred, a su servicio."

@tool("convertir_moneda", "Convierte un monto entre monedas.",
      {"monto": {"type": "number"}, "de": {"type": "string"}, "a": {"type": "string"}})
def convertir(ctx, args):
    ...
    return "resultado"
```

Los patrones de `@command` se comparan con el texto en minúsculas y sin
tildes. Para acciones delicadas usa `ask_confirmation(ctx, "descripción", accion)`.

```
alfred/
  core.py        # comandos, herramientas, confirmaciones, .env
  brain.py       # Claude: herramientas, búsqueda web y perfil
  tareas.py      # recordatorios, aviso del día antes, noticias de las 6:00
  agenda.py      # clases, torneos, eventos y recordatorios (+ exportar .ics)
  dateparse.py   # fechas en español ("mañana a las 9", "todos los martes")
  expenses.py    # Excel de gastos y reportes
  files.py       # organizar carpetas
  shopify.py     # auditoría y cambios en Shopify
  news.py        # resumen de noticias con búsqueda web
  notify.py      # avisos por pantalla, correo y Telegram
  telegram.py    # bot de Telegram
  profile.py     # plantilla del perfil
  commands/      # agenda, archivos, gastos, general, noticias, notas, pc, tienda, trading
```
