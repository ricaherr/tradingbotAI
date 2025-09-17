import MetaTrader5 as mt5
import os
import pandas as pd
import time
from datetime import datetime

def asegurar_datos_historicos(simbolo, timeframe, num_velas, min_velas, reintentos=3, max_age_days=7):
    """
    Asegura que un archivo de datos históricos exista, tenga suficientes registros y no sea demasiado antiguo.
    Si no es así, intenta descargarlo desde MetaTrader 5 con una lógica de reintentos.

    Args:
        simbolo (str): El símbolo a descargar (ej. "EURUSD").
        timeframe (mt5.TIMEFRAME): El timeframe de MT5 (ej. mt5.TIMEFRAME_H1).
        num_velas (int): El número de velas a descargar si el archivo no existe o está desactualizado.
        min_velas (int): El número mínimo de velas que el archivo debe tener para ser válido.
        reintentos (int): Número de veces que se intentará la conexión/descarga.
        max_age_days (int|None): Si el archivo es más antiguo que este número de días, se considera desactualizado.
                                 None para no verificar la antigüedad. Por defecto, 7 días.

    Returns:
        str|None: La ruta al archivo de datos si es válido, o None si falla.
    """
    nombre_archivo = f"{simbolo}_{timeframe_to_str(timeframe)}.csv"
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    output_path = os.path.join(project_root, "data", "datos_historicos", nombre_archivo)

    # 1. Validar el archivo existente (tamaño y antigüedad)
    if os.path.exists(output_path):
        try:
            df_existente = pd.read_csv(output_path)
            
            # Verificar antigüedad
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(output_path))
            file_age_days = (datetime.now() - file_mod_time).days

            if len(df_existente) >= min_velas and (max_age_days is None or file_age_days <= max_age_days):
                print(f"Archivo de datos '{nombre_archivo}' encontrado, validado ({len(df_existente)} velas) y actualizado (hace {file_age_days} días).")
                return output_path
            else:
                razon_descarga = []
                if len(df_existente) < min_velas: razon_descarga.append(f"demasiado pequeño ({len(df_existente)}/{min_velas} velas)")
                if max_age_days is not None and file_age_days > max_age_days: razon_descarga.append(f"demasiado antiguo (hace {file_age_days} días)")
                print(f"Archivo de datos '{nombre_archivo}' encontrado, pero {' y '.join(razon_descarga)}. Se descargará de nuevo.")
        except pd.errors.EmptyDataError:
            print(f"Archivo de datos '{nombre_archivo}' está vacío. Se descargará de nuevo.")
        except Exception as e:
            print(f"Error al leer el archivo '{nombre_archivo}': {e}. Se descargará de nuevo.")

    # 2. Si el archivo no es válido o no existe, intentar la descarga
    print(f"Iniciando descarga de datos para '{simbolo}'...")
    for i in range(reintentos):
        print(f"Intento de descarga {i + 1}/{reintentos}...")
        if _descargar_y_guardar(simbolo, timeframe, num_velas, output_path):
            # Verificar que el archivo descargado ahora sí es válido
            df_descargado = pd.read_csv(output_path)
            if len(df_descargado) >= min_velas:
                return output_path
            else:
                print(f"La descarga fue exitosa pero no se obtuvieron suficientes datos ({len(df_descargado)}/{min_velas}).")
        
        if i < reintentos - 1:
            print("La descarga falló. Esperando 5 segundos antes de reintentar...")
            time.sleep(5)

    print(f"Error: No se pudieron obtener datos válidos para '{simbolo}' después de {reintentos} intentos.")
    return None

def _descargar_y_guardar(simbolo, timeframe, num_velas, output_path):
    """Función auxiliar para conectar, descargar y guardar los datos."""
    if not mt5.initialize():
        print("Error de conexión: No se pudo inicializar MetaTrader 5. ¿Está la terminal abierta?")
        return False
    
    print("Conexión con MT5 establecida.")
    
    try:
        rates = mt5.copy_rates_from_pos(simbolo, timeframe, 0, num_velas)
    except Exception as e:
        print(f"Ocurrió un error en la API de MT5 al descargar los datos: {e}")
        mt5.shutdown()
        return False
    finally:
        mt5.shutdown()
        print("Conexión con MT5 cerrada.")

    if rates is None or len(rates) == 0:
        print("Error de datos: No se recibieron datos de MT5. Verifique el nombre del símbolo.")
        return False

    print(f"Se descargaron {len(rates)} velas. Procesando y guardando...")
    df = pd.DataFrame(rates)
    df['timestamp'] = pd.to_datetime(df['time'], unit='s')
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'tick_volume']]
    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    
    try:
        df.to_csv(output_path, index=False)
        print(f"Datos guardados exitosamente en '{os.path.basename(output_path)}'.")
        return True
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")
        return False

def timeframe_to_str(timeframe):
    """Convierte un timeframe de MT5 a un string legible."""
    mapa = {
        mt5.TIMEFRAME_M1: "M1",
        mt5.TIMEFRAME_M5: "M5",
        mt5.TIMEFRAME_H1: "H1",
        mt5.TIMEFRAME_D1: "D1",
    }
    return mapa.get(timeframe, "desconocido")