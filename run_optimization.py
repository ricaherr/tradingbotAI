import os
import sys
import copy
import json
from datetime import datetime
import MetaTrader5 as mt5
import matplotlib.pyplot as plt

# Importar los componentes de nuestro sistema de IA
from src.estrategia_ia.optimization.optimizer import IntelligentOptimizer
from src.estrategia_ia.core.data_manager import asegurar_datos_historicos
from src.estrategia_ia import config

def plot_and_save_convergence(history, strategy_name):
    """
    Genera y guarda un gráfico de la convergencia del Sharpe Ratio.
    """
    if not history:
        print("No hay historial de convergencia para graficar.")
        return

    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 7))

    cycles = range(1, len(history) + 1)
    ax.plot(cycles, history, marker='o', linestyle='-', color='royalblue', label='Mejor Sharpe Ratio')

    # Marcar el punto más alto
    best_sharpe = max(history)
    best_cycle = history.index(best_sharpe) + 1
    ax.scatter(best_cycle, best_sharpe, color='red', s=100, zorder=5, label=f'Máximo: {best_sharpe:.2f} (Ciclo {best_cycle})')

    ax.set_title(f'Convergencia de Optimización para "{strategy_name}"', fontsize=16)
    ax.set_xlabel('Ciclo de Optimización', fontsize=12)
    ax.set_ylabel('Mejor Sharpe Ratio Encontrado', fontsize=12)
    ax.legend()
    ax.grid(True)

    # Guardar el gráfico
    plot_filename = "convergence_plot.png"
    try:
        plt.savefig(plot_filename)
        print(f"\nGráfico de convergencia guardado como: {plot_filename}")
    except Exception as e:
        print(f"\nError al guardar el gráfico: {e}")

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
    print("Presiona Ctrl+C para detener la optimización en cualquier momento.")
    print("=" * 50)

    optimizer = IntelligentOptimizer(
        strategy_config=estrategia_para_optimizar, 
        data_file_path=ruta_archivo_datos
    )

    try:
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

    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("Optimización interrumpida por el usuario.")
        plot_and_save_convergence(optimizer.convergence_history, NOMBRE_ESTRATEGIA_A_OPTIMIZAR)
        print("Saliendo...")
        print("=" * 50)
        sys.exit(0)
    
    # Generar gráfico al final de la ejecución normal
    plot_and_save_convergence(optimizer.convergence_history, NOMBRE_ESTRATEGIA_A_OPTIMIZAR)


if __name__ == "__main__":
    run()
