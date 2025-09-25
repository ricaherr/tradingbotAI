#!/usr/bin/env python3
"""
Script para debuggear problemas de rendimiento en el sistema.
"""

import sys
import os
import time
import cProfile
import pstats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from estrategia_ia.backtesting.backtester import run_backtest
from estrategia_ia.config import ESTRATEGIAS

def test_single_backtest():
    """Test de un solo backtest para medir rendimiento."""
    
    # Usar datos existentes
    data_file = "data/datos_historicos/EURUSD_H1.csv"
    
    # Estrategia simple
    estrategia = {
        "nombre": "Test Performance",
        "usar_filtro_tendencia": True,
        "ema_reversion": 20,
        "ema_tendencia": 100
    }
    
    print("Iniciando backtest de rendimiento...")
    start_time = time.time()
    
    # Ejecutar con período muy corto
    result = run_backtest(
        data_file,
        estrategia,
        show_plot=False,
        verbose=True,
        backtest_period_years=0.1  # Solo ~36 días
    )
    
    end_time = time.time()
    
    print(f"\nBacktest completado en {end_time - start_time:.2f} segundos")
    
    if result:
        print(f"Operaciones totales: {result.get('operaciones_totales', 0)}")
        print(f"Profit neto: ${result.get('profit_neto', 0):.2f}")
    else:
        print("Backtest falló - resultado None")

def profile_backtest():
    """Ejecutar backtest con profiling para identificar cuellos de botella."""
    
    print("Ejecutando backtest con profiling...")
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    test_single_backtest()
    
    profiler.disable()
    
    # Mostrar estadísticas
    stats = pstats.Stats(profiler)
    print("\n" + "="*60)
    print("TOP 10 FUNCIONES MÁS LENTAS:")
    print("="*60)
    stats.sort_stats('cumulative').print_stats(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--profile":
        profile_backtest()
    else:
        test_single_backtest()