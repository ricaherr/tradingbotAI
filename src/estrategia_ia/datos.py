# datos.py

import MetaTrader5 as mt5
import pandas as pd

def obtener_datos(simbolo, timeframe, num_velas):
    """
    Obtiene los datos del mercado para un símbolo.
    Asume que la conexión con MT5 ya está inicializada.
    """
    try:
        # Obtener los datos del par
        rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, num_velas)
        
        if rates is None:
            print(f"Error: No se pudieron obtener datos para {simbolo}")
            return None
            
        return rates
    except Exception as e:
        print(f"Error al obtener datos para {simbolo}: {e}")
        return None