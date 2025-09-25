import unittest
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.optimization.optimizer import GeneticOptimizer
from estrategia_ia.config import ESTRATEGIAS

class TestOptimizer(unittest.TestCase):
    
    def setUp(self):
        """Crear datos de prueba mínimos."""
        # Crear datos sintéticos muy pequeños
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        np.random.seed(42)  # Para resultados reproducibles
        
        prices = 1.1000 + np.cumsum(np.random.randn(100) * 0.0001)
        
        self.test_data = pd.DataFrame({
            'open': prices,
            'high': prices + np.random.rand(100) * 0.0005,
            'low': prices - np.random.rand(100) * 0.0005,
            'close': prices + np.random.randn(100) * 0.0002,
            'volume': np.random.randint(100, 1000, 100)
        }, index=dates)
        
        # Guardar datos de prueba
        self.test_file = 'test_data.csv'
        self.test_data.to_csv(self.test_file)
        
        # Estrategia de prueba mínima
        self.test_strategy = {
            "nombre": "Test Strategy",
            "usar_filtro_tendencia": True,
            "optimizable_params": {
                "ema_reversion": {"min": 10, "max": 20, "step": 5},
                "ema_tendencia": {"min": 50, "max": 100, "step": 25}
            }
        }
    
    def tearDown(self):
        """Limpiar archivos de prueba."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_optimizer_creation(self):
        """Test que el optimizador se puede crear."""
        optimizer = GeneticOptimizer(
            strategy_config=self.test_strategy,
            data_file_path=self.test_file,
            population_size=2,
            generations=1,
            test_mode=True
        )
        
        self.assertIsNotNone(optimizer)
        self.assertEqual(optimizer.population_size, 2)
        self.assertEqual(optimizer.generations, 1)
    
    def test_create_initial_population(self):
        """Test creación de población inicial."""
        optimizer = GeneticOptimizer(
            strategy_config=self.test_strategy,
            data_file_path=self.test_file,
            population_size=3,
            generations=1,
            test_mode=True
        )
        
        population = optimizer._create_initial_population()
        
        self.assertEqual(len(population), 3)
        for individual in population:
            self.assertIn('ema_reversion', individual)
            self.assertIn('ema_tendencia', individual)
            self.assertGreaterEqual(individual['ema_reversion'], 10)
            self.assertLessEqual(individual['ema_reversion'], 20)
    
    def test_ultra_quick_optimization(self):
        """Test optimización ultra rápida (solo para verificar que no falla)."""
        optimizer = GeneticOptimizer(
            strategy_config=self.test_strategy,
            data_file_path=self.test_file,
            population_size=2,
            generations=1,
            backtest_period_years=0.01,  # Solo unos pocos días
            test_mode=True
        )
        
        try:
            result, config = optimizer.run_optimization()
            # Si llega aquí sin error, el test pasa
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Optimización ultra rápida falló: {e}")

if __name__ == '__main__':
    unittest.main()