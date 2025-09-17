import MetaTrader5 as mt5

# Establece la conexión con la plataforma de trading MT5
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# Obtén los datos de un símbolo
symbol = "EURUSD"
if not mt5.symbol_select(symbol, True):
    print(symbol, "not found. Failed to get symbol.")
    mt5.shutdown()
    quit()

# Obtén los 10 últimos precios del EURUSD
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
print(f"Número de precios obtenidos: {len(rates)}")
print("Últimos 10 precios:")
for rate in rates:
    print(rate)

# Cierra la conexión
mt5.shutdown()