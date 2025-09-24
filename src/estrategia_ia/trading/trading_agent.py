import MetaTrader5 as mt5
import time
import logging

# --- IMPORTAR CONFIGURACIÓN Y COMPONENTES DEL CORE ---
from estrategia_ia import config
from estrategia_ia.core.engine import TradingEngine
from estrategia_ia.core.live_data_source import LiveDataSource
from estrategia_ia.trading.mt5_broker import MT5Broker

# --- CONFIGURACIÓN DEL REGISTRO ---
from estrategia_ia.utils.logger import engine_logger, broker_logger
from estrategia_ia.utils.error_handler import retry_on_failure

# --- FUNCIONES DE CONEXIÓN ---
@retry_on_failure(max_retries=3, delay=2, exceptions=(ConnectionError,))
def conectar_mt5():
    """
    Establece la conexión con MetaTrader 5.
    """
    if not mt5.initialize():
        error_code = mt5.last_error()
        broker_logger.error("Fallo al inicializar MetaTrader 5, error code: %s", error_code)
        raise ConnectionError(f"No se pudo inicializar MT5: {error_code}")
    
    print("Conexión con MT5 inicializada. Esperando para estabilizar...")
    time.sleep(1)
    
    account_info = mt5.account_info()
    if not account_info:
        raise ConnectionError("No se pudo obtener información de la cuenta MT5")
    
    broker_logger.info(f"Conexión exitosa a la cuenta: {account_info.login} en {account_info.server}")
    print(f"[OK] Conexión exitosa a la cuenta: {account_info.login} ({account_info.server})")
    return True

def desconectar_mt5():
    """Desconecta de MetaTrader 5."""
    mt5.shutdown()
    print("[OK] Desconexión de MetaTrader 5.")

def main():
    """
    Función principal del agente de trading que utiliza el TradingEngine.
    """
    # Validar configuración antes de iniciar
    if not config.validar_configuracion():
        return
        
    try:
        conectar_mt5()
    except ConnectionError as e:
        print(f"[ERROR] No se pudo conectar a MT5: {e}")
        return

    # Seleccionar la primera estrategia activa para operar en vivo
    # En una implementación más avanzada, se podría iterar sobre varias
    strategy_config = next((s for s in config.ESTRATEGIAS if s.get("modo") == "live"), None)

    if not strategy_config:
        print("[DETENIDO] No hay estrategias activas configuradas para 'live'.")
        desconectar_mt5()
        return

    simbolo = strategy_config.get("par", "EURUSD")
    nombre_estrategia = strategy_config.get('nombre', 'Estrategia Desconocida')
    print(f"Iniciando agente para la estrategia '{nombre_estrategia}' en el par {simbolo}")

    try:
        # 1. Configurar la fuente de datos en vivo
        data_source = LiveDataSource(
            simbolo=simbolo,
            timeframe=config.TIMEFRAME,
            num_velas_historicas=config.NUM_VELAS,
            verbose=True
        )

        # 2. Configurar el broker de MT5
        broker = MT5Broker(
            capital_inicial=config.CAPITAL_INICIAL,
            riesgo_porcentaje=config.RIESGO_PORCENTAJE,
            verbose=True
        )

        # 3. Configurar el motor de trading
        risk_manager_config = {
            "TRAILING_ACTIVO": config.TRAILING_ACTIVO,
            "BREAK_EVEN_ACTIVO": config.BREAK_EVEN_ACTIVO,
            "BREAK_EVEN_ATR_FACTOR": config.BREAK_EVEN_ATR_FACTOR,
            "TRAILING_ATR_FACTOR": config.TRAILING_ATR_FACTOR
        }

        engine = TradingEngine(
            strategy_config=strategy_config,
            broker=broker,
            data_source=data_source,
            risk_manager_config=risk_manager_config,
            verbose=True
        )

        # 4. Ejecutar el motor
        print("Motor de trading iniciado. Presiona Ctrl+C para detener.")
        engine.run()

    except KeyboardInterrupt:
        print("\n[DETENIDO] Agente detenido por el usuario.")
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado en el agente: {e}", exc_info=True)
        print(f"[ERROR] Ocurrió un error inesperado: {e}")
    finally:
        desconectar_mt5()
        engine_logger.info("Agente de trading finalizado.")

if __name__ == "__main__":
    main()
