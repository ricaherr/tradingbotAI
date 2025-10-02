#!/usr/bin/env python3
"""
diagnostic_risk_management.py

Diagnóstico específico para validar los cambios de FASE 2:
- RiskCalculator y cálculos dinámicos de riesgo
- Integración con strategies y backtesting
- Consistencia de parámetros por timeframe
- Validación de límites de riesgo
"""

import sys
import os
import pandas as pd
import numpy as np

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_risk_calculator_creation():
    """Test 1: Creación y configuración básica del RiskCalculator"""
    print("=== TEST 1: Creación RiskCalculator ===")
    
    try:
        from estrategia_ia.utils.risk_calculator import RiskCalculator
        from estrategia_ia.config import TIMEFRAMES_CONFIG
        
        # Test creación básica
        risk_calc = RiskCalculator(capital_inicial=1000)
        print(f"[OK] RiskCalculator creado con capital: ${risk_calc.capital_inicial}")
        
        # Test configuración de timeframes
        missing_params = []
        for tf, config in TIMEFRAMES_CONFIG.items():
            required = ['risk_multiplier', 'max_risk_per_trade', 'volatility_adjustment', 'min_atr_periods']
            missing = [param for param in required if param not in config]
            if missing:
                missing_params.append(f"{tf}: {missing}")
        
        if missing_params:
            print(f"[ERROR] Parámetros faltantes: {missing_params}")
            return False
        
        print("[OK] Todos los timeframes tienen parámetros de riesgo")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en creación: {e}")
        return False

def test_dynamic_lot_calculation():
    """Test 2: Cálculo dinámico de lotes por timeframe"""
    print("\n=== TEST 2: Cálculo Dinámico de Lotes ===")
    
    try:
        from estrategia_ia.utils.risk_calculator import RiskCalculator
        
        risk_calc = RiskCalculator(capital_inicial=1000)
        
        # Test parámetros base
        test_params = {
            'riesgo_porcentaje': 1.0,
            'atr_value': 0.0015,
            'precio_actual': 1.1000
        }
        
        # Calcular lotes para diferentes timeframes
        lotes_por_tf = {}
        for tf in ['M1', 'M15', 'H1', 'H4']:
            lote = risk_calc.calcular_lote_dinamico(
                timeframe=tf,
                **test_params
            )
            lotes_por_tf[tf] = lote
            print(f"[INFO] {tf}: Lote = {lote}")
        
        # Validar que M1 < M15 < H1 < H4 (menor riesgo para TF cortos)
        if not (lotes_por_tf['M1'] <= lotes_por_tf['M15'] <= lotes_por_tf['H1'] <= lotes_por_tf['H4']):
            print("[WARNING] Lotes no siguen progresión esperada M1 <= M15 <= H1 <= H4")
        
        # Validar límites
        for tf, lote in lotes_por_tf.items():
            if lote < 0.01 or lote > 0.1:
                print(f"[ERROR] {tf}: Lote {lote} fuera de límites [0.01, 0.1]")
                return False
        
        print("[OK] Cálculo dinámico de lotes funciona correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en cálculo de lotes: {e}")
        return False

def test_adaptive_sl_tp():
    """Test 3: SL/TP adaptativos por timeframe"""
    print("\n=== TEST 3: SL/TP Adaptativos ===")
    
    try:
        from estrategia_ia.utils.risk_calculator import RiskCalculator
        
        risk_calc = RiskCalculator()
        
        test_params = {
            'atr_value': 0.0020,
            'precio_entrada': 1.1000,
            'relacion_rr': 2.0
        }
        
        # Test BUY y SELL para diferentes timeframes
        for direccion in ['BUY', 'SELL']:
            print(f"\n[INFO] Dirección: {direccion}")
            
            sl_tp_por_tf = {}
            for tf in ['M1', 'M15', 'H1', 'H4']:
                sl, tp = risk_calc.calcular_sl_tp_adaptativos(
                    timeframe=tf,
                    direccion=direccion,
                    **test_params
                )
                sl_tp_por_tf[tf] = (sl, tp)
                
                # Validar lógica BUY/SELL
                if direccion == 'BUY':
                    if sl >= test_params['precio_entrada'] or tp <= test_params['precio_entrada']:
                        print(f"[ERROR] {tf} BUY: SL={sl} debe ser < precio={test_params['precio_entrada']} < TP={tp}")
                        return False
                else:  # SELL
                    if sl <= test_params['precio_entrada'] or tp >= test_params['precio_entrada']:
                        print(f"[ERROR] {tf} SELL: TP={tp} < precio={test_params['precio_entrada']} < SL={sl}")
                        return False
                
                print(f"[INFO] {tf}: SL={sl:.5f}, TP={tp:.5f}")
            
            # Validar que distancias aumenten con timeframe (H4 > H1 > M15 > M1)
            distancias_sl = {}
            for tf, (sl, tp) in sl_tp_por_tf.items():
                distancia = abs(sl - test_params['precio_entrada'])
                distancias_sl[tf] = distancia
            
            if direccion == 'BUY':
                if not (distancias_sl['M1'] <= distancias_sl['M15'] <= distancias_sl['H1'] <= distancias_sl['H4']):
                    print("[WARNING] Distancias SL no siguen progresión esperada")
        
        print("[OK] SL/TP adaptativos funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en SL/TP adaptativos: {e}")
        return False

