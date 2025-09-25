#!/usr/bin/env python3
"""
Script mejorado para ejecutar la optimización genética de estrategias de trading.
"""

import sys
import os
import argparse
import time

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from estrategia_ia.optimization.optimizer import GeneticOptimizer
from estrategia_ia.config import ESTRATEGIAS, OPTIMIZER_SETTINGS, validar_configuracion
from estrategia_ia.utils.logger import setup_logger
from estrategia_ia.utils.progress_bar import OptimizationProgress
from estrategia_ia.core.data_manager import asegurar_datos_historicos
import MetaTrader5 as mt5

def parse_arguments():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Optimizador Genético de Estrategias de Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_optimization_enhanced.py                    # Optimización completa
  python run_optimization_enhanced.py --quick            # Optimización rápida
  python run_optimization_enhanced.py --strategy "Reversión a la Media"
  python run_optimization_enhanced.py --generations 10 --population 20
  python run_optimization_enhanced.py --profile          # Con profiling de rendimiento
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Optimización rápida (5 gen, 20 individuos)')
    
    parser.add_argument('--strategy', type=str,
                       help='Optimizar solo una estrategia específica')
    
    parser.add_argument('--generations', type=int,
                       help='Número de generaciones (sobrescribe config)')
    
    parser.add_argument('--population', type=int,
                       help='Tamaño de población (sobrescribe config)')
    
    parser.add_argument('--profile', action='store_true',
                       help='Activar profiling de rendimiento')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Salida detallada')
    
    parser.add_argument('--no-progress', action='store_true',
                       help='Desactivar barra de progreso')
    
    return parser.parse_args()

def apply_quick_settings():
    """Aplica configuración rápida para pruebas."""
    OPTIMIZER_SETTINGS['generations'] = 2
    OPTIMIZER_SETTINGS['population_size'] = 4
    print("[INFO] Modo rápido activado: 2 generaciones, 4 individuos")

def main():
    """Función principal del optimizador."""
    args = parse_arguments()
    
    # Configurar logging
    logger = setup_logger("optimizer_main")
    
    print("=" * 60)
    print("    OPTIMIZADOR GENÉTICO DE ESTRATEGIAS DE TRADING")
    print("=" * 60)
    
    # Aplicar configuraciones de argumentos
    if args.quick:
        apply_quick_settings()
    
    if args.generations:
        OPTIMIZER_SETTINGS['generations'] = args.generations
        print(f"[INFO] Generaciones configuradas: {args.generations}")
    
    if args.population:
        OPTIMIZER_SETTINGS['population_size'] = args.population
        print(f"[INFO] Población configurada: {args.population}")
    
    # Validar configuración
    if not validar_configuracion():
        print("\nAbortando optimización debido a errores de configuración.")
        return
    
    # Buscar estrategias activas para optimización
    estrategias_activas = [e for e in ESTRATEGIAS if e.get("modo") == "backtest"]
    
    # Filtrar por estrategia específica si se especificó
    if args.strategy:
        estrategias_activas = [e for e in estrategias_activas if args.strategy.lower() in e['nombre'].lower()]
        if not estrategias_activas:
            print(f"\n[ERROR] No se encontró la estrategia '{args.strategy}'")
            return
    
    if not estrategias_activas:
        print("\n[WARNING] No se encontraron estrategias activas para optimización.")
        print("Configura al menos una estrategia con modo='backtest' en config.py")
        return
    
    print(f"\n[INFO] Estrategias a optimizar: {len(estrategias_activas)}")
    for estrategia in estrategias_activas:
        print(f"  - {estrategia['nombre']}")
    
    # Mostrar configuración del optimizador
    print(f"\n[INFO] Configuración del optimizador:")
    print(f"  - Población: {OPTIMIZER_SETTINGS['population_size']}")
    print(f"  - Generaciones: {OPTIMIZER_SETTINGS['generations']}")
    print(f"  - Tasa de mutación: {OPTIMIZER_SETTINGS['mutation_rate']}")
    print(f"  - Tasa de cruce: {OPTIMIZER_SETTINGS['crossover_rate']}")
    print(f"  - Uso de CPU: {OPTIMIZER_SETTINGS['cpu_core_usage']*100}%")
    
    # Profiling si se solicita
    if args.profile:
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()
    
    # Gestión de datos históricos
    print(f"\n[INFO] Verificando datos históricos...")
    
    if args.quick:
        num_velas = 1000  # Solo 1000 velas para pruebas rápidas
        min_velas = 500
    else:
        num_velas = 50000
        min_velas = 10000
    
    ruta_archivo_datos = asegurar_datos_historicos(
        simbolo="EURUSD",
        timeframe=mt5.TIMEFRAME_H1,
        num_velas=num_velas,
        min_velas=min_velas,
        max_age_days=7
    )
    
    if not ruta_archivo_datos:
        print("\n[ERROR] No se pudo obtener archivo de datos válido")
        return
    
    print(f"[INFO] Usando datos: {ruta_archivo_datos}")
    
    start_time = time.time()
    
    # Ejecutar optimización para cada estrategia
    for i, estrategia in enumerate(estrategias_activas):
        print(f"\n{'='*60}")
        print(f"OPTIMIZANDO ({i+1}/{len(estrategias_activas)}): {estrategia['nombre']}")
        print(f"{'='*60}")
        
        try:
            # Crear optimizador con parámetros correctos
            optimizer = GeneticOptimizer(
                strategy_config=estrategia,
                data_file_path=ruta_archivo_datos,
                population_size=OPTIMIZER_SETTINGS['population_size'],
                generations=OPTIMIZER_SETTINGS['generations'],
                mutation_rate=OPTIMIZER_SETTINGS['mutation_rate'],
                crossover_rate=OPTIMIZER_SETTINGS['crossover_rate'],
                tournament_size=OPTIMIZER_SETTINGS['tournament_size'],
                cpu_core_usage=OPTIMIZER_SETTINGS['cpu_core_usage'],
                backtest_period_years=0.1 if args.quick else None,  # Solo ~36 días para modo rápido
                test_mode=args.quick
            )
            
            # Configurar progreso si no está desactivado
            if not args.no_progress:
                progress = OptimizationProgress(
                    OPTIMIZER_SETTINGS['generations'],
                    OPTIMIZER_SETTINGS['population_size']
                )
                # Nota: Necesitaríamos modificar GeneticOptimizer para soportar callbacks
                # optimizer.set_progress_callback(progress)
            
            mejor_resultado, mejor_config = optimizer.run_optimization()
            
            if mejor_resultado:
                mejor_fitness = mejor_resultado.get('sharpe_ratio', 0)
            else:
                mejor_fitness = 0
            
            print(f"\n[SUCCESS] Optimización completada para '{estrategia['nombre']}'")
            print(f"Mejor fitness: {mejor_fitness:.4f}")
            if args.verbose:
                print(f"Mejor configuración: {mejor_config}")
            
        except Exception as e:
            logger.error(f"Error optimizando {estrategia['nombre']}: {e}")
            print(f"\n[ERROR] Fallo en optimización de '{estrategia['nombre']}': {e}")
    
    # Mostrar tiempo total
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"OPTIMIZACIÓN COMPLETADA en {total_time:.1f} segundos")
    print(f"{'='*60}")
    
    # Mostrar profiling si se activó
    if args.profile:
        profiler.disable()
        stats = pstats.Stats(profiler)
        print("\n[PROFILING] Top 10 funciones más lentas:")
        stats.sort_stats('cumulative').print_stats(10)

if __name__ == "__main__":
    main()