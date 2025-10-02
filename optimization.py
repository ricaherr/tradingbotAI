#!/usr/bin/env python3
"""
CLI para optimización multi-timeframe con parámetros personalizables.
Uso: python optimization.py [opciones]
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from estrategia_ia.config import ESTRATEGIAS, TIMEFRAME_OPTIMIZATION, TIMEFRAMES_CONFIG, OPTIMIZER_SETTINGS
from estrategia_ia.optimization.timeframe_optimizer import TimeframeOptimizer

def parse_timeframes(timeframes_str):
    """Parsea string de timeframes separados por comas."""
    if not timeframes_str:
        return TIMEFRAME_OPTIMIZATION["default_timeframes"]
    
    timeframes = [tf.strip().upper() for tf in timeframes_str.split(',')]
    valid_timeframes = list(TIMEFRAMES_CONFIG.keys())
    
    invalid = [tf for tf in timeframes if tf not in valid_timeframes]
    if invalid:
        raise ValueError(f"Timeframes inválidos: {invalid}. Válidos: {valid_timeframes}")
    
    return timeframes

def get_strategy_by_name(name):
    """Obtiene estrategia por nombre (búsqueda flexible)."""
    name_lower = name.lower()
    
    # Búsqueda exacta
    for strategy in ESTRATEGIAS:
        if strategy["nombre"].lower() == name_lower:
            return strategy
    
    # Búsqueda parcial
    for strategy in ESTRATEGIAS:
        if name_lower in strategy["nombre"].lower():
            return strategy
    
    return None

def list_strategies():
    """Lista todas las estrategias disponibles."""
    print("Estrategias disponibles:")
    for i, strategy in enumerate(ESTRATEGIAS, 1):
        status = "ACTIVA" if strategy.get("modo") == "backtest" else "INACTIVA"
        print(f"  {i}. {strategy['nombre']} ({status})")

def main():
    parser = argparse.ArgumentParser(
        description="Optimización multi-timeframe con parámetros personalizables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python optimization.py --strategy "Reversión" --mode full
  python optimization.py --strategy "Rompimiento" --mode hybrid --timeframes M5,M15,H1
  python optimization.py --strategy "Cruce" --mode screening --days 60
  python optimization.py --list-strategies
  python optimization.py --strategy "Reversión" --timeframes M1,M5 --days 30 --mode single
        """
    )
    
    parser.add_argument('--strategy', '-s', type=str,
                       help='Nombre de la estrategia (búsqueda flexible)')
    
    parser.add_argument('--mode', '-m', type=str,
                       choices=['single', 'screening', 'hybrid', 'full'],
                       default=TIMEFRAME_OPTIMIZATION["mode"],
                       help=f'Modo de optimización (default: {TIMEFRAME_OPTIMIZATION["mode"]})')
    
    parser.add_argument('--timeframes', '-t', type=str,
                       help=f'Timeframes separados por comas (default: {",".join(TIMEFRAME_OPTIMIZATION["default_timeframes"])})')
    
    parser.add_argument('--days', '-d', type=int,
                       default=TIMEFRAME_OPTIMIZATION["backtest_period_days"],
                       help=f'Días de backtest (default: {TIMEFRAME_OPTIMIZATION["backtest_period_days"]})')
    
    parser.add_argument('--list-strategies', action='store_true',
                       help='Lista todas las estrategias disponibles')
    
    parser.add_argument('--output', '-o', type=str,
                       help='Archivo de salida para resultados (opcional)')
    
    parser.add_argument('--generations', '-g', type=int,
                       default=OPTIMIZER_SETTINGS["generations"],
                       help=f'Número de generaciones (default: {OPTIMIZER_SETTINGS["generations"]})')
    
    parser.add_argument('--population', '-p', type=int,
                       default=OPTIMIZER_SETTINGS["population_size"],
                       help=f'Tamaño de población (default: {OPTIMIZER_SETTINGS["population_size"]})')
    
    args = parser.parse_args()
    
    # Listar estrategias si se solicita
    if args.list_strategies:
        list_strategies()
        return
    
    # Validar que se especificó una estrategia
    if not args.strategy:
        print("Error: Debe especificar una estrategia con --strategy")
        print("Use --list-strategies para ver las disponibles")
        return
    
    # Buscar estrategia
    strategy = get_strategy_by_name(args.strategy)
    if not strategy:
        print(f"Error: Estrategia '{args.strategy}' no encontrada")
        list_strategies()
        return
    
    # Parsear timeframes
    try:
        timeframes = parse_timeframes(args.timeframes)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Validar días
    if args.days <= 0:
        print("Error: Los días deben ser mayor a 0")
        return
    
    # Validar generaciones e individuos
    if args.generations <= 0:
        print("Error: Las generaciones deben ser mayor a 0")
        return
    
    if args.population <= 1:
        print("Error: La población debe ser mayor a 1")
        return
    
    # Mostrar configuración
    print(f"=== CONFIGURACIÓN ===")
    print(f"Estrategia: {strategy['nombre']}")
    print(f"Modo: {args.mode}")
    print(f"Timeframes: {', '.join(timeframes)}")
    print(f"Período: {args.days} días")
    print(f"Generaciones: {args.generations}")
    print(f"Población: {args.population}")
    print(f"Archivo salida: {args.output or 'Auto-generado'}")
    
    # Confirmar ejecución
    try:
        confirm = input("\n¿Continuar? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', 'sí', 's']:
            print("Operación cancelada")
            return
    except KeyboardInterrupt:
        print("\nOperación cancelada")
        return
    
    # Ejecutar optimización
    try:
        optimizer = TimeframeOptimizer(
            strategy_config=strategy,
            timeframes=timeframes,
            backtest_days=args.days,
            generations=args.generations,
            population_size=args.population
        )
        
        results = optimizer.optimize(mode=args.mode)
        
        # Mostrar resultados
        optimizer.print_summary(results)
        
        # Guardar resultados
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = strategy['nombre'].replace(' ', '_').replace('/', '_')
            output_file = f"optimization_{safe_name}_{args.mode}_{timestamp}.json"
        
        try:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n[OK] Resultados guardados en: {output_file}")
        except Exception as e:
            print(f"\n[ERROR] No se pudieron guardar los resultados: {e}")
    
    except KeyboardInterrupt:
        print("\n[INFO] Optimización cancelada por el usuario")
    except Exception as e:
        print(f"\n[ERROR] Error durante la optimización: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()