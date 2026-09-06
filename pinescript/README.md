# Pine Script (TradingView) — 5 estrategias con gestión de riesgo

Versión en Pine Script v5 de las 5 estrategias de `strategies/`, lista para
usar en el **Pine Editor de TradingView** como `strategy()`. Incluyen:

- Backtest con el **Strategy Tester** (datos históricos reales de TradingView,
  sin necesidad de exportar nada).
- **Comisión (0.04%) y slippage (1 tick)** ya incluidos en el backtest, para
  que el % de rentabilidad que veas sea realista y no optimista.
- **Stop-loss y take-profit dinámicos basados en ATR** (se adaptan a la
  volatilidad de cada símbolo, en vez de un número fijo de puntos).
- **Filtro de tendencia de timeframe superior** (1h por defecto): solo entra
  a favor de la tendencia mayor, para reducir señales falsas del 5m.
- Marcadores BUY/SELL en el gráfico y `alertcondition()` para alertas.

| Archivo | Estrategia | Indicadores |
|---|---|---|
| [`1_ema_cross.pine`](1_ema_cross.pine) | Cruce de EMAs (9/21) | EMA(9), EMA(21) |
| [`2_rsi_sma.pine`](2_rsi_sma.pine) | RSI + SMA | RSI(14), SMA(50) |
| [`3_bollinger_rsi.pine`](3_bollinger_rsi.pine) | Bollinger + RSI | Bandas de Bollinger(20,2), RSI(14) |
| [`4_macd_cross.pine`](4_macd_cross.pine) | Cruce de MACD | MACD(12,26,9) |
| [`5_stochastic_ema.pine`](5_stochastic_ema.pine) | Estocástico + EMA | %K/%D(14,3), EMA(50) |

## Cómo usarlas

1. Abre [TradingView](https://www.tradingview.com/) y carga el gráfico del
   futuro deseado (p. ej. `BINANCE:BTCUSDT.P`, `XRPUSDT.P`, `SOLUSDT.P`,
   `XAUTUSDT.P`/`PAXGUSDT` o el equivalente en tu bróker/exchange).
2. **Pon el timeframe del gráfico en 5 minutos.**
3. Abre el **Pine Editor**, pega el contenido del `.pine` que quieras usar y
   pulsa "Add to chart".
4. Abre el **Strategy Tester** (pestaña inferior del gráfico) → pestaña
   "Overview" para ver Net Profit %, Max Drawdown, Profit Factor, y "List of
   Trades" / "Performance Summary" para el detalle operación por operación.
   Esto ya usa el historial real del símbolo — no necesitas exportar ni
   subir nada.
5. Ajusta los inputs desde el ⚙️ del indicador:
   - **Gestión de riesgo**: multiplicador de ATR para stop-loss/take-profit.
   - **Filtro de tendencia**: activar/desactivar y elegir el timeframe superior.
   - **Indicador**: los periodos propios de cada estrategia.
6. Para alertas: clic derecho → "Add alert" sobre la estrategia y elige la
   condición `BUY`/`SELL`.

## Nota sobre la estrategia 3 (Bollinger + RSI)

Es una estrategia de **reversión a la media** (compra caídas, vende subidas),
mientras que el filtro de tendencia superior está pensado para estrategias
de **seguimiento de tendencia**. Si notas muy pocas operaciones con el
filtro activado, prueba desactivándolo (`useHtfFilter = false`) en esta
estrategia en particular — la exigencia de "precio > tendencia superior"
puede chocar con la lógica de comprar justo cuando el precio cae.

## Sobre la rentabilidad

Añadir stop-loss/take-profit y un filtro de tendencia normalmente evita las
pérdidas más grandes, pero **no convierte una estrategia sin ventaja
estadística real en rentable**. Antes de operar en real:

- Revisa el **número de operaciones**: con pocas operaciones (< 30-50) el
  resultado del backtest no es estadísticamente confiable.
- Revisa el **Profit Factor** (> 1.5 es razonable) y el **Max Drawdown**
  (cuánto podrías perder en la peor racha).
- Prueba distintos periodos de fechas en el Strategy Tester — una
  estrategia que solo funciona en un tramo concreto probablemente está
  sobreajustada a ese tramo.

> ⚠️ Son plantillas educativas/técnicas. Ninguna estrategia garantiza
> rentabilidad. Antes de operar en real, valida con suficientes datos y
> nunca arriesgues más de lo que puedes permitirte perder, especialmente
> tratándose de futuros apalancados.
