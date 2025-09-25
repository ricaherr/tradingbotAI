#!/usr/bin/env python3
"""
Test simple del optimizador para identificar problemas de rendimiento.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from estrategia_ia.optimization.optimizer import GeneticOptimizer
from estrategia_ia.config import ESTRATEGIAS

def test_optimizer_minimal():
    """Test del optimizador con parámetros mínimos."""
    
    # Usar datos existentes
    data_file = "data/datos_historicos/EURUSD_H1.csv"
    
    # Estrategia de prueba
    estrategia = next(e for e in ESTRATEGIAS if e.get("modo") == "backtest")
    
    print("Iniciando optimizador con parámetros mínimos...")
    print(f"Estrategia: {estrategia['nombre']}")
    
    start_time = time.time()
    
    # Optimizador ultra-mínimo
    optimizer = GeneticOptimizer(
        strategy_config=estrategia,
        data_file_path=data_file,
        population_size=2,  # Solo 2 individuos
        generations=1,      # Solo 1 generación
        backtest_period_years=0.05,  # Solo ~18 días
        test_mode=True
    )
    
    print("Ejecutando optimización...")
    result, config = optimizer.run_optimization()
    
    end_time = time.time()
    
    print(f"\nOptimización completada en {end_time - start_time:.2f} segundos")
    
    if result:
        print(f"Mejor fitness: {result.get('sharpe_ratio', 0):.4f}")
        print(f"Mejor configuración: {config}")
    else:
        print("Optimización falló")

if __name__ == "__main__":
    test_optimizer_minimal()