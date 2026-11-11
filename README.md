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
tests/                          # pruebas unitarias con pytest (incluye Jarvis)
jarvis/                         # asistente personal (ver sección Jarvis)
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

# 🤖 Jarvis — asistente personal

Prototipo de asistente tipo Jarvis, en español, pensado para **ir agregándole
comandos**. Funciona por texto o por voz.

```bash
python -m jarvis                         # modo texto
python -m jarvis --voz                   # modo voz (micrófono + altavoz)
python -m jarvis -c "gasté 20 en café"   # un solo comando
```

## Conectado con Claude 🧠

Si configuras tu clave de la API de Anthropic, todo lo que no entienda un
comando fijo lo responde **Claude**. Claude conversa contigo, recuerda la
conversación y **puede usar los comandos de Jarvis**:

```bash
export ANTHROPIC_API_KEY="tu-clave"   # Windows: set ANTHROPIC_API_KEY=tu-clave
python -m jarvis
```

Ejemplos que solo funcionan con Claude:

- "Ayer almorcé con Ana, pagué la mitad de 600 y luego un uber de 200" → anota 300 en Comida y 200 en Transporte
- "¿Estoy gastando mucho en comida comparado con transporte?"
- "¿Qué opinan mis estrategias sobre Solana ahora mismo?"

Cómo funciona: primero se prueban los comandos fijos (rápidos y sin costo);
solo si ninguno entiende la frase se llama a Claude. Claude tiene dos
herramientas: `registrar_gasto` y `ejecutar_comando`, que puede lanzar
**cualquier** comando registrado con `@command`. Así, los comandos nuevos que
agregues también los puede usar Claude sin tocar nada más.

| Variable | Para qué | Por defecto |
|---|---|---|
| `ANTHROPIC_API_KEY` | Tu clave (consíguela en console.anthropic.com) | — |
| `JARVIS_MODEL` | Modelo de Claude | `claude-opus-5-5` |
| `JARVIS_EFFORT` | `low` (rápido), `medium` o `high` (piensa más) | `low` |

Di "nueva conversación" para que Claude olvide la charla, o arranca con
`python -m jarvis --sin-claude` para usar solo los comandos fijos. Cada
consulta a Claude tiene un costo según el uso de la API.

## Lo que sabe hacer

| Comando | Ejemplos |
|---|---|
| Registrar gasto | "gasté 25.50 en el súper", "pagué 1.200 de renta", "anota gasto de 300 en uber", "gasté 2 mil en ropa", "compré 40 de regalo categoría ocio" |
| Resumen | "¿cuánto llevo gastado este mes?", "¿en qué estoy gastando?", "¿cuánto gasté en octubre?" |
| Reporte mensual (Excel) | "reporte del mes", "reporte del mes pasado", "reporte de octubre" |
| Últimos gastos / corregir | "mis últimos gastos", "borra el último gasto" |
| Señales de trading | "señal de btc", "qué dice la estrategia macd en sol", "señal de oro con datos de prueba" |
| Generales | "ayuda", "¿qué hora es?", "¿qué día es hoy?", "adiós" |

**Gastos:** se guardan en `datos_jarvis/gastos.xlsx` (puedes abrirlo con Excel)
y se clasifican solos por palabras clave (Comida, Transporte, Hogar,
Servicios, Salud, Ocio, Compras, Educación, Finanzas, Otros). Las palabras
clave están en `CATEGORIAS` dentro de `jarvis/expenses.py`.

**Reporte de fin de mes:** al arrancar el primer día de un mes nuevo,
Jarvis crea solo `datos_jarvis/reportes/reporte_AAAA-MM.xlsx` del mes que
terminó, con una hoja de resumen y gráfico de torta por categoría, una de
gasto diario con gráfico de barras y una con el detalle. Si quieres que se
genere aunque no abras Jarvis, prográmalo el día 1 de cada mes:

```bash
# cron (Linux/macOS): día 1 a las 8:00
0 8 1 * * cd /ruta/Fermin-bot- && python -m jarvis -c "reporte del mes pasado"
```

**Voz:** `pip install SpeechRecognition pyttsx3 pyaudio`. El reconocimiento
de voz usa Google (requiere internet) y la respuesta hablada funciona offline.

## Cómo agregar un comando nuevo

1. Copia `jarvis/commands/_plantilla.py` a `jarvis/commands/mi_comando.py`.
   Cualquier archivo de esa carpeta se carga solo; los que empiezan por `_`
   se ignoran.
2. Define la función con `@command`:

```python
from jarvis.core import command

@command("recordatorio", r"^recuerdame (.+)$",
         help="Guarda un recordatorio.", examples=["recuérdame pagar la luz"])
def recordatorio(ctx, match, texto):
    (ctx.data_dir / "recordatorios.txt").open("a").write(match.group(1) + "\n")
    return f"Listo, te recordaré: {match.group(1)}"
```

Los patrones se comparan con el texto **en minúsculas y sin tildes** (escribe
"recuerdame", no "recuérdame"), y la palabra "Jarvis" al inicio se quita
sola. Si necesitas algo al arrancar (como el reporte automático), usa el
decorador `@on_startup`.

```
jarvis/
  core.py           # registro de comandos, normalización y despacho
  expenses.py       # Excel de gastos, categorías y reportes
  brain.py          # conexión con Claude (herramientas e historial)
  voice.py          # micrófono y voz (opcional)
  __main__.py       # interfaz de texto/voz
  commands/
    general.py      # ayuda, hora, fecha, saludo, salir
    gastos.py       # gastos y reportes
    trading.py      # señales de las 5 estrategias
    _plantilla.py   # plantilla para comandos nuevos
```
