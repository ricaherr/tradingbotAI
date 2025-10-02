# strategies.py

from ..utils.risk_calculator import RiskCalculator
from ..config import TIMEFRAMES_CONFIG
import pandas as pd
from typing import Dict, Tuple, Optional

# Instancia global del calculador de riesgo
risk_calculator = RiskCalculator()

def determinar_senales(df, estrategia, timeframe: str = "M15"):
    """
    Identifica señales de compra/venta con gestión dinámica de riesgo.
    VERSIÓN MEJORADA - Integra RiskCalculator para SL/TP adaptativos.
    """
    if len(df) < 2:
        return None, "Datos insuficientes (menos de 2 velas)"

    ultima_vela = df.iloc[-1]
    penultima_vela = df.iloc[-2]
    nombre_estrategia = estrategia.get("nombre")

    # Lógica para la estrategia 'Cruce EMA + Vela Elefante'
    if nombre_estrategia == "Cruce EMA + Vela Elefante":
        # CORRECTO: Leer parámetros desde el diccionario principal de la estrategia
        ema_corta_periodo = estrategia.get("ema_corta", 9)
        ema_larga_periodo = estrategia.get("ema_larga", 20)

        col_ema_corta = f'EMA_{ema_corta_periodo}'
        col_ema_larga = f'EMA_{ema_larga_periodo}'

        if not all(k in df.columns for k in [col_ema_corta, col_ema_larga, 'es_vela_elefante']):
            return None, f"Faltan columnas de indicadores ({col_ema_corta}, {col_ema_larga}, es_vela_elefante)"

        cruce_alcista = df[col_ema_corta].iloc[-2] < df[col_ema_larga].iloc[-2] and df[col_ema_corta].iloc[-1] > df[col_ema_larga].iloc[-1]
        cruce_bajista = df[col_ema_corta].iloc[-2] > df[col_ema_larga].iloc[-2] and df[col_ema_corta].iloc[-1] < df[col_ema_larga].iloc[-1]
        es_elefante = ultima_vela['es_vela_elefante']
        
        # Lógica de la estrategia con gestión de riesgo
        if cruce_alcista and es_elefante:
            signal_data = calcular_parametros_operacion(
                df, estrategia, "compra", timeframe,
                f"Cruce alcista de EMAs ({ema_corta_periodo}/{ema_larga_periodo}) con vela elefante"
            )
            return "compra", signal_data
        elif cruce_bajista and es_elefante:
            signal_data = calcular_parametros_operacion(
                df, estrategia, "venta", timeframe,
                f"Cruce bajista de EMAs ({ema_corta_periodo}/{ema_larga_periodo}) con vela elefante"
            )
            return "venta", signal_data
        else:
            razon = f"No hubo cruce o no fue vela elefante. Elefante: {es_elefante}"
            return None, razon

    # Estrategia simplificada para "Rompimiento de la EMA 20"
    if nombre_estrategia == "Rompimiento de la EMA 20":
        # Usar EMA_20 si existe, sino calcular sobre la marcha
        if 'EMA_20' in df.columns:
            ema_20_actual = ultima_vela['EMA_20']
            ema_20_anterior = penultima_vela['EMA_20']
        else:
            # Calcular EMA simple si no existe
            ema_20_actual = df['close'].tail(20).mean()
            ema_20_anterior = df['close'].tail(21).iloc[:-1].mean()
        
        precio_actual = ultima_vela['close']
        precio_anterior = penultima_vela['close']
        
        # Rompimiento alcista: precio cruza por encima de EMA
        if precio_anterior <= ema_20_anterior and precio_actual > ema_20_actual:
            signal_data = calcular_parametros_operacion(
                df, estrategia, "compra", timeframe, "Rompimiento alcista de EMA_20"
            )
            return "compra", signal_data
        
        # Rompimiento bajista: precio cruza por debajo de EMA  
        if precio_anterior >= ema_20_anterior and precio_actual < ema_20_actual:
            signal_data = calcular_parametros_operacion(
                df, estrategia, "venta", timeframe, "Rompimiento bajista de EMA_20"
            )
            return "venta", signal_data
        
        return None, "No hay rompimiento de EMA_20"
    
    # Estrategia corregida para "Reversión a la Media"
    elif nombre_estrategia == "Reversión a la Media":
        ema_reversion_periodo = estrategia.get("ema_reversion", 20)
        col_ema_reversion = f'EMA_{ema_reversion_periodo}'
        
        # Verificar si existe la columna, sino usar EMA_20 por defecto
        if col_ema_reversion not in df.columns:
            if 'EMA_20' in df.columns:
                col_ema_reversion = 'EMA_20'
            else:
                # Calcular EMA simple
                ema_actual = df['close'].tail(ema_reversion_periodo).mean()
                ema_anterior = df['close'].tail(ema_reversion_periodo + 1).iloc[:-1].mean()
                precio_actual = ultima_vela['close']
                precio_anterior = penultima_vela['close']
                
                # Cruce alcista
                if precio_anterior < ema_anterior and precio_actual > ema_actual:
                    signal_data = calcular_parametros_operacion(
                        df, estrategia, "compra", timeframe, f"Reversión alcista a EMA_{ema_reversion_periodo}"
                    )
                    return "compra", signal_data
                
                # Cruce bajista  
                if precio_anterior > ema_anterior and precio_actual < ema_actual:
                    signal_data = calcular_parametros_operacion(
                        df, estrategia, "venta", timeframe, f"Reversión bajista a EMA_{ema_reversion_periodo}"
                    )
                    return "venta", signal_data
                
                return None, "No hay cruce de EMA"
        
        # Usar columna existente
        ema_actual = ultima_vela[col_ema_reversion]
        ema_anterior = penultima_vela[col_ema_reversion]
        precio_actual = ultima_vela['close']
        precio_anterior = penultima_vela['close']
        
        # Filtro de tendencia opcional (simplificado)
        usar_filtro = estrategia.get("usar_filtro_tendencia", False)
        if usar_filtro:
            ema_tendencia_periodo = estrategia.get("ema_tendencia", 200)
            col_ema_tendencia = f'EMA_{ema_tendencia_periodo}'
            
            if col_ema_tendencia in df.columns:
                ema_tendencia = ultima_vela[col_ema_tendencia]
                
                # Solo operar en dirección de la tendencia
                if precio_actual > ema_tendencia:  # Tendencia alcista
                    if precio_anterior < ema_anterior and precio_actual > ema_actual:
                        signal_data = calcular_parametros_operacion(
                            df, estrategia, "compra", timeframe, 
                            f"Reversión alcista a {col_ema_reversion} (tendencia alcista)"
                        )
                        return "compra", signal_data
                elif precio_actual < ema_tendencia:  # Tendencia bajista
                    if precio_anterior > ema_anterior and precio_actual < ema_actual:
                        signal_data = calcular_parametros_operacion(
                            df, estrategia, "venta", timeframe,
                            f"Reversión bajista a {col_ema_reversion} (tendencia bajista)"
                        )
                        return "venta", signal_data
                
                return None, "Cruce contra tendencia - señal filtrada"
        
        # Sin filtro de tendencia
        if precio_anterior < ema_anterior and precio_actual > ema_actual:
            signal_data = calcular_parametros_operacion(
                df, estrategia, "compra", timeframe, f"Reversión alcista a {col_ema_reversion}"
            )
            return "compra", signal_data
        
        if precio_anterior > ema_anterior and precio_actual < ema_actual:
            signal_data = calcular_parametros_operacion(
                df, estrategia, "venta", timeframe, f"Reversión bajista a {col_ema_reversion}"
            )
            return "venta", signal_data
        
        return None, "No hay cruce de EMA"

    return None, "Estrategia no reconocida"


