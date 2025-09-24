# order_calculations.py
import MetaTrader5 as mt5
from estrategia_ia import config
from estrategia_ia.utils.logger import strategy_logger

def calcular_riesgo_dinamico(df, senal):
    """
    Calcula el Stop Loss y Take Profit basados en el ATR y una relación Riesgo/Beneficio.
    """
    ultima_vela = df.iloc[-1]
    if 'ATR' not in df.columns:
        strategy_logger.warning("ATR no está en el DataFrame. Usando valores por defecto.")
        atr_value = 0.00020 # Valor por defecto
    else:
        atr_value = ultima_vela['ATR']

    precio_entrada = ultima_vela['close']
    stop_loss = None
    take_profit = None
    
    if senal == "compra":
        stop_loss = ultima_vela['low'] - atr_value
        distancia_sl = precio_entrada - stop_loss
        take_profit = precio_entrada + (distancia_sl * config.RELACION_RIESGO_BENEFICIO)
    elif senal == "venta":
        stop_loss = ultima_vela['high'] + atr_value
        distancia_sl = stop_loss - precio_entrada
        take_profit = precio_entrada - (distancia_sl * config.RELACION_RIESGO_BENEFICIO)
    else:
        logging.warning(f"Señal no reconocida: {senal}")
        return None, None
        
    return stop_loss, take_profit

def calcular_lote(capital, riesgo_porcentaje, stop_loss, precio_actual, info_simbolo):
    """
    Calcula el lote dinámicamente basado en el riesgo, SL y precio de entrada.
    Ahora es independiente de MT5, recibiendo el precio_actual como argumento.
    """
    
    if stop_loss is None or stop_loss == 0.0 or stop_loss == precio_actual:
        logging.warning(f"Stop Loss inválido. No se puede calcular el lote. Usando lote mínimo: {config.MIN_LOTE}")
        return config.MIN_LOTE

    tamaño_pip = info_simbolo.point
    distancia_pips = abs(precio_actual - stop_loss) / tamaño_pip

    if distancia_pips <= 0:
        logging.warning(f"Distancia de stop loss es cero o negativa. No se puede calcular el lote. Usando lote mínimo: {config.MIN_LOTE}")
        return config.MIN_LOTE

    riesgo_dinero = capital * (riesgo_porcentaje / 100)

    # Usar el valor del tick del broker para un cálculo más preciso
    valor_tick = info_simbolo.trade_tick_value
    if valor_tick <= 0:
        logging.error(f"Valor de tick inválido. No se puede calcular el lote.")
        return config.MIN_LOTE

    riesgo_por_lote = distancia_pips * valor_tick
    if riesgo_por_lote <= 0:
        logging.error(f"Riesgo por lote es cero o negativo. No se puede calcular el lote.")
        return config.MIN_LOTE

    lote = riesgo_dinero / riesgo_por_lote
    
    # Redondear al paso de volumen del broker
    lote = round(lote / info_simbolo.volume_step) * info_simbolo.volume_step
    lote = round(lote, 2) # Redondeo final
    
    lote_final = max(info_simbolo.volume_min, min(lote, info_simbolo.volume_max, config.MAX_LOTE))
    
    logging.info(f"Lote calculado: {lote_final}")
    return lote_final