import pandas as pd
import numpy as np

def calcular_ema(df, columna, periodo):
    """Calcula la Media Móvil Exponencial (EMA)."""
    return df[columna].ewm(span=periodo, adjust=False).mean()

def calcular_atr(df, periodo):
    """Calcula el Average True Range (ATR)."""
    df_atr = df.copy()
    df_atr['high-low'] = df_atr['high'] - df_atr['low']
    df_atr['high-prev_close'] = abs(df_atr['high'] - df_atr['close'].shift(1))
    df_atr['low-prev_close'] = abs(df_atr['low'] - df_atr['close'].shift(1))
    
    df_atr['true_range'] = df_atr[['high-low', 'high-prev_close', 'low-prev_close']].max(axis=1)
    
    # El ATR es la EMA del True Range
    df_atr['ATR'] = df_atr['true_range'].ewm(span=periodo, adjust=False).mean()
    
    return df_atr['ATR']

def es_vela_elefante(df, atr_columna, multi=2.0):
    """
    Identifica velas elefante basado en el ATR.
    """
    cuerpo = abs(df['close'] - df['open'])
    return cuerpo > (df[atr_columna] * multi)

def calcular_indicadores(df, ema_periods=None, atr_period=14, multi_vela_elefante=2.0):
    """
    Calcula una serie de indicadores técnicos para un DataFrame de datos de mercado.

    Args:
        df (pd.DataFrame): DataFrame con columnas 'open', 'high', 'low', 'close'.
        ema_periods (list, optional): Una lista de períodos para calcular las EMAs. 
                                      Defaults to [9, 20, 200].
        atr_period (int, optional): El período para el cálculo del ATR. Defaults to 14.
        multi_vela_elefante (float, optional): Multiplicador del ATR para definir una vela elefante. 
                                               Defaults to 2.0.

    Returns:
        pd.DataFrame: El DataFrame original con las columnas de los indicadores añadidas.
    """
    if ema_periods is None:
        ema_periods = [9, 20, 200]

    df_indicadores = df.copy()

    # Calcular EMAs dinámicamente
    for periodo in ema_periods:
        df_indicadores[f'EMA_{periodo}'] = calcular_ema(df_indicadores, 'close', periodo)
    
    # Calcular ATR
    df_indicadores['ATR'] = calcular_atr(df_indicadores, periodo=atr_period)
    
    # Identificar velas elefante
    df_indicadores['es_vela_elefante'] = es_vela_elefante(df_indicadores, 'ATR', multi=multi_vela_elefante)
    
    return df_indicadores
