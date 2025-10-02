#!/usr/bin/env python3
"""
Herramienta de diagnóstico para verificar que el sistema de optimización funciona correctamente.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from estrategia_ia.config import ESTRATEGIAS
from estrategia_ia.backtesting.backtester import run_backtest
from estrategia_ia.optimization.evaluator import Evaluator
from estrategia_ia.core.data_manager import asegurar_datos_historicos

def test_strategy_basic(strategy_name, timeframe_code=16385, num_velas=800):
    """Prueba básica de una estrategia con parámetros fijos."""
    
    print(f"\n=== DIAGNÓSTICO: {strategy_name} ===")
    
    # Buscar estrategia
    strategy = None
    for s in ESTRATEGIAS:
        if strategy_name.lower() in s["nombre"].lower():
            strategy = s.copy()
            break
    
    if not strategy:
        print(f"❌ Estrategia '{strategy_name}' no encontrada")
        return False
    
    # Obtener datos
    print("📊 Obteniendo datos...")
    data_file = asegurar_datos_historicos(
        simbolo="EURUSD",
        timeframe=timeframe_code,
        num_velas=num_velas,
        min_velas=num_velas // 2,
        max_age_days=7
    )
    
    if not data_file:
        print("❌ No se pudieron obtener datos")
        return False
    
    print(f"✅ Datos obtenidos: {data_file}")
    
    # Ejecutar backtest con parámetros base
    print("🔄 Ejecutando backtest...")
    
    try:
        report = run_backtest(
            data_file,
            strategy,
            show_plot=False,
            verbose=False,
            backtest_period_years=0.25  # 3 meses
        )
        
        if not report:
            print("❌ Backtest falló - reporte vacío")
            return False
        
        print(f"✅ Backtest completado")
        print(f"   Operaciones totales: {report.get('operaciones_totales', 0)}")
        print(f"   Capital inicial: ${report.get('capital_inicial', 0):,.2f}")
        print(f"   Capital final: ${report.get('capital_final', 0):,.2f}")
        print(f"   Profit neto: ${report.get('profit_neto', 0):,.2f}")
        
        # Evaluar resultados
        evaluator = Evaluator(report)
        evaluation = evaluator.evaluate()
        
        print(f"   ROI mensual: {evaluation.get('roi_mensual_pct', 0):.2f}%")
        print(f"   Sharpe ratio: {evaluation.get('sharpe_ratio', 0):.2f}")
        print(f"   Win rate: {evaluation.get('win_rate_pct', 0):.1f}%")
        print(f"   Viable: {'SÍ' if evaluation.get('viable', False) else 'NO'}")
        
        return evaluation.get('roi_mensual_pct', 0) != 0
        
    except Exception as e:
        print(f"❌ Error en backtest: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parameter_variation(strategy_name):
    """Prueba variaciones de parámetros para ver si afectan los resultados."""
    
    print(f"\n=== PRUEBA DE VARIACIÓN DE PARÁMETROS: {strategy_name} ===")
    
    # Buscar estrategia
    strategy = None
    for s in ESTRATEGIAS:
        if strategy_name.lower() in s["nombre"].lower():
            strategy = s.copy()
            break
    
    if not strategy:
        print(f"❌ Estrategia '{strategy_name}' no encontrada")
        return
    
    # Obtener datos
    data_file = asegurar_datos_historicos(
        simbolo="EURUSD",
        timeframe=16385,  # H1
        num_velas=800,
        min_velas=400,
        max_age_days=7
    )
    
    if not data_file:
        print("❌ No se pudieron obtener datos")
        return
    
    # Probar diferentes configuraciones
    test_configs = []
    
    if "Reversión" in strategy_name:
        test_configs = [
            {"ema_reversion": 14, "desviacion_threshold": 1.0, "riesgo_porcentaje": 1.0},
            {"ema_reversion": 20, "desviacion_threshold": 1.5, "riesgo_porcentaje": 2.0},
            {"ema_reversion": 26, "desviacion_threshold": 2.0, "riesgo_porcentaje": 2.5},
        ]
    elif "Rompimiento" in strategy_name:
        test_configs = [
            {"ema_period": 15, "riesgo_porcentaje": 1.0, "relacion_riesgo_beneficio": 1.5},
            {"ema_period": 20, "riesgo_porcentaje": 2.0, "relacion_riesgo_beneficio": 2.0},
            {"ema_period": 25, "riesgo_porcentaje": 2.5, "relacion_riesgo_beneficio": 2.5},
        ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n--- Configuración {i}: {config} ---")
        
        test_strategy = strategy.copy()
        test_strategy.update(config)
        
        try:
            report = run_backtest(
                data_file,
                test_strategy,
                show_plot=False,
                verbose=False,
                backtest_period_years=0.25
            )
            
            if report:
                evaluator = Evaluator(report)
                evaluation = evaluator.evaluate()
                
                print(f"   Operaciones: {report.get('operaciones_totales', 0)}")
                print(f"   ROI mensual: {evaluation.get('roi_mensual_pct', 0):.2f}%")
                print(f"   Profit neto: ${report.get('profit_neto', 0):,.2f}")
            else:
                print("   ❌ Backtest falló")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🔧 DIAGNÓSTICO DEL SISTEMA DE OPTIMIZACIÓN")
    print("=" * 50)
    
    # Probar estrategias conocidas
    strategies_to_test = [
        ("Rompimiento", "Estrategia que debería funcionar"),
        ("Reversión", "Estrategia problemática")
    ]
    
    results = {}
    
    for strategy_name, description in strategies_to_test:
        print(f"\n🧪 Probando {description}")
        results[strategy_name] = test_strategy_basic(strategy_name)
        
        # Si la estrategia básica funciona, probar variaciones
        if results[strategy_name]:
            test_parameter_variation(strategy_name)
    
    # Resumen
    print(f"\n{'='*50}")
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print(f"{'='*50}")
    
    for strategy_name, works in results.items():
        status = "✅ FUNCIONA" if works else "❌ NO FUNCIONA"
        print(f"{strategy_name}: {status}")
    
    if not any(results.values()):
        print("\n🚨 PROBLEMA CRÍTICO: Ninguna estrategia genera resultados")
        print("   Posibles causas:")
        print("   - Datos históricos corruptos")
        print("   - Error en lógica de backtesting")
        print("   - Configuración de parámetros incorrecta")
    elif results.get("Rompimiento", False) and not results.get("Reversión", False):
        print("\n✅ Sistema funciona correctamente")
        print("❌ Estrategia 'Reversión a la Media' tiene problemas específicos")
    
    print(f"\nDiagnóstico completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()