"""
Tests unitarios para RiskCalculator
Parte del testing exhaustivo de FASE 3
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.utils.risk_calculator import RiskCalculator
from estrategia_ia.config import TIMEFRAMES_CONFIG


class TestRiskCalculator(unittest.TestCase):
    """Tests unitarios para RiskCalculator"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.risk_calc = RiskCalculator(capital_inicial=1000)
        self.test_params = {
            'timeframe': 'M15',
            'riesgo_porcentaje': 1.0,
            'atr_value': 0.0015,
            'precio_actual': 1.1000,
            'precio_entrada': 1.1000,
            'direccion': 'BUY',
            'relacion_rr': 2.0
        }
    
    def test_initialization(self):
        """Test inicialización correcta"""
        self.assertEqual(float(self.risk_calc.capital_inicial), 1000)
        self.assertEqual(float(self.risk_calc.min_lote), 0.01)
        self.assertEqual(float(self.risk_calc.max_lote), 0.1)
    
    def test_calcular_lote_dinamico_basic(self):
        """Test cálculo básico de lote dinámico"""
        lote = self.risk_calc.calcular_lote_dinamico(
            timeframe=self.test_params['timeframe'],
            riesgo_porcentaje=self.test_params['riesgo_porcentaje'],
            atr_value=self.test_params['atr_value'],
            precio_actual=self.test_params['precio_actual']
        )
        
        # Verificar que el lote está en rango válido
        self.assertGreaterEqual(lote, 0.01)
        self.assertLessEqual(lote, 0.1)
        self.assertIsInstance(lote, float)
    
    def test_calcular_lote_dinamico_timeframes(self):
        """Test que diferentes timeframes producen diferentes lotes"""
        lotes = {}
        
        for tf in ['M1', 'M15', 'H1', 'H4']:
            lote = self.risk_calc.calcular_lote_dinamico(
                timeframe=tf,
                riesgo_porcentaje=1.0,
                atr_value=0.0015,
                precio_actual=1.1000
            )
            lotes[tf] = lote
        
        # Verificar que M1 <= M15 <= H1 <= H4 (progresión de riesgo)
        self.assertLessEqual(lotes['M1'], lotes['M15'])
        self.assertLessEqual(lotes['M15'], lotes['H1'])
        self.assertLessEqual(lotes['H1'], lotes['H4'])
    
    def test_calcular_sl_tp_adaptativos_buy(self):
        """Test SL/TP para operaciones BUY"""
        sl, tp = self.risk_calc.calcular_sl_tp_adaptativos(
            timeframe=self.test_params['timeframe'],
            atr_value=self.test_params['atr_value'],
            precio_entrada=self.test_params['precio_entrada'],
            direccion='BUY',
            relacion_rr=self.test_params['relacion_rr']
        )
        
        # Para BUY: SL < precio_entrada < TP
        self.assertLess(sl, self.test_params['precio_entrada'])
        self.assertGreater(tp, self.test_params['precio_entrada'])
        
        # Verificar relación riesgo/beneficio aproximada
        distancia_sl = abs(self.test_params['precio_entrada'] - sl)
        distancia_tp = abs(tp - self.test_params['precio_entrada'])
        rr_real = distancia_tp / distancia_sl
        
        self.assertAlmostEqual(rr_real, self.test_params['relacion_rr'], places=1)
    
    def test_calcular_sl_tp_adaptativos_sell(self):
        """Test SL/TP para operaciones SELL"""
        sl, tp = self.risk_calc.calcular_sl_tp_adaptativos(
            timeframe=self.test_params['timeframe'],
            atr_value=self.test_params['atr_value'],
            precio_entrada=self.test_params['precio_entrada'],
            direccion='SELL',
            relacion_rr=self.test_params['relacion_rr']
        )
        
        # Para SELL: TP < precio_entrada < SL
        self.assertLess(tp, self.test_params['precio_entrada'])
        self.assertGreater(sl, self.test_params['precio_entrada'])
    
    def test_validar_riesgo_operacion_valida(self):
        """Test validación de operación válida"""
        validacion = self.risk_calc.validar_riesgo_operacion(
            timeframe='M15',
            lote=0.05,
            distancia_sl=0.0010,
            precio_actual=1.1000
        )
        
        self.assertTrue(validacion['valido'])
        self.assertIn('riesgo_porcentual', validacion)
        self.assertIn('lote_validado', validacion)
    
    def test_validar_riesgo_operacion_invalida(self):
        """Test validación de operación inválida"""
        # Lote muy alto
        validacion = self.risk_calc.validar_riesgo_operacion(
            timeframe='M1',  # M1 tiene max_risk_per_trade = 0.5%
            lote=1.0,        # Lote muy alto
            distancia_sl=0.0050,
            precio_actual=1.1000
        )
        
        self.assertFalse(validacion['valido'])
        self.assertIn('razon', validacion)
    
    def test_calcular_atr(self):
        """Test cálculo de ATR"""
        # Crear datos de prueba
        dates = pd.date_range('2023-01-01', periods=20, freq='h')
        df_test = pd.DataFrame({
            'high': np.random.uniform(1.0950, 1.1150, 20),
            'low': np.random.uniform(1.0850, 1.1050, 20),
            'close': np.random.uniform(1.0900, 1.1100, 20),
        }, index=dates)
        
        atr_series = self.risk_calc.calcular_atr(df_test, period=14)
        
        # Verificar que ATR es una serie válida
        self.assertIsInstance(atr_series, pd.Series)
        self.assertGreater(len(atr_series), 0)
        
        # Verificar que los valores ATR son positivos
        atr_values = atr_series.dropna()
        self.assertTrue(all(atr_values > 0))
    
    def test_ajustar_riesgo_por_drawdown(self):
        """Test ajuste de riesgo por drawdown"""
        riesgo_base = 2.0
        
        # Sin drawdown
        riesgo_sin_dd = self.risk_calc.ajustar_riesgo_por_drawdown(
            drawdown_actual=0,
            riesgo_base=riesgo_base,
            timeframe='M15'
        )
        
        # Con drawdown moderado
        riesgo_con_dd = self.risk_calc.ajustar_riesgo_por_drawdown(
            drawdown_actual=7,  # 7% drawdown
            riesgo_base=riesgo_base,
            timeframe='M15'
        )
        
        # Con drawdown alto
        riesgo_alto_dd = self.risk_calc.ajustar_riesgo_por_drawdown(
            drawdown_actual=15,  # 15% drawdown
            riesgo_base=riesgo_base,
            timeframe='M15'
        )
        
        # El riesgo debe reducirse con mayor drawdown
        self.assertGreaterEqual(riesgo_sin_dd, riesgo_con_dd)
        self.assertGreaterEqual(riesgo_con_dd, riesgo_alto_dd)
    
    def test_timeframe_invalido(self):
        """Test manejo de timeframe inválido"""
        with self.assertRaises(ValueError):
            self.risk_calc.calcular_lote_dinamico(
                timeframe='INVALID',
                riesgo_porcentaje=1.0,
                atr_value=0.0015,
                precio_actual=1.1000
            )
    
    def test_atr_zero(self):
        """Test manejo de ATR cero"""
        lote = self.risk_calc.calcular_lote_dinamico(
            timeframe='M15',
            riesgo_porcentaje=1.0,
            atr_value=0.0,  # ATR cero
            precio_actual=1.1000
        )
        
        # Debe devolver lote mínimo
        self.assertEqual(lote, 0.01)
    
    def test_capital_diferente(self):
        """Test con capital diferente al inicial"""
        lote_capital_alto = self.risk_calc.calcular_lote_dinamico(
            timeframe='M15',
            riesgo_porcentaje=1.0,
            atr_value=0.0015,
            precio_actual=1.1000,
            capital_actual=2000  # Capital más alto
        )
        
        lote_capital_bajo = self.risk_calc.calcular_lote_dinamico(
            timeframe='M15',
            riesgo_porcentaje=1.0,
            atr_value=0.0015,
            precio_actual=1.1000,
            capital_actual=500   # Capital más bajo
        )
        
        # Mayor capital debería permitir mayor lote
        self.assertGreaterEqual(lote_capital_alto, lote_capital_bajo)


if __name__ == '__main__':
    unittest.main()