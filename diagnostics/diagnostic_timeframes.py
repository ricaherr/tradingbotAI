#!/usr/bin/env python3
"""
AUDITORÍA DE VARIABLES DEPENDIENTES DEL TIMEFRAME
Identifica todas las variables que deben cambiar según el timeframe
y propone soluciones dinámicas.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def analyze_timeframe_dependencies():
    """Analiza todas las dependencias del timeframe en el sistema"""
    
    print("ANÁLISIS DE VARIABLES DEPENDIENTES DEL TIMEFRAME")
    print("=" * 60)
    
    # 1. EVALUATOR - Cálculos de métricas
    print("\n1. EVALUATOR (optimization/evaluator.py)")
    print("   PROBLEMA ACTUAL:")
    print("   - periods_per_year = 252 (fijo para días)")
    print("   - No considera que M1 tiene más períodos que H4")
    print("   - Sharpe, Sortino, Calmar usan el mismo factor")
    
    print("\n   VARIABLES QUE DEBEN SER DINÁMICAS:")
    timeframe_periods = {
        "M1": 252 * 24 * 60,      # 362,880 períodos/año
        "M5": 252 * 24 * 12,      # 72,576 períodos/año  
        "M15": 252 * 24 * 4,      # 24,192 períodos/año
        "M30": 252 * 24 * 2,      # 12,096 períodos/año
        "H1": 252 * 24,           # 6,048 períodos/año
        "H4": 252 * 6,            # 1,512 períodos/año
    }
    
    for tf, periods in timeframe_periods.items():
        print(f"   - {tf}: {periods:,} períodos/año")
    
    # 2. DATA_MANAGER - Cantidad de velas
    print("\n2. DATA_MANAGER (core/data_manager.py)")
    print("   PROBLEMA ACTUAL:")
    print("   - velas_needed está en config pero no se usa dinámicamente")
    print("   - min_velas no se ajusta por timeframe")
    
    print("\n   VARIABLES QUE DEBEN SER DINÁMICAS:")
    print("   - num_velas: Más velas para timeframes menores")
    print("   - min_velas: Mínimo estadísticamente válido por TF")
    print("   - max_age_days: Timeframes menores necesitan datos más frescos")
    
    # 3. ESTRATEGIAS - Parámetros técnicos
    print("\n3. ESTRATEGIAS (core/strategies.py)")
    print("   PROBLEMA POTENCIAL:")
    print("   - Períodos de EMA pueden ser inadecuados para diferentes TF")
    print("   - ATR lookback period fijo")
    print("   - Thresholds de distancia no escalados")
    
    print("\n   VARIABLES QUE DEBEN SER DINÁMICAS:")
    print("   - EMA periods: Ajustar según volatilidad del TF")
    print("   - ATR lookback: Más períodos para TF menores")
    print("   - Distance thresholds: Escalar por volatilidad típica")
    
    # 4. RISK_MANAGER - Gestión de riesgo
    print("\n4. RISK_MANAGER")
    print("   PROBLEMA POTENCIAL:")
    print("   - ATR factors fijos para todos los timeframes")
    print("   - Trailing stop distances no escaladas")
    
    print("\n   VARIABLES QUE DEBEN SER DINÁMICAS:")
    print("   - ATR_FACTOR: Diferentes por volatilidad del TF")
    print("   - TRAILING_DISTANCE: Ajustada por ruido del TF")
    
    # 5. BACKTESTER - Configuración de pruebas
    print("\n5. BACKTESTER")
    print("   PROBLEMA POTENCIAL:")
    print("   - backtest_period_years no considera densidad de datos")
    print("   - window_size fijo en data_source")
    
    print("\n   VARIABLES QUE DEBEN SER DINÁMICAS:")
    print("   - window_size: Más velas para TF menores")
    print("   - min_trades_required: Ajustado por frecuencia esperada")

def propose_dynamic_solution():
    """Propone una solución dinámica para manejar timeframes"""
    
    print("\n" + "=" * 60)
    print("SOLUCIÓN PROPUESTA: TIMEFRAME_CONTEXT")
    print("=" * 60)
    
    solution = '''
# Nuevo archivo: src/estrategia_ia/core/timeframe_context.py

class TimeframeContext:
    """
    Contexto dinámico que ajusta variables según el timeframe activo.
    Centraliza toda la lógica dependiente del timeframe.
    """
    
    TIMEFRAME_SPECS = {
        "M1": {
            "minutes": 1,
            "periods_per_day": 1440,
            "periods_per_year": 252 * 1440,
            "typical_volatility": 0.0001,
            "noise_level": "high",
            "data_freshness_hours": 2,
            "min_backtest_days": 30,
            "optimal_ema_base": 20,
            "atr_lookback": 14,
            "window_size": 500
        },
        "M5": {
            "minutes": 5,
            "periods_per_day": 288,
            "periods_per_year": 252 * 288,
            "typical_volatility": 0.0002,
            "noise_level": "medium-high",
            "data_freshness_hours": 6,
            "min_backtest_days": 60,
            "optimal_ema_base": 15,
            "atr_lookback": 12,
            "window_size": 400
        },
        "M15": {
            "minutes": 15,
            "periods_per_day": 96,
            "periods_per_year": 252 * 96,
            "typical_volatility": 0.0003,
            "noise_level": "medium",
            "data_freshness_hours": 12,
            "min_backtest_days": 90,
            "optimal_ema_base": 12,
            "atr_lookback": 10,
            "window_size": 300
        },
        "M30": {
            "minutes": 30,
            "periods_per_day": 48,
            "periods_per_year": 252 * 48,
            "typical_volatility": 0.0004,
            "noise_level": "medium-low",
            "data_freshness_hours": 24,
            "min_backtest_days": 120,
            "optimal_ema_base": 10,
            "atr_lookback": 8,
            "window_size": 250
        },
        "H1": {
            "minutes": 60,
            "periods_per_day": 24,
            "periods_per_year": 252 * 24,
            "typical_volatility": 0.0006,
            "noise_level": "low",
            "data_freshness_hours": 48,
            "min_backtest_days": 180,
            "optimal_ema_base": 8,
            "atr_lookback": 6,
            "window_size": 200
        },
        "H4": {
            "minutes": 240,
            "periods_per_day": 6,
            "periods_per_year": 252 * 6,
            "typical_volatility": 0.0010,
            "noise_level": "very-low",
            "data_freshness_hours": 96,
            "min_backtest_days": 365,
            "optimal_ema_base": 6,
            "atr_lookback": 4,
            "window_size": 150
        }
    }
    
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        self.specs = self.TIMEFRAME_SPECS[timeframe]
    
    def get_periods_per_year(self):
        return self.specs["periods_per_year"]
    
    def get_optimal_ema_period(self, base_period: int):
        """Ajusta período EMA según timeframe"""
        factor = self.specs["optimal_ema_base"] / 20  # 20 es base para H1
        return max(2, int(base_period * factor))
    
    def get_atr_lookback(self):
        return self.specs["atr_lookback"]
    
    def get_distance_threshold_multiplier(self):
        """Multiplica thresholds de distancia por volatilidad típica"""
        return self.specs["typical_volatility"] / 0.0006  # 0.0006 es base para H1
    
    def get_window_size(self):
        return self.specs["window_size"]
    
    def get_min_backtest_days(self):
        return self.specs["min_backtest_days"]
    
    def get_data_freshness_hours(self):
        return self.specs["data_freshness_hours"]

# USO EN EVALUATOR:
def _calculate_sharpe_ratio(self, risk_free_rate=0):
    context = TimeframeContext(self.timeframe)  # Necesita timeframe
    periods_per_year = context.get_periods_per_year()
    # ... resto del cálculo

# USO EN ESTRATEGIAS:
def calculate_ema(self, data, period):
    context = TimeframeContext(self.current_timeframe)
    adjusted_period = context.get_optimal_ema_period(period)
    # ... cálculo con período ajustado
    '''
    
    print(solution)

def identify_critical_fixes():
    """Identifica las correcciones más críticas"""
    
    print("\n" + "=" * 60)
    print("CORRECCIONES CRÍTICAS INMEDIATAS")
    print("=" * 60)
    
    fixes = [
        {
            "archivo": "optimization/evaluator.py",
            "problema": "periods_per_year fijo en 252",
            "solucion": "Usar TimeframeContext.get_periods_per_year()",
            "impacto": "CRÍTICO - Sharpe/Sortino/Calmar incorrectos",
            "prioridad": 1
        },
        {
            "archivo": "core/data_manager.py", 
            "problema": "velas_needed no dinámico",
            "solucion": "Usar TimeframeContext.get_window_size()",
            "impacto": "ALTO - Datos insuficientes para TF menores",
            "prioridad": 2
        },
        {
            "archivo": "core/strategies.py",
            "problema": "Períodos EMA fijos",
            "solucion": "Usar TimeframeContext.get_optimal_ema_period()",
            "impacto": "MEDIO - Estrategias subóptimas",
            "prioridad": 3
        },
        {
            "archivo": "core/data_source.py",
            "problema": "window_size fijo en 500",
            "solucion": "Usar TimeframeContext.get_window_size()",
            "impacto": "MEDIO - Memoria y rendimiento",
            "prioridad": 4
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n{i}. {fix['archivo']}")
        print(f"   Problema: {fix['problema']}")
        print(f"   Solución: {fix['solucion']}")
        print(f"   Impacto: {fix['impacto']}")
        print(f"   Prioridad: {fix['prioridad']}")

def main():
    analyze_timeframe_dependencies()
    propose_dynamic_solution()
    identify_critical_fixes()
    
    print("\n" + "=" * 60)
    print("RECOMENDACIÓN")
    print("=" * 60)
    print("1. Implementar TimeframeContext inmediatamente")
    print("2. Corregir Evaluator (prioridad 1)")
    print("3. Actualizar todos los componentes gradualmente")
    print("4. Agregar tests para validar consistencia entre TF")

if __name__ == "__main__":
    main()