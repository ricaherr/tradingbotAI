# datos.py

import MetaTrader5 as mt5
import pandas as pd

def obtener_datos(simbolo, timeframe, num_velas):
    """
    Obtiene los datos del mercado para un símbolo.
    Asume que la conexión con MT5 ya está inicializada.
    """
    # Obtener los datos del par
    rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, num_velas)
    
    # Nota: No se llama a mt5.initialize() ni a mt5.shutdown() aquí.
    
    return rates