# data_source.py
import pandas as pd
from estrategia_ia.utils.error_handler import safe_execute
from estrategia_ia.utils.logger import data_logger

class HistoricalDataSource:
    """
    Proporciona datos históricos desde un archivo CSV, vela por vela.
    """
    def __init__(self, file_path, backtest_period_years=None, verbose=False):
        self.verbose = verbose
        def load_data():
            df = pd.read_csv(file_path, index_col='time', parse_dates=['time'])
            if df.empty:
                raise ValueError("Archivo CSV está vacío")
            return df
        
        df = safe_execute(load_data, default_return=pd.DataFrame(), log_errors=True)
        
        if df.empty:
            if self.verbose: print(f"Error: No se pudieron cargar datos de '{file_path}'")
            self.df_data = pd.DataFrame()
        else:
            if backtest_period_years and backtest_period_years > 0:
                end_date = df.index.max()
                days_back = int(backtest_period_years * 365)
                start_date = end_date - pd.Timedelta(days=days_back)
                self.df_data = df[df.index >= start_date].copy()
                if self.verbose:
                    print(f"Datos históricos limitados a los últimos {backtest_period_years} año(s) ({days_back} días).")
            else:
                self.df_data = df.copy()
            
            if self.verbose and not self.df_data.empty:
                 print(f"Datos cargados desde {self.df_data.index.min():%Y-%m-%d} hasta {self.df_data.index.max():%Y-%m-%d}. Total: {len(self.df_data)} velas.")
        
        self.current_index = -1

    def has_next(self):
        """Verifica si hay más velas para procesar."""
        return self.current_index < len(self.df_data) - 1

    def get_next_candle_with_history(self):
        """
        Avanza al siguiente paso de tiempo y devuelve la vela actual y el historial disponible.
        """
        if not self.has_next():
            return None, None

        self.current_index += 1
        
        # La ventana de historial incluye la vela actual
        historial_disponible = self.df_data.iloc[0 : self.current_index + 1]
        vela_actual = self.df_data.iloc[self.current_index]
        
        return vela_actual, historial_disponible
