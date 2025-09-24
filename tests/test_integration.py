import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestIntegration(unittest.TestCase):
    
    def test_imports_basicos(self):
        """Test que todos los módulos principales se pueden importar"""
        try:
            from estrategia_ia.config import validar_configuracion
            from estrategia_ia.core.indicadores import calcular_ema
            from estrategia_ia.utils.logger import setup_logger
            from estrategia_ia.utils.error_handler import safe_execute
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Error de importación: {e}")
    
    def test_configuracion_sistema(self):
        """Test que la configuración del sistema es válida"""
        from estrategia_ia.config import validar_configuracion
        resultado = validar_configuracion()
        self.assertTrue(resultado, "La configuración del sistema no es válida")
    
    def test_logger_funciona(self):
        """Test que el sistema de logging funciona"""
        from estrategia_ia.utils.logger import setup_logger
        
        logger = setup_logger("test")
        self.assertIsNotNone(logger)
        
        # Test que no falla al hacer log
        try:
            logger.info("Test message")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Error en logging: {e}")
    
    def test_error_handler_funciona(self):
        """Test que el manejo de errores funciona"""
        from estrategia_ia.utils.error_handler import safe_execute
        
        def funcion_que_falla():
            raise ValueError("Test error")
        
        def funcion_que_funciona():
            return "success"
        
        # Test función que falla
        resultado = safe_execute(funcion_que_falla, default_return="default")
        self.assertEqual(resultado, "default")
        
        # Test función que funciona
        resultado = safe_execute(funcion_que_funciona)
        self.assertEqual(resultado, "success")

if __name__ == '__main__':
    unittest.main()