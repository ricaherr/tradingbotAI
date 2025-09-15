import pandas as pd
import numpy as np

def calcular_ema(df, columna, periodo):
    """Calcula la Media Móvil Exponencial (EMA) de forma manual."""
    return df[columna].ewm(span=periodo, adjust=False).mean()

def calcular_atr(df, periodo):
    """Calcula el Average True Range (ATR) de forma manual."""
    df['high-low'] = df['high'] - df['low']
    df['high-prev_close'] = abs(df['high'] - df['close'].shift(1))
    df['low-prev_close'] = abs(df['low'] - df['close'].shift(1))
    
    df['true_range'] = df[['high-low', 'high-prev_close', 'low-prev_close']].max(axis=1)
    
    # El ATR es la EMA del True Range
    df['ATR'] = df['true_range'].ewm(span=periodo, adjust=False).mean()
    
    # Limpiar columnas temporales
    df.drop(columns=['high-low', 'high-prev_close', 'low-prev_close', 'true_range'], inplace=True)
    return df

def es_vela_elefante(df, multi=2.0):
    """
    Identifica velas elefante. Se define por un cuerpo que es al menos 'multi' veces
    el tamaño promedio del cuerpo (medido por ATR).
    """
    if 'ATR' not in df.columns or df.empty:
        df['es_vela_elefante'] = False
        return df

    df['cuerpo'] = abs(df['close'] - df['open'])
    criterio = df['cuerpo'] > (df['ATR'] * multi)
    df['es_vela_elefante'] = criterio
    return df

def calcular_indicadores(datos, atr_period=14, multi_vela_elefante=2.0):
    df = pd.DataFrame(datos)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    # Calcular las EMAs de forma manual
    df['EMA_9'] = calcular_ema(df, 'close', 9)
    df['EMA_20'] = calcular_ema(df, 'close', 20)
    df['EMA_200'] = calcular_ema(df, 'close', 200)
    
    # Calcular el ATR de forma manual
    df = calcular_atr(df, periodo=atr_period)
    
    # Calcular si es una vela elefante
    df = es_vela_elefante(df, multi=multi_vela_elefante)
    
    return df