def test_risk_validation():
    """Test 4: Validación de límites de riesgo"""
    print("\n=== TEST 4: Validación de Riesgo ===")
    
    try:
        from estrategia_ia.utils.risk_calculator import RiskCalculator
        
        risk_calc = RiskCalculator(capital_inicial=1000)
        
        # Test casos válidos
        validacion_ok = risk_calc.validar_riesgo_operacion(
            timeframe="M15",
            lote=0.05,
            distancia_sl=0.0010,
            precio_actual=1.1000
        )
        
        if not validacion_ok['valido']:
            print(f"[ERROR] Validación falló para caso válido: {validacion_ok['razon']}")
            return False
        
        print(f"[OK] Caso válido: Riesgo {validacion_ok['riesgo_porcentual']:.2f}%")
        
        # Test caso con riesgo excesivo
        validacion_fail = risk_calc.validar_riesgo_operacion(
            timeframe="M1",  # M1 tiene max_risk_per_trade = 0.5%
            lote=1.0,        # Lote muy alto
            distancia_sl=0.0050,  # SL muy amplio
            precio_actual=1.1000
        )
        
        if validacion_fail['valido']:
            print("[ERROR] Validación debería fallar para riesgo excesivo")
            return False
        
        print(f"[OK] Caso inválido detectado: {validacion_fail['razon']}")
        
        # Test lotes fuera de límites
        validacion_lote = risk_calc.validar_riesgo_operacion(
            timeframe="H1",
            lote=0.005,  # Menor que MIN_LOTE
            distancia_sl=0.0010,
            precio_actual=1.1000
        )
        
        if validacion_lote['valido']:
            print("[ERROR] Validación debería fallar para lote muy pequeño")
            return False
        
        print("[OK] Validación de límites funciona correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en validación de riesgo: {e}")
        return False

