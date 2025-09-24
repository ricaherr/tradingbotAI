import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.core.indicadores import calcular_ema, calcular_atr, es_vela_elefante

class TestIndicadores(unittest.TestCase):
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.df_test = pd.DataFrame({
            'close': [1.1000, 1.1010, 1.1005, 1.1020, 1.1015, 1.1030, 1.1025, 1.1040],
            'high': [1.1015, 1.1020, 1.1015, 1.1025, 1.1020, 1.1035, 1.1030, 1.1045],
            'low': [0.9995, 1.1005, 1.1000, 1.1015, 1.1010, 1.1025, 1.1020, 1.1035],
            'open': [1.1005, 1.1000, 1.1010, 1.1005, 1.1020, 1.1015, 1.1030, 1.1025]
        })
    
    def test_calcular_ema(self):
        """Test cálculo de EMA optimizado"""
        ema = calcular_ema(self.df_test, 'close', 3)
        
        # Verificar que no hay NaN en los resultados
        self.assertFalse(np.isnan(ema).any())
        
        # Verificar que la longitud es correcta
        self.assertEqual(len(ema), len(self.df_test))
        
        # Verificar que los valores son razonables
        self.assertTrue(all(ema > 0))
    
    def test_calcular_atr(self):
        """Test cálculo de ATR optimizado"""
        atr = calcular_atr(self.df_test, 3)
        
        # Verificar que no hay NaN después del período inicial
        self.assertFalse(np.isnan(atr[3:]).any())
        
        # Verificar que ATR es positivo
        self.assertTrue(all(atr[3:] > 0))
        
        # Verificar longitud
        self.assertEqual(len(atr), len(self.df_test))
    
    def test_es_vela_elefante(self):
        """Test detección de vela elefante"""
        # Crear una vela elefante artificial
        df_elefante = pd.DataFrame({
            'high': [1.1000, 1.1050],  # Vela grande
            'low': [1.0950, 1.1045],
            'close': [1.0975, 1.1048],
            'open': [1.0975, 1.1047]
        })
        
        atr_values = np.array([0.0020, 0.0020])  # ATR de 20 pips
        
        # Agregar columna ATR al DataFrame
        df_elefante['ATR'] = atr_values
        
        # Probar detección de vela elefante
        resultado = es_vela_elefante(df_elefante, 'ATR', 2.0)
        
        # Verificar que devuelve una Serie booleana
        self.assertEqual(len(resultado), 2)
        self.assertIsInstance(resultado.iloc[0], (bool, np.bool_))

if __name__ == '__main__':
    unittest.main()