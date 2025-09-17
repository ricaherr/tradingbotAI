import pandas as pd
import os
import sys

# Importar las funciones que queremos depurar
from src.estrategia_ia.core.indicadores import calcular_indicadores
from src.estrategia_ia.core.strategies import determinar_senales

def run_final_debug():
    """
    Script de depuración final y a prueba de fallos.
    Analiza una única vela y reporta cada paso.
    """
    try:
        # --- CONFIGURACIÓN DE LA PRUEBA ---
        NOMBRE_ARCHIVO_DATOS = "EURUSD_1h.csv"
        PUNTO_DE_PRUEBA = 500 # Analizaremos la vela número 500
        
        estrategia_config = {
            "nombre": "Reversión a la Media",
            "usar_filtro_tendencia": True,
            "ema_reversion": 20,
            "ema_tendencia": 50
        }
        
        ema_periods_requeridos = [20, 50]
        num_velas_minimas = max(ema_periods_requeridos) + 2

        # --- CARGA DE DATOS ---
        project_root = os.path.dirname(os.path.abspath(__file__))
        datos_historicos_csv = os.path.join(project_root, "data", "datos_historicos", NOMBRE_ARCHIVO_DATOS)
        df_historico = pd.read_csv(datos_historicos_csv, parse_dates=['timestamp'])
        df_historico.rename(columns={'timestamp': 'time'}, inplace=True)

        print("="*50)
        print("INICIANDO SCRIPT DE DEPURACIÓN FINAL")
        print(f"Analizando la vela #{PUNTO_DE_PRUEBA}")
        print("="*50)
        
        print(f"0. Datos históricos cargados. Número total de velas: {len(df_historico)}\n")
        if len(df_historico) < PUNTO_DE_PRUEBA:
            print("Error: El punto de prueba es mayor que el número de velas en el archivo.")
            return

        # --- LÓGICA DE PRUEBA AISLADA ---
        
        # 1. Obtener ventana de datos
        start_index = PUNTO_DE_PRUEBA - num_velas_minimas
        end_index = PUNTO_DE_PRUEBA
        df_ventana = df_historico.iloc[start_index:end_index].copy() # Usamos .copy() para más seguridad
        print(f"1. Ventana de datos obtenida: {len(df_ventana)} velas (desde el índice {start_index} a {end_index})\n")

        if df_ventana.empty:
            print("Error Crítico: La ventana de datos está vacía después de cortarla. El problema está en la manipulación del DataFrame.")
            return

        # 2. Calcular indicadores
        print("2. Calculando indicadores...")
        df_indicadores = calcular_indicadores(
            df_ventana,
            ema_periods=ema_periods_requeridos
        )
        print("Indicadores calculados. Columnas resultantes:")
        print(df_indicadores.columns.tolist())
        print("\nÚltimas 5 filas del DataFrame con indicadores:")
        print(df_indicadores.tail())
        print("\n")

        # 3. Determinar señal
        print("3. Determinando señal...")
        senal, razon = determinar_senales(df_indicadores, estrategia_config)
        
        # 4. Reporte final
        print("="*50)
        print("RESULTADO DE LA DEPURACIÓN")
        print("="*50)
        print(f"Señal generada: {senal}")
        print(f"Razón: {razon}")

    except Exception as e:
        print("\n" + "!"*50)
        print("HA OCURRIDO UNA EXCEPCIÓN INESPERADA")
        import traceback
        traceback.print_exc()
        print(""*50)

if __name__ == "__main__":
    run_final_debug()
