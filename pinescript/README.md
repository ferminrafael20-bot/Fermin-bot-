# Pine Script (TradingView) — mismas 5 estrategias

Versión en Pine Script v5 de las 5 estrategias de `strategies/`, lista para
usar en el **Pine Editor de TradingView** como `strategy()` (incluye
backtest con el Strategy Tester, marcadores de compra/venta en el gráfico y
`alertcondition()` para crear alertas).

| Archivo | Estrategia | Indicadores |
|---|---|---|
| [`1_ema_cross.pine`](1_ema_cross.pine) | Cruce de EMAs (9/21) | EMA(9), EMA(21) |
| [`2_rsi_sma.pine`](2_rsi_sma.pine) | RSI + SMA | RSI(14), SMA(50) |
| [`3_bollinger_rsi.pine`](3_bollinger_rsi.pine) | Bollinger + RSI | Bandas de Bollinger(20,2), RSI(14) |
| [`4_macd_cross.pine`](4_macd_cross.pine) | Cruce de MACD | MACD(12,26,9) |
| [`5_stochastic_ema.pine`](5_stochastic_ema.pine) | Estocástico + EMA | %K/%D(14,3), EMA(50) |

La lógica de compra/venta es idéntica a la versión Python en `strategies/`
(mismos periodos y niveles por defecto).

## Cómo usarlas

1. Abre [TradingView](https://www.tradingview.com/) y carga el gráfico del
   futuro deseado (p. ej. `BINANCE:BTCUSDT.P`, `XRPUSDT.P`, `SOLUSDT.P`,
   `XAUTUSDT.P` o el equivalente en tu bróker/exchange).
2. **Pon el timeframe del gráfico en 5 minutos** (las estrategias no fijan
   el timeframe internamente; heredan el del gráfico).
3. Abre el **Pine Editor**, pega el contenido del `.pine` que quieras usar y
   pulsa "Add to chart".
4. Revisa los resultados en el **Strategy Tester** (pestaña inferior) y
   ajusta los inputs (periodos, niveles de sobrecompra/sobreventa,
   permitir long/short) desde el panel de configuración del indicador.
5. Para recibir notificaciones, crea una alerta sobre la estrategia y
   selecciona la condición `BUY`/`SELL` (o "Order fills" para las entradas
   reales del backtest).

> ⚠️ Igual que la versión Python: son plantillas educativas/técnicas, sin
> gestión de riesgo (stop-loss/take-profit) incorporada por defecto.
> Añade tu propia gestión de riesgo antes de operar en real, especialmente
> tratándose de futuros apalancados.
