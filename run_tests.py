#!/usr/bin/env python3
"""
Script para ejecutar todos los tests del sistema de trading
"""

import unittest
import sys
import os

def run_all_tests():
    """Ejecuta todos los tests y muestra un resumen"""
    
    # Agregar el directorio de tests al path
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    # Descubrir y ejecutar todos los tests
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Ejecutar tests con verbosidad
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "="*50)
    print("RESUMEN DE TESTS")
    print("="*50)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    
    if result.errors:
        print("\nERRORES:")
        for test, error in result.errors:
            print(f"  - {test}: {error.split('\\n')[0]}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure.split('\\n')[0]}")
    
    if result.wasSuccessful():
        print("\n[OK] TODOS LOS TESTS PASARON CORRECTAMENTE")
        return True
    else:
        print("\n[ERROR] ALGUNOS TESTS FALLARON")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)