import os
import MetaTrader5 as mt5
import pandas as pd
import time
import logging
import csv
from datetime import datetime
from notificaciones import enviar_notificacion
from gestor_riesgo_en_operacion import GestorRiesgoEnOperacion
from gestion_riesgo import GestionRiesgo
from registro_operaciones import registrar_operacion_abierta, monitorear_y_registrar_operaciones_cerradas, ordenes_en_curso
from indicadores import calcular_indicadores, es_vela_elefante
import pytz

# --- IMPORTAR CONFIGURACIÓN ---
import config

# --- CONFIGURACIÓN DEL REGISTRO ---
logging.basicConfig(
    filename=config.LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

# Crear el archivo de operaciones si no existe
if not os.path.isfile(config.OPERACIONES_CSV):
    columnas = [
        'ticket_mt5', 'simbolo', 'estrategia', 'fecha_apertura', 'fecha_cierre', 'tipo', 'precio_apertura',
        'precio_cierre', 'resultado_dinero', 'resultado_pips', 'stop_loss', 'take_profit', 'lote', 'comentario'
    ]
    with open(config.OPERACIONES_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()

# --- FUNCIONES AUXILIARES ---
def conectar_mt5():
    """
    Intenta establecer la conexión inicial con MetaTrader 5.
    """
    if not mt5.initialize():
        logging.error("Fallo al inicializar MetaTrader 5, error code: %s", mt5.last_error())
        return False
    return True

def desconectar_mt5():
    """Desconecta de MetaTrader 5."""
    mt5.shutdown()
    print("✅ Desconexión de MetaTrader 5.")

def obtener_datos(simbolo, timeframe, num_velas):
    """Obtiene los datos históricos del par y el timeframe especificados."""
    timezone = pytz.timezone("Etc/UTC")
    utc_from = datetime.now(timezone) - pd.Timedelta(f"{num_velas + 10}min")
    
    if not mt5.initialize():
        logging.error("initialize() falló al obtener datos: %s", mt5.last_error())
        return None
        
    rates = mt5.copy_rates_from(simbolo, timeframe, utc_from, num_velas)
    if rates is None or len(rates) == 0:
        logging.warning(f"No se pudieron obtener datos para {simbolo}. Código de error: {mt5.last_error()}")
        return None
    
    return rates

def obtener_informacion_operacion(ticket):
    """Busca en el diccionario global la información de una operación por su ticket."""
    return ordenes_en_curso.get(ticket)

def ejecutar_orden(simbolo, tipo_orden, stop_loss, take_profit, capital, riesgo_porcentaje, nombre_estrategia, gestor_riesgo_global):
    """
    Ejecuta una orden de compra o venta en MetaTrader 5.
    Calcula el tamaño del lote basado en el riesgo, la distancia del SL y el capital.
    Ahora incluye un factor de reducción basado en pérdidas consecutivas y validación de lote.
    """
    if mt5.positions_total() >= config.MAX_OPERACIONES_SIMULTANEAS:
        logging.warning(f"Máximo de operaciones simultáneas ({MAX_OPERACIONES_SIMULTANEAS}) alcanzado. No se puede abrir una nueva orden en {simbolo}.")
        print(f"⚠️ Máximo de operaciones simultáneas alcanzado. Esperando...")
        return
        
    symbol_info = mt5.symbol_info(simbolo)
    if symbol_info is None:
        logging.error(f"No se pudo obtener información del símbolo {simbolo}.")
        return

    tick = mt5.symbol_info_tick(simbolo)
    if tick is None:
        logging.error(f"No se pudo obtener el tick para el símbolo {simbolo}.")
        return

    precio_actual = tick.bid if tipo_orden == mt5.ORDER_TYPE_BUY else tick.ask

    if config.VALIDAR_SPREAD:
        spread = symbol_info.spread * symbol_info.point
        beneficio_potencial_en_dinero = abs(take_profit - precio_actual) / symbol_info.point * mt5.symbol_info_tick(simbolo).bid * 100000
        spread_en_dinero = spread * mt5.symbol_info_tick(simbolo).bid * 100000
        if spread_en_dinero / beneficio_potencial_en_dinero > config.MAX_SPREAD_PORCENTAJE_BENEFICIO:
            print(f"⚠️ Spread demasiado alto en {simbolo}. Operación cancelada.")
            return

    distancia_stop_pips = abs(precio_actual - stop_loss) / symbol_info.point
    
    if distancia_stop_pips == 0:
        logging.error("La distancia del stop loss es 0. No se puede calcular el lote.")
        return
        
    riesgo_dinero = capital * (riesgo_porcentaje / 100)
    valor_pip = symbol_info.trade_tick_value_profit
    
    factor_reduccion = gestor_riesgo_global.factor_posicion(nombre_estrategia)
    
    lote_final = (riesgo_dinero / (distancia_stop_pips * valor_pip)) * factor_reduccion
    
    if lote_final < config.MIN_LOTE:
        print(f"⚠️ Lote calculado ({lote_final:.4f}) es menor que el mínimo permitido ({config.MIN_LOTE:.2f}). Se ajustará al mínimo.")
        lote_final = config.MIN_LOTE

    lote_final = max(symbol_info.volume_min, min(lote_final, symbol_info.volume_max))
    
    lote_final = round(lote_final, 2)
    
    if lote_final < config.MIN_LOTE:
        logging.warning(f"El lote final ({lote_final}) es menor que el lote mínimo. No se ejecutará la orden.")
        return
    
    # --- Código para enviar la orden ---
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": simbolo,
        "volume": lote_final,
        "type": tipo_orden,
        "price": precio_actual,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 20,
        "comment": f"Estrategia: {nombre_estrategia}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    resultado = mt5.order_send(request)

    # NUEVO: Validar si la variable resultado es None
    if resultado is None:
        logging.error("Fallo al enviar la orden. Posiblemente se perdió la conexión con MetaTrader 5.")
        print("❌ Fallo al enviar la orden. ¿Está el terminal MT5 abierto y conectado?")
        return # Salir de la función para evitar el error

    if resultado.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"Orden ejecutada: {simbolo} {tipo_orden} | Lote: {lote_final:.2f} | SL: {stop_loss} | TP: {take_profit}")
        print(f"🚀 Orden ejecutada: {simbolo} | Tipo: {'COMPRA' if tipo_orden == mt5.ORDER_TYPE_BUY else 'VENTA'} | Lote: {lote_final:.2f}")
        
        # Registrar la orden para el seguimiento
        registrar_operacion_abierta(
            ticket=resultado.order,
            simbolo=simbolo,
            estrategia=nombre_estrategia,
            lote=lote_final,
            tipo='compra' if tipo_orden == mt5.ORDER_TYPE_BUY else 'venta',
            precio_apertura=precio_actual,
            sl=stop_loss,
            tp=take_profit
        )

        # Enviar notificación
        mensaje = f"✅ NUEVA OPERACIÓN\nPar: {simbolo}\nTipo: {'COMPRA' if tipo_orden == mt5.ORDER_TYPE_BUY else 'VENTA'}\nLote: {lote_final:.2f}\nEstrategia: {nombre_estrategia}"
        enviar_notificacion(mensaje)
    else:
        logging.error(f"Fallo al ejecutar la orden: {resultado.retcode} | {resultado.comment}")
        print(f"❌ Fallo al ejecutar la orden. Código de error: {resultado.retcode}")
        # Enviar notificación de error
        mensaje_error = f"❌ ERROR en OPERACIÓN\nPar: {simbolo}\nError: {resultado.retcode} - {resultado.comment}"
        enviar_notificacion(mensaje_error)

def calcular_lote(capital, riesgo_porcentaje, stop_loss, simbolo, tipo_orden, info_simbolo):
    """Calcula el lote dinámicamente basado en el riesgo por operación."""
    precio_actual = mt5.symbol_info_tick(simbolo).ask if tipo_orden == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(simbolo).bid
    
    if stop_loss is None or stop_loss == 0.0 or stop_loss == precio_actual:
        logging.warning(f"Stop Loss inválido. No se puede calcular el lote. Usando lote mínimo: {config.MIN_LOTE}")
        return 0.01

    tamaño_pip = info_simbolo.point
    distancia_pips = abs(precio_actual - stop_loss) / tamaño_pip

    if distancia_pips <= 0:
        logging.warning(f"Distancia de stop loss es cero o negativa. No se puede calcular el lote. Usando lote mínimo: {config.MIN_LOTE}")
        return 0.01

    riesgo_dinero = capital * (riesgo_porcentaje / 100)
    valor_pip_lote = 10 # Valor del pip por lote estándar para pares con USD al final (ej. EURUSD)

    # Verificar si el par tiene la moneda de cuenta al principio
    if config.MONEDA_DE_CUENTA in simbolo:
        valor_pip_lote = 1 # Para pares como USDJPY, USDCHF

    lote = riesgo_dinero / (distancia_pips * valor_pip_lote)
    lote = round(lote, 2)
    
    # Validar que el lote no exceda el máximo y esté dentro de los límites
    if lote > config.MAX_LOTE:
        lote = config.MAX_LOTE
    
    if lote < mt5.symbol_info(simbolo).volume_min:
        logging.warning(f"El lote calculado ({lote}) es menor al mínimo. Usando lote mínimo: {mt5.symbol_info(simbolo).volume_min}")
        lote = mt5.symbol_info(simbolo).volume_min
    
    logging.info(f"Lote calculado para {simbolo}: {lote}")
    return lote

def calcular_riesgo_dinamico(df, senal):
    """
    Calcula el Stop Loss y Take Profit basados en el ATR.
    """
    ultima_vela = df.iloc[-1]
    if 'ATR' not in df.columns:
        logging.warning("ATR no está en el DataFrame. Usando valores por defecto.")
        atr_value = 0.00020 # Valor por defecto
    else:
        atr_value = ultima_vela['ATR']
    
    stop_loss = None
    take_profit = None
    
    if senal == "compra":
        stop_loss = ultima_vela['low'] - atr_value
        take_profit = ultima_vela['close'] + (atr_value * 2) # Riesgo/Beneficio 1:2
    elif senal == "venta":
        stop_loss = ultima_vela['high'] + atr_value
        take_profit = ultima_vela['close'] - (atr_value * 2)
        
    return stop_loss, take_profit

def determinar_senales(df, estrategia):
    """
    Identifica las señales de compra o venta basadas en el nombre de la estrategia.
    """
    ultima_vela = df.iloc[-1]
    
    if len(df) < 2:
        return None

    # Lógica para la estrategia 'Cruce EMA + Vela Elefante'
    if estrategia["nombre"] == "Cruce EMA + Vela Elefante":
        if not all(k in df.columns for k in ['EMA_9', 'EMA_20', 'es_vela_elefante']):
            return None

        cruce_alcista = df['EMA_9'].iloc[-2] < df['EMA_20'].iloc[-2] and ultima_vela['EMA_9'] > ultima_vela['EMA_20']
        cruce_bajista = df['EMA_9'].iloc[-2] > df['EMA_20'].iloc[-2] and ultima_vela['EMA_9'] < ultima_vela['EMA_20']
        es_elefante = ultima_vela['es_vela_elefante']
        
        if cruce_alcista and es_elefante:
            return "compra"
        elif cruce_bajista and es_elefante:
            return "venta"

    # Lógica para la estrategia 'Rompimiento de la EMA 20'
    elif estrategia["nombre"] == "Rompimiento de la EMA 20":
        if not all(k in df.columns for k in ['EMA_20', 'es_vela_elefante']):
            return None
        
        es_elefante = ultima_vela['es_vela_elefante']
        
        if es_elefante:
            rompimiento_alcista = ultima_vela['close'] > ultima_vela['EMA_20'] and df['close'].iloc[-2] < df['EMA_20'].iloc[-2]
            if rompimiento_alcista:
                return "compra"

            rompimiento_bajista = ultima_vela['close'] < ultima_vela['EMA_20'] and df['close'].iloc[-2] > df['EMA_20'].iloc[-2]
            if rompimiento_bajista:
                return "venta"
    
    # Lógica para la estrategia 'Reversión a la Media'
    elif estrategia["nombre"] == "Reversión a la Media":
        criterios = estrategia.get("criterios", {})
        if 'EMA_20' not in df.columns:
            return None
        
        precio_sobre_ema200 = True
        precio_bajo_ema200 = True
        if criterios.get("usar_filtro_tendencia_200_ema", False):
            if 'EMA_200' not in df.columns or len(df) < 200:
                print("No hay suficientes datos para la EMA de 200. Desactivando filtro de tendencia.")
            else:
                precio_sobre_ema200 = ultima_vela['close'] > ultima_vela['EMA_200']
                precio_bajo_ema200 = ultima_vela['close'] < ultima_vela['EMA_200']
        
        cruce_alcista = df['close'].iloc[-2] < df['EMA_20'].iloc[-2] and ultima_vela['close'] > ultima_vela['EMA_20']
        if cruce_alcista and precio_sobre_ema200:
            return "compra"

        cruce_bajista = df['close'].iloc[-2] > df['EMA_20'].iloc[-2] and ultima_vela['close'] < ultima_vela['EMA_20']
        if cruce_bajista and precio_bajo_ema200:
            return "venta"

    return None

def verificar_y_reconectar_mt5():
    """
    Verifica si la conexión con MetaTrader 5 está activa.
    Si se ha perdido, intenta reestablecerla.
    """
    if mt5.account_info() is None:
        logging.warning("Conexión con MetaTrader 5 perdida. Intentando reconectar...")
        print("⚠️ Conexión perdida. Intentando reconectar...")
        if not mt5.initialize():
            logging.error("Fallo al re-inicializar la conexión con MetaTrader 5. Saliendo.")
            print("❌ No se pudo reconectar. Verifique su terminal MT5. Cerrando el agente.")
            return False
        else:
            logging.info("Conexión reestablecida con éxito.")
            print("✅ Conexión reestablecida.")
    return True

def main():
    """
    Función principal del agente de trading que se ejecuta en un bucle.
    """
    if not conectar_mt5():
        return
    
    estrategias_activas = [e for e in config.ESTRATEGIAS if e.get("activa", False)]
    if not estrategias_activas:
        logging.warning("No hay estrategias activas. Deteniendo el agente.")
        print("🛑 No hay estrategias activas. Deteniendo el agente.")
        desconectar_mt5()
        return

    # NUEVO: Inicializar la gestión de riesgo global
    gestor_riesgo_global = GestionRiesgo(
        limite_global=config.PERDIDA_MAXIMA_DIARIA,
        modo_porcentaje=True,
        capital_inicial=config.CAPITAL_INICIAL,
        reducir_posicion_activo=config.REDUCIR_POSICION_ACTIVO,
        perdidas_consecutivas_reduccion=config.PERDIDAS_CONSECUTIVAS_REDUCCION,
        factor_reduccion=config.FACTOR_REDUCCION_LOTE
    )
    # Cargar el historial del CSV para saber si los límites de pérdidas se han alcanzado
    gestor_riesgo_global.cargar_desde_csv(config.OPERACIONES_CSV)
    
    gestor_riesgo_op = GestorRiesgoEnOperacion(
        modo_trailing=config.TRAILING_ACTIVO,
        break_even_activo=config.BREAK_EVEN_ACTIVO,
        atr_factor_break_even=config.BREAK_EVEN_ATR_FACTOR,
        atr_factor_trailing=config.TRAILING_ATR_FACTOR,
    )

    logging.info("Agente de trading iniciado. Monitoreando varios pares...")
    
    while True:
        try:
            # Aseguramos que la conexión esté activa al inicio de cada ciclo.
            if not verificar_y_reconectar_mt5():
                time.sleep(60)
                continue

            # --- FASE 1: Monitorear y gestionar operaciones abiertas ---
            if mt5.positions_total() > 0:
                logging.info("Monitoreando operaciones abiertas para trailing stop...")
                print("👀 Monitoreando operaciones abiertas...")
                operaciones_abiertas = mt5.positions_get()
                
                for operacion in operaciones_abiertas:
                    info_operacion = obtener_informacion_operacion(operacion.ticket)
                    if info_operacion is None:
                        logging.warning(f"No se encontró información para el ticket {operacion.ticket}. Omitiendo trailing stop.")
                        continue
                    
                    # Obtener los datos más recientes para el ATR
                    datos_operacion = obtener_datos(operacion.symbol, config.TIMEFRAME, config.NUM_VELAS)
                    if datos_operacion is None:
                        logging.warning(f"No se pudieron obtener datos para el símbolo de la operación {operacion.symbol}.")
                        continue
                    df_operacion = calcular_indicadores(datos_operacion)
                    atr_value = df_operacion.iloc[-1]['ATR']
                    
                    symbol_info = mt5.symbol_info_tick(operacion.symbol)
                    precio_actual = symbol_info.bid if operacion.type == mt5.ORDER_TYPE_BUY else symbol_info.ask
                    
                    # Llamar al gestor para actualizar el stop
                    nuevo_stop = gestor_riesgo_op.actualizar_stop(
                        precio_entrada=operacion.price_open,
                        stop_actual=operacion.sl,
                        precio_actual=precio_actual,
                        tipo='compra' if operacion.type == mt5.ORDER_TYPE_BUY else 'venta',
                        atr_value=atr_value
                    )
                    
                    # Si el stop es diferente, modificar la orden
                    if abs(nuevo_stop - operacion.sl) > 0.00001:
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "symbol": operacion.symbol,
                            "sl": nuevo_stop,
                            "tp": operacion.tp,
                            "position": operacion.ticket,
                            "comment": "Trailing stop actualizado",
                        }
                        
                        resultado_mod = mt5.order_send(request)
                        if resultado_mod.retcode == mt5.TRADE_RETCODE_DONE:
                            logging.info(f"Stop loss actualizado para el ticket {operacion.ticket} de {operacion.sl} a {nuevo_stop}")
                            print(f"✅ Stop Loss actualizado para el ticket {operacion.ticket}")
                            info_operacion['stop_loss'] = nuevo_stop # Actualizar el diccionario local
                        else:
                            logging.error(f"Fallo al actualizar SL para el ticket {operacion.ticket}. Código: {resultado_mod.retcode}")
                            print(f"❌ Fallo al actualizar SL para el ticket {operacion.ticket}. Código: {resultado_mod.retcode}")

            # NUEVO: Monitorear y registrar operaciones cerradas y sus resultados en el gestor de riesgo global
            monitorear_y_registrar_operaciones_cerradas(gestor_riesgo_global)
            
            # --- FASE 2: Buscar nuevas señales ---
            # NUEVO: Verificar si la pérdida máxima diaria ha sido alcanzada
            if not gestor_riesgo_global.puede_operar():
                logging.warning("Límite de pérdida diario alcanzado. Deteniendo la búsqueda de nuevas señales.")
                print("🛑 ¡Límite de pérdida diario alcanzado! Deteniendo la búsqueda de señales por hoy.")
                time.sleep(60)
                continue

            # Bucle para cada estrategia activa
            for estrategia in estrategias_activas:
                nombre_estrategia = estrategia["nombre"]
                pares_a_operar = estrategia.get("pares", config.PARES_A_OPERAR)
                
                # NUEVO: Verificar si la estrategia puede operar
                if not gestor_riesgo_global.puede_operar(nombre_estrategia):
                    logging.warning(f"La estrategia '{nombre_estrategia}' no puede operar (límite alcanzado o cooldown).")
                    print(f"⚠️ La estrategia '{nombre_estrategia}' no puede operar. Omisión.")
                    continue

                # Bucle para cada par de la estrategia
                for par in pares_a_operar:
                    logging.info(f"Analizando '{par}' con la estrategia: '{nombre_estrategia}'")
                    
                    datos = obtener_datos(par, config.TIMEFRAME, config.NUM_VELAS)
                    if datos is None or len(datos) < 2:
                        logging.warning(f"No se pudieron obtener datos suficientes para {par}.")
                        continue
                    
                    df = calcular_indicadores(datos, atr_period=config.ATR_PERIOD, multi_vela_elefante=config.MULTI_VELA_ELEFANTE)

                    # Determinar la señal
                    senal = determinar_senales(df, estrategia)

                    if senal:
                        logging.info(f"¡Señal de {senal.upper()} detectada en {par}!")
                        print(f"✅ ¡Señal de {senal.upper()} en {par} con la estrategia '{nombre_estrategia}'!")
                        
                        # Cálculo de riesgo y ejecución de la orden
                        stop_loss, take_profit = calcular_riesgo_dinamico(df, senal)
                        tipo_orden = mt5.ORDER_TYPE_BUY if senal == "compra" else mt5.ORDER_TYPE_SELL
                        
                        ejecutar_orden(
                            simbolo=par,
                            tipo_orden=tipo_orden,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            capital=config.CAPITAL_INICIAL,
                            riesgo_porcentaje=config.RIESGO_PORCENTAJE,
                            nombre_estrategia=nombre_estrategia,
                            gestor_riesgo_global=gestor_riesgo_global # NUEVO: Pasamos la instancia
                        )
                    else:
                        logging.info(f"No se detectó ninguna señal para {par} con esta estrategia.")
                        print(f"❌ No se encontró señal para {par}.")
            
            time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Agente detenido por el usuario.")
            print("\n🛑 Agente detenido.")
            break
        except Exception as e:
            logging.error(f"Ocurrió un error: {e}", exc_info=True)
            print(f"🚨 ¡Ocurrió un error inesperado! Revisando en 60 segundos.")
            time.sleep(60)
            
    desconectar_mt5()
    logging.info("Agente de trading finalizado.")

if __name__ == "__main__":
    if conectar_mt5():
        main()
    else:
        print("No se pudo conectar a MetaTrader 5. El agente no se iniciará.")