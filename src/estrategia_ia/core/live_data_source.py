# live_data_source.py
import MetaTrader5 as mt5
import pandas as pd
import time
import pytz
from datetime import datetime

class LiveDataSource:
    """
    Fuente de datos para operaciones en vivo con MetaTrader 5.
    """
    def __init__(self, simbolo, timeframe, num_velas_historicas=200, verbose=False):
        self.simbolo = simbolo
        self.timeframe = timeframe
        self.num_velas_historicas = num_velas_historicas
        self.verbose = verbose
        self.last_candle_time = None
        self.timezone = pytz.timezone("Etc/UTC")

    def has_next(self):
        """
        En modo live, siempre hay una siguiente vela (potencialmente).
        El bucle se controla externamente.
        """
        return True

    def get_next_candle_with_history(self):
        """
        Obtiene la vela más reciente y un historial de velas anteriores.
        Espera a que haya una nueva vela para continuar.
        """
        while True:
            rates = mt5.copy_rates_from_pos(self.simbolo, self.timeframe, 0, self.num_velas_historicas)
            if rates is None or len(rates) == 0:
                
                time.sleep(1)
                continue

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            current_candle_time = df.index[-1]

            if self.last_candle_time is None:
                self.last_candle_time = current_candle_time
                # En la primera ejecución, no esperamos, simplemente devolvemos los datos actuales
                return df.iloc[-1], df

            if current_candle_time > self.last_candle_time:
                self.last_candle_time = current_candle_time
                
                return df.iloc[-1], df
            
            # Esperar antes de volver a consultar para no sobrecargar la CPU
            time.sleep(1)