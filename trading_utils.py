#!/usr/bin/env python3
"""
Utilidades del sistema de trading - Script principal de comandos.
"""

import sys
import os
import argparse

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from estrategia_ia.utils.messages import MessageFormatter, show_startup_banner, show_help_commands
from estrategia_ia.config import validar_configuracion

def parse_arguments():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Utilidades del Sistema de Trading con IA",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando de validación
    validate_parser = subparsers.add_parser('validate', help='Validar configuración del sistema')
    
    # Comando de información
    info_parser = subparsers.add_parser('info', help='Mostrar información del sistema')
    
    # Comando de ayuda
    help_parser = subparsers.add_parser('help', help='Mostrar comandos disponibles')
    
    # Comando de test rápido
    test_parser = subparsers.add_parser('test', help='Ejecutar test rápido del sistema')
    
    # Comando de limpieza
    clean_parser = subparsers.add_parser('clean', help='Limpiar archivos temporales')
    
    return parser.parse_args()

def validate_system():
    """Valida la configuración completa del sistema."""
    msg = MessageFormatter()
    
    msg.header("VALIDACIÓN DEL SISTEMA")
    
    # Validar configuración
    msg.info("Validando configuración...")
    if validar_configuracion():
        msg.success("Configuración válida")
    else:
        msg.error("Errores en configuración detectados")
        return False
    
    # Validar imports críticos
    msg.info("Validando imports críticos...")
    try:
        from estrategia_ia.core.indicadores import calcular_ema
        from estrategia_ia.optimization.optimizer import GeneticOptimizer
        from estrategia_ia.utils.logger import setup_logger
        msg.success("Todos los imports críticos funcionan")
    except ImportError as e:
        msg.error(f"Error en imports: {e}")
        return False
    
    # Validar estructura de directorios
    msg.info("Validando estructura de directorios...")
    required_dirs = [
        'src/estrategia_ia/core',
        'src/estrategia_ia/optimization',
        'src/estrategia_ia/utils',
        'tests',
        'data'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        msg.warning(f"Directorios faltantes: {', '.join(missing_dirs)}")
    else:
        msg.success("Estructura de directorios correcta")
    
    msg.success("Validación del sistema completada")
    return True

def show_system_info():
    """Muestra información del sistema."""
    msg = MessageFormatter()
    
    msg.header("INFORMACIÓN DEL SISTEMA")
    
    # Información de Python
    msg.section("Entorno Python")
    print(f"  Versión de Python: {sys.version}")
    print(f"  Directorio de trabajo: {os.getcwd()}")
    
    # Información de configuración
    msg.section("Configuración Actual")
    try:
        from estrategia_ia.config import OPTIMIZER_SETTINGS, ESTRATEGIAS
        print(f"  Estrategias configuradas: {len(ESTRATEGIAS)}")
        print(f"  Población del optimizador: {OPTIMIZER_SETTINGS['population_size']}")
        print(f"  Generaciones: {OPTIMIZER_SETTINGS['generations']}")
        
        # Estrategias activas
        activas = [e for e in ESTRATEGIAS if e.get('modo') == 'backtest']
        print(f"  Estrategias activas: {len(activas)}")
        for estrategia in activas:
            print(f"    - {estrategia['nombre']}")
            
    except Exception as e:
        msg.error(f"Error leyendo configuración: {e}")
    
    # Información de archivos
    msg.section("Archivos del Sistema")
    important_files = [
        'run_optimization.py',
        'run_optimization_enhanced.py',
        'run_tests.py',
        'trading_utils.py',
        'src/estrategia_ia/config.py'
    ]
    
    for file_path in important_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  [OK] {file_path} ({size} bytes)")
        else:
            print(f"  [MISSING] {file_path} (faltante)")

def run_quick_test():
    """Ejecuta un test rápido del sistema."""
    msg = MessageFormatter()
    
    msg.header("TEST RÁPIDO DEL SISTEMA")
    
    # Test de configuración
    msg.info("Ejecutando test de configuración...")
    if not validate_system():
        msg.error("Test de configuración falló")
        return False
    
    # Test de indicadores
    msg.info("Ejecutando test de indicadores...")
    try:
        import pandas as pd
        from estrategia_ia.core.indicadores import calcular_ema
        
        # Crear datos de prueba
        test_data = pd.DataFrame({
            'close': [1.1000, 1.1010, 1.1005, 1.1020, 1.1015]
        })
        
        ema = calcular_ema(test_data, 'close', 3)
        if len(ema) == len(test_data):
            msg.success("Test de indicadores pasó")
        else:
            msg.error("Test de indicadores falló")
            return False
            
    except Exception as e:
        msg.error(f"Error en test de indicadores: {e}")
        return False
    
    # Test de optimizador (solo import)
    msg.info("Ejecutando test de optimizador...")
    try:
        from estrategia_ia.optimization.optimizer import GeneticOptimizer
        msg.success("Test de optimizador pasó")
    except Exception as e:
        msg.error(f"Error en test de optimizador: {e}")
        return False
    
    msg.success("Todos los tests rápidos pasaron correctamente")
    return True

def clean_system():
    """Limpia archivos temporales del sistema."""
    msg = MessageFormatter()
    
    msg.header("LIMPIEZA DEL SISTEMA")
    
    # Archivos a limpiar
    temp_patterns = [
        '*.pyc',
        '__pycache__',
        '*.log',
        'convergence_plot*.png'
    ]
    
    cleaned_count = 0
    
    for pattern in temp_patterns:
        msg.info(f"Limpiando archivos: {pattern}")
        
        if pattern == '__pycache__':
            # Limpiar directorios __pycache__
            for root, dirs, files in os.walk('.'):
                if '__pycache__' in dirs:
                    import shutil
                    pycache_path = os.path.join(root, '__pycache__')
                    try:
                        shutil.rmtree(pycache_path)
                        cleaned_count += 1
                        msg.info(f"  Eliminado: {pycache_path}")
                    except Exception as e:
                        msg.warning(f"  No se pudo eliminar {pycache_path}: {e}")
        else:
            # Limpiar archivos por patrón
            import glob
            files = glob.glob(pattern, recursive=True)
            for file_path in files:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    msg.info(f"  Eliminado: {file_path}")
                except Exception as e:
                    msg.warning(f"  No se pudo eliminar {file_path}: {e}")
    
    msg.success(f"Limpieza completada. {cleaned_count} elementos eliminados")

def main():
    """Función principal."""
    args = parse_arguments()
    
    if not args.command:
        show_startup_banner()
        show_help_commands()
        return
    
    if args.command == 'validate':
        validate_system()
    elif args.command == 'info':
        show_system_info()
    elif args.command == 'help':
        show_help_commands()
    elif args.command == 'test':
        run_quick_test()
    elif args.command == 'clean':
        clean_system()
    else:
        MessageFormatter.error(f"Comando desconocido: {args.command}")

if __name__ == "__main__":
    main()