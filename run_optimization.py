import os
import copy
import json
from datetime import datetime
import MetaTrader5 as mt5

# Importar los componentes de nuestro sistema de IA
from src.estrategia_ia.optimization.optimizer import IntelligentOptimizer
from src.estrategia_ia.core.data_manager import asegurar_datos_historicos
from src.estrategia_ia import config

def run():
    """
    Punto de entrada principal para el sistema de optimización de estrategias.
    """
    # --- 1. CONFIGURACIÓN DE LA OPTIMIZACIÓN ---
    NOMBRE_ESTRATEGIA_A_OPTIMIZAR = "Reversión a la Media"
    CICLOS_DE_OPTIMIZACION = 50 # Aumentamos los ciclos para una mejor búsqueda

    # --- 2. GESTIÓN AUTOMÁTICA DE DATOS ---
    print("=" * 50)
    print("Paso 1: Verificando y asegurando datos históricos...")
    print("=" * 50)
    
    # El data_manager se encargará de validar y/o descargar los datos necesarios
    ruta_archivo_datos = asegurar_datos_historicos(
        simbolo="EURUSD",
        timeframe=mt5.TIMEFRAME_H1,
        num_velas=50000, # Descargar ~5 años si es necesario
        min_velas=10000,  # Considerar el archivo válido si tiene al menos 10k velas
        max_age_days=7 # Descargar si el archivo tiene más de 7 días
    )

    if not ruta_archivo_datos:
        print("\nError Crítico: No se pudo obtener un archivo de datos válido. Abortando optimización.")
        return

    # --- 3. PREPARACIÓN DE LA ESTRATEGIA ---
    estrategia_original = next((item for item in config.ESTRATEGIAS if item["nombre"] == NOMBRE_ESTRATEGIA_A_OPTIMIZAR), None)

    if not estrategia_original:
        print(f"Error: No se encontró la estrategia '{NOMBRE_ESTRATEGIA_A_OPTIMIZAR}' en config.py")
        return

    estrategia_para_optimizar = copy.deepcopy(estrategia_original)

    # --- 4. EJECUCIÓN DEL OPTIMIZADOR DE IA ---
    print("\n" + "=" * 50)
    print(f"Paso 2: Iniciando optimizador para '{NOMBRE_ESTRATEGIA_A_OPTIMIZAR}'")
    print("=" * 50)

    optimizer = IntelligentOptimizer(
        strategy_config=estrategia_para_optimizar, 
        data_file_path=ruta_archivo_datos
    )

    best_result, best_config = optimizer.run_optimization_cycles(CICLOS_DE_OPTIMIZACION)

    # --- 5. GUARDADO DE RESULTADOS ---
    if best_result and best_config:
        print("\n" + "=" * 50)
        print("Paso 3: Guardando el mejor resultado encontrado...")
        print("=" * 50)
        
        nombre_archivo_json = f"{NOMBRE_ESTRATEGIA_A_OPTIMIZAR.replace(' ', '_')}.json"
        project_root = os.path.dirname(os.path.abspath(__file__))
        ruta_json = os.path.join(project_root, "src", "estrategia_ia", "core", nombre_archivo_json)

        resultado_final_json = {
            "nombre_estrategia": best_config["nombre"],
            "descripcion": "Resultados de la optimización de IA.",
            "ultima_optimizacion": datetime.now().isoformat(),
            "mejor_resultado": {
                "estado": "Viable" if best_result["profit_neto"] > 0 and best_result["sharpe_ratio"] > 0.1 else "No Viable",
                "parametros_optimos": {k: best_config[k] for k in best_config.get("optimizable_params", {}).keys()},
                "metricas_rendimiento": best_result
            },
            "historial_optimizaciones": optimizer.results_history
        }

        try:
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(resultado_final_json, f, indent=4, ensure_ascii=False, default=str)
            print(f"Resultados guardados exitosamente en: {ruta_json}")
        except Exception as e:
            print(f"Error al guardar el archivo JSON: {e}")
    else:
        print("\nNo se encontró una configuración rentable para guardar.")

if __name__ == "__main__":
    run()