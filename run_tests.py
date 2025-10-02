"""
Script para ejecutar todos los tests de FASE 3
"""

import unittest
import sys
import os
import time

def run_all_tests():
    """Ejecuta todos los tests unitarios"""
    print("=" * 60)
    print("EJECUTANDO TESTS UNITARIOS - FASE 3")
    print("=" * 60)
    
    start_time = time.time()
    
    # Descubrir y ejecutar todos los tests
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    if not os.path.exists(test_dir):
        print(f"[ERROR] Directorio de tests no encontrado: {test_dir}")
        return False
    
    # Cargar tests
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Estadísticas
    total_time = time.time() - start_time
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print(f"Tests ejecutados: {total_tests}")
    print(f"Exitosos: {total_tests - failures - errors}")
    print(f"Fallidos: {failures}")
    print(f"Errores: {errors}")
    print(f"Tasa de éxito: {success_rate:.1f}%")
    print(f"Tiempo total: {total_time:.2f}s")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] TODOS LOS TESTS PASARON")
        return True
    else:
        print("\n[ERROR] ALGUNOS TESTS FALLARON")
        
        if result.failures:
            print("\nFALLOS:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nERRORES:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
        
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)