#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA DEL SISTEMA DE OPTIMIZACIÓN
Rastrea cada paso del flujo completo para identificar todas las inconsistencias.
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.config import ESTRATEGIAS, TIMEFRAMES_CONFIG
from estrategia_ia.optimization.timeframe_optimizer import TimeframeOptimizer
from estrategia_ia.optimization.optimizer import GeneticOptimizer
from estrategia_ia.optimization.fitness_worker import run_fitness_calculation
from estrategia_ia.backtesting.backtester import run_backtest
from estrategia_ia.optimization.evaluator import Evaluator
from estrategia_ia.core.data_manager import asegurar_datos_historicos

def audit_step_1_cli_parsing():
    """Simula el parsing del CLI con -t M30"""
    print("=== PASO 1: CLI PARSING ===")
    
    # Simular argumentos del CLI
    timeframes_input = "M30"
    timeframes = [tf.strip().upper() for tf in timeframes_input.split(',')]
    
    print(f"Input CLI: -t {timeframes_input}")
    print(f"Timeframes parseados: {timeframes}")
    print(f"Timeframes válidos: {list(TIMEFRAMES_CONFIG.keys())}")
    
    # Validar
    invalid = [tf for tf in timeframes if tf not in TIMEFRAMES_CONFIG.keys()]
    if invalid:
        print(f"[ERROR] Timeframes inválidos: {invalid}")
        return None
    else:
        print("[OK] Timeframes válidos")
        return timeframes

def audit_step_2_strategy_selection():
    """Audita la selección de estrategia"""
    print("\n=== PASO 2: SELECCIÓN DE ESTRATEGIA ===")
    
    strategy_name = "Reversión"
    strategy = None
    
    for s in ESTRATEGIAS:
        if strategy_name.lower() in s["nombre"].lower():
            strategy = s
            break
    
    if not strategy:
        print(f"[ERROR] Estrategia '{strategy_name}' no encontrada")
        return None
    
    print(f"[OK] Estrategia encontrada: {strategy['nombre']}")
    print(f"Parámetros optimizables: {list(strategy.get('optimizable_params', {}).keys())}")
    
    return strategy

def audit_step_3_timeframe_optimizer_init(strategy, timeframes):
    """Audita la inicialización del TimeframeOptimizer"""
    print("\n=== PASO 3: TIMEFRAME OPTIMIZER INIT ===")
    
    optimizer = TimeframeOptimizer(
        strategy_config=strategy,
        timeframes=timeframes,
        backtest_days=30,  # Usar 30 días para prueba rápida
        generations=1,
        population_size=2
    )
    
    print(f"TimeframeOptimizer creado:")
    print(f"  strategy_name: {optimizer.strategy_name}")
    print(f"  timeframes: {optimizer.timeframes}")
    print(f"  backtest_days: {optimizer.backtest_days}")
    
    return optimizer

def audit_step_4_data_acquisition(optimizer):
    """Audita la obtención de datos"""
    print("\n=== PASO 4: OBTENCIÓN DE DATOS ===")
    
    timeframe = optimizer.timeframes[0]  # M30
    print(f"Obteniendo datos para timeframe: {timeframe}")
    
    # Llamar al método real
    data_file = optimizer._get_timeframe_data(timeframe)
    
    print(f"Archivo obtenido: {data_file}")
    
    # Verificar que el archivo existe y es correcto
    if data_file and os.path.exists(data_file):
        filename = os.path.basename(data_file)
        print(f"[OK] Archivo existe: {filename}")
        
        # Verificar que contiene M30
        if "M30" in filename:
            print("[OK] Archivo corresponde a M30")
        else:
            print(f"[ERROR] Archivo no corresponde a M30: {filename}")
            
        return data_file
    else:
        print("[ERROR] Archivo no existe")
        return None