def calcular_parametros_operacion(df: pd.DataFrame, 
                                 estrategia: Dict, 
                                 direccion: str, 
                                 timeframe: str,
                                 razon: str) -> Dict:
    """Calcula parámetros dinámicos de la operación usando RiskCalculator"""
    
    ultima_vela = df.iloc[-1]
    precio_actual = ultima_vela['close']
    
    # Calcular ATR
    atr_period = estrategia.get('atr_period', estrategia.get('ATR_PERIOD', 14))
    atr_series = risk_calculator.calcular_atr(df, atr_period)
    atr_actual = atr_series.iloc[-1] if not atr_series.empty else 0.001
    
    # Parámetros de riesgo de la estrategia
    riesgo_porcentaje = estrategia.get('riesgo_porcentaje', 1.0)
    relacion_rr = estrategia.get('relacion_riesgo_beneficio', 2.0)
    
    # Calcular lote dinámico
    lote = risk_calculator.calcular_lote_dinamico(
        timeframe=timeframe,
        riesgo_porcentaje=riesgo_porcentaje,
        atr_value=atr_actual,
        precio_actual=precio_actual
    )
    
    # Calcular SL y TP adaptativos
    stop_loss, take_profit = risk_calculator.calcular_sl_tp_adaptativos(
        timeframe=timeframe,
        atr_value=atr_actual,
        precio_entrada=precio_actual,
        direccion=direccion,
        relacion_rr=relacion_rr
    )
    
    # Validar riesgo de la operación
    distancia_sl = abs(precio_actual - stop_loss)
    validacion = risk_calculator.validar_riesgo_operacion(
        timeframe=timeframe,
        lote=lote,
        distancia_sl=distancia_sl,
        precio_actual=precio_actual
    )
    
    return {
        "razon": razon,
        "precio_entrada": precio_actual,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "lote": lote,
        "atr": atr_actual,
        "timeframe": timeframe,
        "riesgo_porcentual": validacion.get('riesgo_porcentual', 0),
        "validacion": validacion,
        "parametros_estrategia": {
            "riesgo_base": riesgo_porcentaje,
            "relacion_rr": relacion_rr,
            "atr_period": atr_period
        }
    }


def validar_senal_con_riesgo(signal_data: Dict) -> Tuple[bool, str]:
    """Valida si la señal cumple criterios de riesgo"""
    
    if not signal_data or not isinstance(signal_data, dict):
        return False, "Datos de señal inválidos"
    
    validacion = signal_data.get('validacion', {})
    
    if not validacion.get('valido', False):
        return False, validacion.get('razon', 'Validación de riesgo falló')
    
    # Verificar límites adicionales
    riesgo_porcentual = validacion.get('riesgo_porcentual', 0)
    if riesgo_porcentual > 3.0:  # Límite global de seguridad
        return False, f"Riesgo {riesgo_porcentual:.2f}% excede límite global 3.0%"
    
    return True, "Señal validada correctamente"