"""
Tests unitarios para PerformanceCalculator
Parte del testing exhaustivo de FASE 3
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.utils.performance_calculator import PerformanceCalculator


class TestPerformanceCalculator(unittest.TestCase):
    """Tests unitarios para PerformanceCalculator"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.perf_calc = PerformanceCalculator(timeframe="M15")
        
        # Datos de prueba
        self.equity_curve_profitable = [1000, 1010, 1020, 1015, 1030, 1040, 1035, 1050]
        self.equity_curve_losing = [1000, 990, 980, 985, 970, 960, 965, 950]
        self.equity_curve_flat = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
        
        self.test_reporte = {
            'capital_inicial': 1000,
            'capital_final': 1050,
            'equity_curve': self.equity_curve_profitable,
            'ganancia_bruta': 80,
            'perdida_bruta': 30,
            'operaciones_ganadoras': 6,
            'operaciones_perdedoras': 2
        }
    
    def test_initialization(self):
        """Test inicialización correcta"""
        self.assertEqual(self.perf_calc.timeframe, "M15")
        self.assertEqual(self.perf_calc.periods_per_year, 24192)  # 252 * 24 * 4
        
        # Test con timeframe diferente
        perf_calc_h1 = PerformanceCalculator(timeframe="H1")
        self.assertEqual(perf_calc_h1.periods_per_year, 6048)  # 252 * 24
    
    def test_calculate_returns(self):
        """Test cálculo de retornos"""
        returns = self.perf_calc.calculate_returns(self.equity_curve_profitable)
        
        self.assertIsInstance(returns, pd.Series)
        self.assertEqual(len(returns), len(self.equity_curve_profitable) - 1)
        
        # Verificar que los retornos son razonables
        self.assertTrue(all(abs(ret) < 1 for ret in returns))  # Retornos < 100%
    
    def test_calculate_returns_empty(self):
        """Test cálculo de retornos con datos vacíos"""
        returns = self.perf_calc.calculate_returns([])
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns.iloc[0], 0)
        
        returns = self.perf_calc.calculate_returns([1000])
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns.iloc[0], 0)
    
    def test_calculate_sharpe_ratio_profitable(self):
        """Test Sharpe ratio para estrategia rentable"""
        returns = self.perf_calc.calculate_returns(self.equity_curve_profitable)
        sharpe = self.perf_calc.calculate_sharpe_ratio(returns)
        
        self.assertIsInstance(sharpe, float)
        self.assertGreater(sharpe, 0)  # Debería ser positivo para estrategia rentable
        self.assertLessEqual(abs(sharpe), 10)  # Dentro del límite
    
    def test_calculate_sharpe_ratio_losing(self):
        """Test Sharpe ratio para estrategia perdedora"""
        returns = self.perf_calc.calculate_returns(self.equity_curve_losing)
        sharpe = self.perf_calc.calculate_sharpe_ratio(returns)
        
        self.assertIsInstance(sharpe, float)
        self.assertLess(sharpe, 0)  # Debería ser negativo para estrategia perdedora
        self.assertGreaterEqual(sharpe, -10)  # Dentro del límite
    
    def test_calculate_sharpe_ratio_flat(self):
        """Test Sharpe ratio para estrategia plana"""
        returns = self.perf_calc.calculate_returns(self.equity_curve_flat)
        sharpe = self.perf_calc.calculate_sharpe_ratio(returns)
        
        self.assertEqual(sharpe, 0)  # Sin variación = Sharpe 0
    
    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio"""
        returns = self.perf_calc.calculate_returns(self.equity_curve_profitable)
        sortino = self.perf_calc.calculate_sortino_ratio(returns)
        
        self.assertIsInstance(sortino, float)
        self.assertLessEqual(abs(sortino), 10)  # Dentro del límite
    
    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio"""
        calmar = self.perf_calc.calculate_calmar_ratio(
            total_return=0.05,  # 5% retorno
            max_drawdown=0.02,  # 2% drawdown
            num_periods=100
        )
        
        self.assertIsInstance(calmar, float)
        self.assertGreater(calmar, 0)  # Debería ser positivo
        self.assertLessEqual(abs(calmar), 10)  # Dentro del límite
    
    def test_calculate_calmar_ratio_zero_drawdown(self):
        """Test Calmar ratio con drawdown cero"""
        calmar = self.perf_calc.calculate_calmar_ratio(
            total_return=0.05,
            max_drawdown=0.0,  # Sin drawdown
            num_periods=100
        )
        
        self.assertEqual(calmar, 0)  # Debería ser 0 cuando no hay drawdown
    
    def test_calculate_max_drawdown(self):
        """Test cálculo de máximo drawdown"""
        # Crear equity curve con drawdown conocido
        equity_with_dd = [1000, 1050, 1030, 1020, 1040, 1060]  # Max DD: 1050 -> 1020 = 2.86%
        
        dd_metrics = self.perf_calc.calculate_max_drawdown(equity_with_dd)
        
        self.assertIn('max_drawdown', dd_metrics)
        self.assertIn('max_drawdown_percent', dd_metrics)
        self.assertIn('max_drawdown_value', dd_metrics)
        
        self.assertGreater(dd_metrics['max_drawdown'], 0)
        self.assertGreater(dd_metrics['max_drawdown_percent'], 0)
        self.assertGreater(dd_metrics['max_drawdown_value'], 0)
    
    def test_calculate_max_drawdown_no_drawdown(self):
        """Test drawdown con equity curve siempre creciente"""
        equity_no_dd = [1000, 1010, 1020, 1030, 1040, 1050]
        
        dd_metrics = self.perf_calc.calculate_max_drawdown(equity_no_dd)
        
        self.assertEqual(dd_metrics['max_drawdown'], 0)
        self.assertEqual(dd_metrics['max_drawdown_percent'], 0)
    
    def test_calculate_win_loss_ratio(self):
        """Test Win/Loss ratio"""
        win_loss = self.perf_calc.calculate_win_loss_ratio(
            ganancia_bruta=100,
            perdida_bruta=50,
            ops_ganadoras=5,
            ops_perdedoras=3
        )
        
        # (100/5) / (50/3) = 20 / 16.67 = 1.2
        self.assertAlmostEqual(win_loss, 1.2, places=1)
    
    def test_calculate_win_loss_ratio_no_losses(self):
        """Test Win/Loss ratio sin pérdidas"""
        win_loss = self.perf_calc.calculate_win_loss_ratio(
            ganancia_bruta=100,
            perdida_bruta=0,
            ops_ganadoras=5,
            ops_perdedoras=0
        )
        
        self.assertEqual(win_loss, float('inf'))
    
    def test_calculate_win_loss_ratio_no_wins(self):
        """Test Win/Loss ratio sin ganancias"""
        win_loss = self.perf_calc.calculate_win_loss_ratio(
            ganancia_bruta=0,
            perdida_bruta=50,
            ops_ganadoras=0,
            ops_perdedoras=3
        )
        
        self.assertEqual(win_loss, 0)
    
    def test_calculate_comprehensive_metrics(self):
        """Test cálculo de métricas comprehensivas"""
        metrics = self.perf_calc.calculate_comprehensive_metrics(self.test_reporte)
        
        # Verificar que todas las métricas están presentes
        expected_keys = [
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'win_loss_ratio',
            'profit_factor', 'total_return', 'total_return_percent',
            'max_drawdown', 'max_drawdown_percent', 'periods_per_year', 'timeframe'
        ]
        
        for key in expected_keys:
            self.assertIn(key, metrics)
        
        # Verificar tipos de datos
        self.assertIsInstance(metrics['sharpe_ratio'], float)
        self.assertIsInstance(metrics['total_return'], float)
        self.assertIsInstance(metrics['timeframe'], str)
        
        # Verificar valores razonables
        self.assertEqual(metrics['timeframe'], 'M15')
        self.assertAlmostEqual(metrics['total_return'], 0.05, places=2)  # 5% return
    
    def test_validate_metrics(self):
        """Test validación de métricas"""
        # Métricas válidas
        valid_metrics = {
            'sharpe_ratio': 1.5,
            'sortino_ratio': 2.0,
            'calmar_ratio': 1.2,
            'max_drawdown': 0.05,
            'profit_factor': 1.8,
            'total_return': 0.15
        }
        
        validations = self.perf_calc.validate_metrics(valid_metrics)
        
        self.assertTrue(all(validations.values()))
        
        # Métricas inválidas
        invalid_metrics = {
            'sharpe_ratio': 15,  # Muy alto
            'max_drawdown': 1.5,  # > 100%
            'total_return': -2.0  # < -100%
        }
        
        validations = self.perf_calc.validate_metrics(invalid_metrics)
        
        self.assertFalse(validations['sharpe_reasonable'])
        self.assertFalse(validations['drawdown_reasonable'])
        self.assertFalse(validations['total_return_reasonable'])
    
    def test_different_timeframes(self):
        """Test con diferentes timeframes"""
        timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4']
        
        for tf in timeframes:
            perf_calc = PerformanceCalculator(timeframe=tf)
            returns = perf_calc.calculate_returns(self.equity_curve_profitable)
            sharpe = perf_calc.calculate_sharpe_ratio(returns)
            
            # Verificar que cada timeframe produce resultados válidos
            self.assertIsInstance(sharpe, float)
            self.assertLessEqual(abs(sharpe), 10)
            
            # Verificar que periods_per_year es correcto
            self.assertGreater(perf_calc.periods_per_year, 0)


if __name__ == '__main__':
    unittest.main()