def audit_step_5_config_creation(optimizer):
    """Audita la creación de configuración para timeframe fijo"""
    print("\n=== PASO 5: CREACIÓN DE CONFIGURACIÓN ===")
    
    timeframe = optimizer.timeframes[0]  # M30
    config = optimizer._create_single_timeframe_config(timeframe)
    
    print(f"Configuración creada para {timeframe}:")
    print(f"  fixed_timeframe: {config.get('fixed_timeframe')}")
    print(f"  timeframe_name: {config.get('timeframe_name')}")
    print(f"  backtest_days: {config.get('backtest_days')}")
    
    # Verificar que fixed_timeframe es correcto
    expected_index = list(TIMEFRAMES_CONFIG.keys()).index(timeframe)
    actual_index = config.get('fixed_timeframe')
    
    if actual_index == expected_index:
        print(f"[OK] fixed_timeframe correcto: {actual_index} (esperado: {expected_index})")
    else:
        print(f"[ERROR] fixed_timeframe incorrecto: {actual_index} (esperado: {expected_index})")
    
    # Verificar que timeframe no está en optimizable_params
    if 'optimizable_params' in config and 'timeframe' in config['optimizable_params']:
        print("[ERROR] timeframe aún está en optimizable_params")
    else:
        print("[OK] timeframe removido de optimizable_params")
    
    return config

def audit_step_6_genetic_optimizer_init(config, data_file):
    """Audita la inicialización del GeneticOptimizer"""
    print("\n=== PASO 6: GENETIC OPTIMIZER INIT ===")
    
    genetic_optimizer = GeneticOptimizer(
        strategy_config=config,
        data_file_path=data_file,
        population_size=2,
        generations=1,
        test_mode=True  # Para evitar multiprocessing
    )
    
    print(f"GeneticOptimizer creado:")
    print(f"  data_file_path: {os.path.basename(genetic_optimizer.data_file_path)}")
    print(f"  strategy_config keys: {list(genetic_optimizer.strategy_config_base.keys())}")
    print(f"  fixed_timeframe: {genetic_optimizer.strategy_config_base.get('fixed_timeframe')}")
    
    return genetic_optimizer

def audit_step_7_individual_creation(genetic_optimizer):
    """Audita la creación de individuos"""
    print("\n=== PASO 7: CREACIÓN DE INDIVIDUOS ===")
    
    # Crear población inicial
    population = genetic_optimizer._create_initial_population()
    
    print(f"Población creada: {len(population)} individuos")
    print(f"Primer individuo: {population[0]}")
    
    # Verificar que no contiene timeframe
    if 'timeframe' in population[0]:
        print("[ERROR] Individuo contiene parámetro timeframe")
    else:
        print("[OK] Individuo no contiene timeframe (correcto para modo fijo)")
    
    return population[0]

def audit_step_8_fitness_calculation(genetic_optimizer, individual):
    """Audita el cálculo de fitness"""
    print("\n=== PASO 8: CÁLCULO DE FITNESS ===")
    
    # Método directo del optimizer
    print("8a. Método directo del optimizer:")
    fitness_direct = genetic_optimizer._calculate_fitness(individual)
    print(f"  Fitness directo: {fitness_direct}")
    
    # Método del fitness_worker
    print("\n8b. Método del fitness_worker:")
    args = (
        individual,
        genetic_optimizer.strategy_config_base,
        genetic_optimizer.data_file_path,
        None,  # backtest_period_years
        True   # test_mode
    )
    
    fitness_worker = run_fitness_calculation(args)
    print(f"  Fitness worker: {fitness_worker}")
    
    # Comparar
    if abs(fitness_direct - fitness_worker) < 0.001:
        print("[OK] Fitness consistente entre métodos")
    else:
        print(f"[ERROR] Fitness inconsistente: {fitness_direct} vs {fitness_worker}")
    
    return fitness_direct

