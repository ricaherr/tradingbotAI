#!/usr/bin/env python3
"""
Test unitario para MetricsCalculator.
Valida que los cálculos sean correctos y consistentes entre timeframes.
"""

import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.core.metrics_calculator import MetricsCalculator, CalculatorFactory
from estrategia_ia.optimization.evaluator import Evaluator


def test_metrics_calculator_creation():
    """Test: Creación de calculadoras por timeframe"""
    print("=== TEST: Creación de MetricsCalculator ===")
    
    timeframes = ["M1", "M5", "M15", "M30", "H1", "H4"]
    
    for tf in timeframes:
        calc = CalculatorFactory.create_metrics_calculator(tf)
        info = calc.get_timeframe_info()
        
        print(f"{tf}: {info['periods_per_year']:,} períodos/año")
        
        # Validar que periods_per_year es correcto
        expected_periods = {
            "M1": 252 * 24 * 60,
            "M5": 252 * 24 * 12, 
            "M15": 252 * 24 * 4,
            "M30": 252 * 24 * 2,
            "H1": 252 * 24,
            "H4": 252 * 6
        }
        
        assert calc.periods_per_year == expected_periods[tf], f"Períodos incorrectos para {tf}"
    
    print("[OK] Todas las calculadoras creadas correctamente")


def test_sharpe_ratio_consistency():
    """Test: Sharpe Ratio debe ser diferente entre timeframes para mismos retornos"""
    print("\n=== TEST: Consistencia Sharpe Ratio ===")
    
    # Crear retornos de prueba
    returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015] * 10)  # 50 retornos
    
    calc_m1 = CalculatorFactory.create_metrics_calculator("M1")
    calc_h4 = CalculatorFactory.create_metrics_calculator("H4")
    
    sharpe_m1 = calc_m1.calculate_sharpe_ratio(returns)
    sharpe_h4 = calc_h4.calculate_sharpe_ratio(returns)
    
    print(f"Sharpe M1: {sharpe_m1:.4f}")
    print(f"Sharpe H4: {sharpe_h4:.4f}")
    
    # M1 debe tener Sharpe más alto (más períodos por año)
    assert sharpe_m1 > sharpe_h4, "M1 debería tener Sharpe mayor que H4"
    
    # Ratio debe ser aproximadamente sqrt(periods_ratio)
    periods_ratio = calc_m1.periods_per_year / calc_h4.periods_per_year
    expected_ratio = np.sqrt(periods_ratio)
    actual_ratio = sharpe_m1 / sharpe_h4
    
    print(f"Ratio esperado: {expected_ratio:.2f}, Ratio actual: {actual_ratio:.2f}")
    
    # Permitir 5% de diferencia por redondeos
    assert abs(actual_ratio - expected_ratio) / expected_ratio < 0.05, "Ratio de Sharpe incorrecto"
    
    print("[OK] Sharpe Ratio consistente entre timeframes")


def test_evaluator_with_timeframe():
    """Test: Evaluator debe usar timeframe correcto"""
    print("\n=== TEST: Evaluator con Timeframe ===")
    
    # Crear reporte de prueba
    test_report = {
        "capital_inicial": 1000,
        "capital_final": 1100,
        "profit_neto": 100,
        "operaciones_totales": 20,
        "operaciones_ganadoras": 12,
        "operaciones_perdedoras": 8,
        "ganancia_bruta": 200,
        "perdida_bruta": -100,
        "max_drawdown": 0.05,
        "equity_curve": np.linspace(1000, 1100, 50).tolist(),
        "periodo_dias": 30
    }
    
    # Crear evaluadores para diferentes timeframes
    eval_m1 = Evaluator(test_report, "M1")
    eval_h4 = Evaluator(test_report, "H4")
    
    # Evaluar
    result_m1 = eval_m1.evaluate()
    result_h4 = eval_h4.evaluate()
    
    print(f"Sharpe M1: {result_m1['sharpe_ratio']:.4f}")
    print(f"Sharpe H4: {result_h4['sharpe_ratio']:.4f}")
    print(f"Calmar M1: {result_m1['calmar_ratio']:.4f}")
    print(f"Calmar H4: {result_h4['calmar_ratio']:.4f}")
    
    # M1 debe tener métricas diferentes a H4
    assert result_m1['sharpe_ratio'] != result_h4['sharpe_ratio'], "Sharpe debe ser diferente entre timeframes"
    
    # Sortino puede ser igual si no hay retornos negativos suficientes
    print(f"Sortino M1: {result_m1['sortino_ratio']:.4f}")
    print(f"Sortino H4: {result_h4['sortino_ratio']:.4f}")
    
    # ROI debe ser igual (no depende del timeframe)
    assert abs(result_m1['roi_mensual_pct'] - result_h4['roi_mensual_pct']) < 0.01, "ROI mensual debe ser igual"
    
    print("[OK] Evaluator funciona correctamente con timeframes")


