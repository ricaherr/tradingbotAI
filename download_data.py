import MetaTrader5 as mt5
import os
import pandas as pd
from datetime import datetime, timedelta

def download_real_data():
    """
    Se conecta a MetaTrader 5 para descargar un historial de datos reales.
    """
    # --- PARÁMETROS DE DESCARGA ---
    SIMBOLO = "EURUSD"
    TIMEFRAME = mt5.TIMEFRAME_H1 # Velas de 1 Hora
    NUM_VELAS = 50000 # Aproximadamente 5 años de datos horarios
    NOMBRE_ARCHIVO = "EURUSD_1h.csv"

    print("="*50)
    print("INICIANDO DESCARGA DE DATOS REALES DESDE METATRADER 5")
    print("Asegúrate de que la terminal de MT5 está abierta.")
    print("="*50)

    # 1. Conectar con MetaTrader 5
    if not mt5.initialize():
        print("Error: Fallo al inicializar MetaTrader 5. ¿Está la terminal abierta?")
        mt5.shutdown()
        return
    
    print("Conexión con MetaTrader 5 establecida.")

    # 2. Obtener datos
    print(f"Descargando {NUM_VELAS} velas de {SIMBOLO} en timeframe H1...")
    try:
        rates = mt5.copy_rates_from_pos(SIMBOLO, TIMEFRAME, 0, NUM_VELAS)
    except Exception as e:
        print(f"Ocurrió un error al descargar los datos: {e}")
        mt5.shutdown()
        return

    # 3. Desconectar de MT5
    mt5.shutdown()
    print("Conexión con MetaTrader 5 cerrada.")

    if rates is None or len(rates) == 0:
        print("Error: No se recibieron datos de MT5. Verifica el nombre del símbolo y la conexión.")
        return

    # 4. Procesar y guardar los datos
    print(f"Se descargaron {len(rates)} velas. Procesando...")
    df = pd.DataFrame(rates)
    # La columna 'time' de MT5 viene como timestamp de Unix, la convertimos a datetime
    df['timestamp'] = pd.to_datetime(df['time'], unit='s')
    
    # Seleccionar y renombrar columnas para que coincidan con nuestro formato
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'tick_volume']]
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)

    # 5. Guardar en el archivo CSV
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(project_root, "data", "datos_historicos", NOMBRE_ARCHIVO)
    
    try:
        df.to_csv(output_path, index=False)
        print(f"\n¡ÉXITO! Archivo '{NOMBRE_ARCHIVO}' guardado con {len(df)} velas de datos reales.")
        print(f"Ubicación: {output_path}")
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")

if __name__ == "__main__":
    download_real_data()
