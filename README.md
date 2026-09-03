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
tests/                          # pruebas unitarias con pytest
```

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