def audit_step_9_backtest_direct(genetic_optimizer, individual):
    """Audita el backtest directo"""
    print("\n=== PASO 9: BACKTEST DIRECTO ===")
    
    # Ejecutar backtest directamente
    report = genetic_optimizer._run_backtest(individual)
    
    if not report:
        print("[ERROR] Backtest no generó reporte")
        return None
    
    print(f"Reporte generado:")
    print(f"  Operaciones totales: {report.get('operaciones_totales', 0)}")
    print(f"  Profit neto: ${report.get('profit_neto', 0):.2f}")
    print(f"  Capital final: ${report.get('capital_final', 0):.2f}")
    print(f"  Sharpe (engine): {report.get('sharpe_ratio', 0):.4f}")
    
    return report

def audit_step_10_evaluator_analysis(report):
    """Audita el análisis del Evaluator"""
    print("\n=== PASO 10: ANÁLISIS DEL EVALUATOR ===")
    
    evaluator = Evaluator(report)
    evaluation = evaluator.evaluate()
    
    print(f"Evaluación generada:")
    print(f"  Sharpe (evaluator): {evaluation.get('sharpe_ratio', 0):.4f}")
    print(f"  ROI mensual: {evaluation.get('roi_mensual_pct', 0):.4f}%")
    print(f"  Win rate: {evaluation.get('win_rate_pct', 0):.2f}%")
    
    # Comparar con engine
    engine_sharpe = report.get('sharpe_ratio', 0)
    evaluator_sharpe = evaluation.get('sharpe_ratio', 0)
    
    if abs(engine_sharpe - evaluator_sharpe) < 0.1:
        print("[OK] Sharpe consistente entre engine y evaluator")
    else:
        print(f"[ERROR] Sharpe inconsistente: engine={engine_sharpe:.4f} vs evaluator={evaluator_sharpe:.4f}")
    
    return evaluation

def audit_step_11_data_verification():
    """Verifica que se están usando los datos correctos"""
    print("\n=== PASO 11: VERIFICACIÓN DE DATOS ===")
    
    # Verificar archivos existentes
    data_dir = os.path.join(os.path.dirname(__file__), "data", "datos_historicos")
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        print(f"Archivos de datos disponibles: {files}")
        
        # Verificar M30
        m30_files = [f for f in files if 'M30' in f]
        if m30_files:
            print(f"[OK] Archivos M30 encontrados: {m30_files}")
        else:
            print("[ERROR] No se encontraron archivos M30")
    else:
        print("[ERROR] Directorio de datos no existe")

def run_full_audit():
    """Ejecuta la auditoría completa"""
    print("AUDITORÍA COMPLETA DEL SISTEMA DE OPTIMIZACIÓN")
    print("=" * 60)
    
    try:
        # Paso 1: CLI Parsing
        timeframes = audit_step_1_cli_parsing()
        if not timeframes:
            return
        
        # Paso 2: Strategy Selection
        strategy = audit_step_2_strategy_selection()
        if not strategy:
            return
        
        # Paso 3: TimeframeOptimizer Init
        optimizer = audit_step_3_timeframe_optimizer_init(strategy, timeframes)
        
        # Paso 4: Data Acquisition
        data_file = audit_step_4_data_acquisition(optimizer)
        if not data_file:
            return
        
        # Paso 5: Config Creation
        config = audit_step_5_config_creation(optimizer)
        
        # Paso 6: GeneticOptimizer Init
        genetic_optimizer = audit_step_6_genetic_optimizer_init(config, data_file)
        
        # Paso 7: Individual Creation
        individual = audit_step_7_individual_creation(genetic_optimizer)
        
        # Paso 8: Fitness Calculation
        fitness = audit_step_8_fitness_calculation(genetic_optimizer, individual)
        
        # Paso 9: Backtest Direct
        report = audit_step_9_backtest_direct(genetic_optimizer, individual)
        if not report:
            return
        
        # Paso 10: Evaluator Analysis
        evaluation = audit_step_10_evaluator_analysis(report)
        
        # Paso 11: Data Verification
        audit_step_11_data_verification()
        
        print("\n" + "=" * 60)
        print("AUDITORÍA COMPLETADA")
        print("Revisa los mensajes [ERROR] para identificar problemas")
        
    except Exception as e:
        print(f"\n[ERROR] ERROR DURANTE AUDITORÍA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_full_audit()