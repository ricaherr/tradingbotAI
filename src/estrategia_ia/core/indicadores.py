import pandas as pd
import numpy as np
import warnings

# Suprimir warnings de pandas SettingWithCopyWarning que generan ruido
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

def calcular_ema(df, columna, periodo):
    """Calcula la Media Móvil Exponencial (EMA) optimizada."""
    values = df[columna].values
    alpha = 2.0 / (periodo + 1.0)
    ema = np.empty_like(values, dtype=np.float64)
    ema[0] = values[0]
    
    for i in range(1, len(values)):
        ema[i] = alpha * values[i] + (1 - alpha) * ema[i-1]
    
    return pd.Series(ema, index=df.index)

def calcular_atr(df, periodo):
    """Calcula el Average True Range (ATR) optimizado."""
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    
    # Primer valor no tiene close anterior
    tr2[0] = tr1[0]
    tr3[0] = tr1[0]
    
    true_range = np.maximum(tr1, np.maximum(tr2, tr3))
    
    # EMA del true range
    alpha = 2.0 / (periodo + 1.0)
    atr = np.empty_like(true_range)
    atr[0] = true_range[0]
    
    for i in range(1, len(true_range)):
        atr[i] = alpha * true_range[i] + (1 - alpha) * atr[i-1]
    
    return pd.Series(atr, index=df.index)

def es_vela_elefante(df, atr_columna, multi=2.0):
    """
    Identifica velas elefante basado en el ATR optimizado.
    """
    cuerpo = np.abs(df['close'].values - df['open'].values)
    atr_threshold = df[atr_columna].values * multi
    return pd.Series(cuerpo > atr_threshold, index=df.index)

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

    # Calcular EMAs dinámicamente usando .loc para evitar warnings
    for periodo in ema_periods:
        df.loc[:, f'EMA_{periodo}'] = calcular_ema(df, 'close', periodo)
    
    # Calcular ATR
    df.loc[:, 'ATR'] = calcular_atr(df, periodo=atr_period)
    
    # Identificar velas elefante
    df.loc[:, 'es_vela_elefante'] = es_vela_elefante(df, 'ATR', multi=multi_vela_elefante)
    
    return df
