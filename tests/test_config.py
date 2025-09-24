import unittest
import pandas as pd
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from estrategia_ia.config import validar_configuracion, validar_estrategia, validar_datos_mercado

class TestConfig(unittest.TestCase):
    
    def test_validar_configuracion_correcta(self):
        """Test que la configuración por defecto es válida"""
        resultado = validar_configuracion()
        self.assertTrue(resultado)
    
    def test_validar_estrategia_valida(self):
        """Test validación de estrategia correcta"""
        estrategia = {
            "nombre": "Test Strategy",
            "ema_reversion": 20,
            "ema_tendencia": 150,
            "optimizable_params": {
                "ema_reversion": {"min": 10, "max": 50, "step": 2},
                "ema_tendencia": {"min": 100, "max": 250, "step": 10}
            }
        }
        errores = validar_estrategia(estrategia)
        self.assertEqual(len(errores), 0)
    
    def test_validar_estrategia_invalida(self):
        """Test validación de estrategia con errores"""
        estrategia = {
            "nombre": "Test Strategy",
            "ema_corta": 30,  # Mayor que ema_larga
            "ema_larga": 20
        }
        errores = validar_estrategia(estrategia)
        self.assertGreater(len(errores), 0)
    
    def test_validar_datos_mercado_validos(self):
        """Test validación de datos de mercado correctos"""
        df = pd.DataFrame({
            'open': [1.1000, 1.1010, 1.1005],
            'high': [1.1015, 1.1020, 1.1015],
            'low': [0.9995, 1.1005, 1.1000],
            'close': [1.1010, 1.1005, 1.1012]
        })
        errores = validar_datos_mercado(df)
        self.assertEqual(len(errores), 0)
    
    def test_validar_datos_mercado_invalidos(self):
        """Test validación de datos con errores lógicos"""
        df = pd.DataFrame({
            'open': [1.1000, 1.1010],
            'high': [1.0990, 1.1020],  # high < open en primera fila
            'low': [0.9995, 1.1005],
            'close': [1.1010, 1.1005]
        })
        errores = validar_datos_mercado(df)
        self.assertGreater(len(errores), 0)

if __name__ == '__main__':
    unittest.main()