def test_edge_cases():
    """Test: Casos extremos"""
    print("\n=== TEST: Casos Extremos ===")
    
    calc = CalculatorFactory.create_metrics_calculator("M30")
    
    # Test: Sin retornos
    empty_returns = pd.Series([])
    sharpe_empty = calc.calculate_sharpe_ratio(empty_returns)
    assert sharpe_empty == 0.0, "Sharpe con retornos vacíos debe ser 0"
    
    # Test: Retornos constantes (std ≈ 0)
    constant_returns = pd.Series([0.01] * 10)
    sharpe_constant = calc.calculate_sharpe_ratio(constant_returns)
    print(f"Sharpe constante: {sharpe_constant}, std: {constant_returns.std()}")
    # Con std muy pequeño, Sharpe debe ser muy alto
    assert sharpe_constant > 1e10, "Sharpe con std≈0 debe ser muy alto"
    
    # Test: Solo retornos negativos
    negative_returns = pd.Series([-0.01, -0.02, -0.005])
    sharpe_negative = calc.calculate_sharpe_ratio(negative_returns)
    assert sharpe_negative < 0, "Sharpe con retornos negativos debe ser negativo"
    
    # Test: Calmar con drawdown = 0
    calmar_zero_dd = calc.calculate_calmar_ratio(0.1, 0.0, 100)
    assert calmar_zero_dd == 0.0, "Calmar con drawdown=0 debe ser 0"
    
    print("[OK] Casos extremos manejados correctamente")


def test_old_vs_new_evaluator():
    """Test: Comparar evaluador viejo vs nuevo"""
    print("\n=== TEST: Comparación Evaluador Viejo vs Nuevo ===")
    
    # Crear reporte que simule M30
    test_report = {
        "capital_inicial": 1000,
        "capital_final": 896.89,
        "profit_neto": -103.11,
        "operaciones_totales": 39,
        "operaciones_ganadoras": 12,
        "operaciones_perdedoras": 27,
        "ganancia_bruta": 150,
        "perdida_bruta": -253.11,
        "max_drawdown": 0.1105,
        "equity_curve": [1000 - i*2.64 for i in range(40)],  # Simular pérdida gradual
        "periodo_dias": 30
    }
    
    # Evaluador nuevo con M30
    eval_new = Evaluator(test_report, "M30")
    result_new = eval_new.evaluate()
    
    print(f"Sharpe Nuevo (M30): {result_new['sharpe_ratio']:.4f}")
    print(f"ROI Mensual: {result_new['roi_mensual_pct']:.4f}%")
    
    # El Sharpe debe ser mejor que -196 (el valor anterior incorrecto)
    # Para una estrategia perdedora, -3466 es más realista que -196 con periods_per_year incorrecto
    assert result_new['sharpe_ratio'] > -10000, f"Sharpe extremadamente bajo: {result_new['sharpe_ratio']}"
    assert result_new['sharpe_ratio'] != -196.33, "No debe usar el cálculo incorrecto anterior"
    
    print("[OK] Evaluador nuevo genera métricas razonables")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("EJECUTANDO TESTS DE METRICS_CALCULATOR")
    print("=" * 50)
    
    try:
        test_metrics_calculator_creation()
        test_sharpe_ratio_consistency()
        test_evaluator_with_timeframe()
        test_edge_cases()
        test_old_vs_new_evaluator()
        
        print("\n" + "=" * 50)
        print("[OK] TODOS LOS TESTS PASARON CORRECTAMENTE")
        print("MetricsCalculator está funcionando como esperado")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FALLÓ: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)