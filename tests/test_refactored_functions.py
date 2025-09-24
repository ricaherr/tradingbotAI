import unittest
import pandas as pd
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importar solo funciones públicas para tests básicos
from estrategia_ia.utils import registro_operaciones
from estrategia_ia.optimization import adjuster

class TestRefactoredFunctions(unittest.TestCase):
    
    def test_modulos_importan_correctamente(self):
        """Test que los módulos refactorizados se pueden importar"""
        self.assertTrue(hasattr(registro_operaciones, 'monitorear_y_registrar_operaciones_cerradas'))
        self.assertTrue(hasattr(adjuster, 'Adjuster'))
    
    def test_funciones_existen(self):
        """Test que las funciones principales existen después de refactoring"""
        # Verificar que las funciones principales siguen existiendo
        self.assertTrue(callable(getattr(registro_operaciones, 'monitorear_y_registrar_operaciones_cerradas', None)))
        
        # Verificar que la clase adjuster existe
        adjuster_class = getattr(adjuster, 'Adjuster', None)
        self.assertIsNotNone(adjuster_class)

if __name__ == '__main__':
    unittest.main()