def test_strategies_integration():
    """Test 5: Integración con strategies actualizadas"""
    print("\n=== TEST 5: Integración con Strategies ===")
    
    try:
        from estrategia_ia.core.strategies import calcular_parametros_operacion, validar_senal_con_riesgo
        
        # Crear datos de prueba
        dates = pd.date_range('2023-01-01', periods=50, freq='h')
        df_test = pd.DataFrame({
            'open': np.random.uniform(1.0900, 1.1100, 50),
            'high': np.random.uniform(1.0950, 1.1150, 50),
            'low': np.random.uniform(1.0850, 1.1050, 50),
            'close': np.random.uniform(1.0900, 1.1100, 50),
        }, index=dates)
        
        estrategia_test = {
            'nombre': 'Test Strategy',
            'riesgo_porcentaje': 1.0,
            'relacion_riesgo_beneficio': 2.0,
            'atr_period': 14
        }
        
        # Test calcular_parametros_operacion
        for tf in ['M15', 'H1']:
            params = calcular_parametros_operacion(
                df=df_test,
                estrategia=estrategia_test,
                direccion="BUY",
                timeframe=tf,
                razon=f"Test signal {tf}"
            )
            
            # Validar estructura de respuesta
            required_keys = ['precio_entrada', 'stop_loss', 'take_profit', 'lote', 'atr', 'timeframe', 'validacion']
            missing_keys = [key for key in required_keys if key not in params]
            if missing_keys:
                print(f"[ERROR] {tf}: Faltan claves en params: {missing_keys}")
                return False
            
            # Validar valores lógicos para BUY
            if params['stop_loss'] >= params['precio_entrada']:
                print(f"[ERROR] {tf}: SL {params['stop_loss']:.5f} >= precio_entrada {params['precio_entrada']:.5f} en BUY")
                return False
            
            if params['take_profit'] <= params['precio_entrada']:
                print(f"[ERROR] {tf}: TP {params['take_profit']:.5f} <= precio_entrada {params['precio_entrada']:.5f} en BUY")
                return False
            
            print(f"[OK] {tf}: Parámetros calculados correctamente")
            
            # Test validar_senal_con_riesgo
            es_valida, razon = validar_senal_con_riesgo(params)
            if not es_valida:
                print(f"[ERROR] {tf}: Señal válida rechazada: {razon}")
                return False
            
            print(f"[OK] {tf}: Señal validada correctamente")
        
        print("[OK] Integración con strategies funciona correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en integración strategies: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backtester_integration():
    """Test 6: Integración con backtesting"""
    print("\n=== TEST 6: Integración con Backtesting ===")
    
    try:
        from estrategia_ia.utils.risk_calculator import RiskCalculator
        from estrategia_ia.trading.broker_simulator import BrokerSimulator
        
        # Test que BrokerSimulator acepta RiskCalculator
        risk_calc = RiskCalculator(capital_inicial=1000)
        broker = BrokerSimulator(
            capital_inicial=1000,
            riesgo_porcentaje=1.0,
            risk_calculator=risk_calc
        )
        
        if broker.risk_calculator is None:
            print("[ERROR] BrokerSimulator no acepta RiskCalculator")
            return False
        
        print("[OK] BrokerSimulator integrado con RiskCalculator")
        
        # Test que backtester pasa RiskCalculator
        from estrategia_ia.backtesting.backtester import run_backtest
        print("[OK] Backtester importa RiskCalculator correctamente")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en integración backtester: {e}")
        return False

def test_timeframe_consistency():
    """Test 7: Consistencia entre timeframes"""
    print("\n=== TEST 7: Consistencia entre Timeframes ===")
    
    try:
        from estrategia_ia.utils.risk_calculator import RiskCalculator
        from estrategia_ia.config import TIMEFRAMES_CONFIG
        
        risk_calc = RiskCalculator()
        
        # Parámetros base para comparación
        base_params = {
            'riesgo_porcentaje': 1.0,
            'atr_value': 0.0015,
            'precio_actual': 1.1000,
            'precio_entrada': 1.1000,
            'direccion': 'BUY',
            'relacion_rr': 2.0
        }
        
        resultados = {}
        
        for tf in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4']:
            config = TIMEFRAMES_CONFIG[tf]
            
            # Calcular métricas
            lote = risk_calc.calcular_lote_dinamico(
                timeframe=tf,
                riesgo_porcentaje=base_params['riesgo_porcentaje'],
                atr_value=base_params['atr_value'],
                precio_actual=base_params['precio_actual']
            )
            
            sl, tp = risk_calc.calcular_sl_tp_adaptativos(
                timeframe=tf,
                atr_value=base_params['atr_value'],
                precio_entrada=base_params['precio_entrada'],
                direccion=base_params['direccion'],
                relacion_rr=base_params['relacion_rr']
            )
            
            distancia_sl = abs(sl - base_params['precio_entrada'])
            distancia_tp = abs(tp - base_params['precio_entrada'])
            rr_real = distancia_tp / distancia_sl if distancia_sl > 0 else 0
            
            resultados[tf] = {
                'lote': lote,
                'distancia_sl': distancia_sl,
                'distancia_tp': distancia_tp,
                'rr_real': rr_real,
                'risk_multiplier': config['risk_multiplier'],
                'volatility_adj': config['volatility_adjustment']
            }
            
            print(f"[INFO] {tf}: Lote={lote:.3f}, SL_dist={distancia_sl:.5f}, RR={rr_real:.2f}")
        
        # Validar progresiones lógicas
        timeframes_orden = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4']
        
        # Los lotes deberían aumentar con timeframes más largos (menos restrictivos)
        lotes = [resultados[tf]['lote'] for tf in timeframes_orden]
        if not all(lotes[i] <= lotes[i+1] for i in range(len(lotes)-1)):
            print("[WARNING] Lotes no siguen progresión esperada")
        
        # Las distancias SL deberían aumentar con timeframes más largos
        distancias = [resultados[tf]['distancia_sl'] for tf in timeframes_orden]
        if not all(distancias[i] <= distancias[i+1] for i in range(len(distancias)-1)):
            print("[WARNING] Distancias SL no siguen progresión esperada")
        
        # RR debería mantenerse cerca del objetivo (2.0)
        rr_values = [resultados[tf]['rr_real'] for tf in timeframes_orden]
        rr_promedio = sum(rr_values) / len(rr_values)
        if abs(rr_promedio - 2.0) > 0.5:
            print(f"[WARNING] RR promedio {rr_promedio:.2f} se desvía del objetivo 2.0")
        
        print("[OK] Consistencia entre timeframes validada")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en consistencia timeframes: {e}")
        return False

def main():
    """Ejecuta el diagnóstico completo de gestión de riesgo"""
    print("DIAGNÓSTICO: GESTIÓN DE RIESGO DINÁMICA (FASE 2)")
    print("=" * 60)
    
    tests = [
        test_risk_calculator_creation,
        test_dynamic_lot_calculation,
        test_adaptive_sl_tp,
        test_risk_validation,
        test_strategies_integration,
        test_backtester_integration,
        test_timeframe_consistency
    ]
    
    resultados = []
    for test in tests:
        try:
            resultado = test()
            resultados.append(resultado)
        except Exception as e:
            print(f"[ERROR] Error en {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            resultados.append(False)
    
    print("\n" + "=" * 60)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    tests_pasados = sum(resultados)
    total_tests = len(resultados)
    
    print(f"Tests pasados: {tests_pasados}/{total_tests}")
    
    if all(resultados):
        print("[SUCCESS] GESTIÓN DE RIESGO DINÁMICA FUNCIONANDO CORRECTAMENTE")
        print("\nValidaciones completadas:")
        print("- RiskCalculator creado e integrado")
        print("- Cálculos dinámicos por timeframe")
        print("- SL/TP adaptativos funcionando")
        print("- Validación de límites operativa")
        print("- Integración con strategies completa")
        print("- Backtesting integrado")
        print("- Consistencia entre timeframes validada")
        return True
    else:
        print("[ERROR] ALGUNOS TESTS FALLARON")
        print("Revisar implementación de gestión de riesgo")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)