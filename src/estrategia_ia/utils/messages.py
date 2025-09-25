"""
Utilidades para mensajes informativos mejorados al usuario.
"""

import sys
from datetime import datetime
from typing import Optional, Dict, Any

class MessageFormatter:
    """Formateador de mensajes para mejorar la experiencia del usuario."""
    
    # Colores ANSI para terminal (funciona en la mayoría de terminales)
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        'END': '\033[0m'
    }
    
    @classmethod
    def _colorize(cls, text: str, color: str) -> str:
        """Aplica color al texto si el terminal lo soporta."""
        if sys.stdout.isatty():  # Solo colorear si es un terminal interactivo
            return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['END']}"
        return text
    
    @classmethod
    def success(cls, message: str) -> None:
        """Mensaje de éxito."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {cls._colorize('[OK]', 'GREEN')} {message}"
        print(formatted)
    
    @classmethod
    def error(cls, message: str) -> None:
        """Mensaje de error."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {cls._colorize('[ERROR]', 'RED')} {message}"
        print(formatted)
    
    @classmethod
    def warning(cls, message: str) -> None:
        """Mensaje de advertencia."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {cls._colorize('[WARNING]', 'YELLOW')} {message}"
        print(formatted)
    
    @classmethod
    def info(cls, message: str) -> None:
        """Mensaje informativo."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {cls._colorize('[INFO]', 'BLUE')} {message}"
        print(formatted)
    
    @classmethod
    def header(cls, title: str, width: int = 60) -> None:
        """Encabezado destacado."""
        border = "=" * width
        title_centered = title.center(width)
        print(f"\n{cls._colorize(border, 'CYAN')}")
        print(f"{cls._colorize(title_centered, 'BOLD')}")
        print(f"{cls._colorize(border, 'CYAN')}")
    
    @classmethod
    def section(cls, title: str, width: int = 50) -> None:
        """Sección con título."""
        border = "-" * width
        print(f"\n{cls._colorize(border, 'BLUE')}")
        print(f"{cls._colorize(title, 'BOLD')}")
        print(f"{cls._colorize(border, 'BLUE')}")
    
    @classmethod
    def table_row(cls, data: Dict[str, Any], widths: Optional[Dict[str, int]] = None) -> None:
        """Fila de tabla formateada."""
        if not widths:
            widths = {key: 15 for key in data.keys()}
        
        row = ""
        for key, value in data.items():
            width = widths.get(key, 15)
            formatted_value = str(value)[:width-1]  # Truncar si es muy largo
            row += f"{formatted_value:<{width}} "
        
        print(row)
    
    @classmethod
    def progress_summary(cls, current: int, total: int, description: str = "") -> None:
        """Resumen de progreso simple."""
        percent = (current / total) * 100 if total > 0 else 0
        status = f"Progreso: {current}/{total} ({percent:.1f}%)"
        if description:
            status += f" - {description}"
        cls.info(status)

def show_optimization_summary(results: Dict[str, Any]) -> None:
    """Muestra un resumen detallado de los resultados de optimización."""
    msg = MessageFormatter()
    
    msg.header("RESUMEN DE OPTIMIZACIÓN")
    
    # Información básica
    msg.section("Información General")
    print(f"  Estrategia: {results.get('strategy_name', 'N/A')}")
    print(f"  Tiempo total: {results.get('total_time', 'N/A')} segundos")
    print(f"  Generaciones: {results.get('generations', 'N/A')}")
    print(f"  Población: {results.get('population_size', 'N/A')}")
    
    # Mejores resultados
    if 'best_fitness' in results:
        msg.section("Mejores Resultados")
        print(f"  Mejor fitness: {results['best_fitness']:.4f}")
        
        if 'best_config' in results:
            print("  Mejores parámetros:")
            for param, value in results['best_config'].items():
                print(f"    {param}: {value}")
    
    # Métricas de rendimiento
    if 'performance_metrics' in results:
        metrics = results['performance_metrics']
        msg.section("Métricas de Rendimiento")
        
        # Tabla de métricas principales
        msg.table_row({
            'Métrica': 'Valor',
            'Descripción': 'Detalle'
        }, {'Métrica': 20, 'Valor': 15, 'Descripción': 25})
        
        print("-" * 60)
        
        key_metrics = [
            ('profit_neto', 'Beneficio Neto', '$'),
            ('sharpe_ratio', 'Sharpe Ratio', ''),
            ('max_drawdown', 'Max Drawdown', '%'),
            ('win_rate', 'Tasa de Acierto', '%'),
            ('total_trades', 'Total Operaciones', '')
        ]
        
        for key, name, unit in key_metrics:
            if key in metrics:
                value = metrics[key]
                if unit == '%':
                    value_str = f"{value:.2f}%"
                elif unit == '$':
                    value_str = f"${value:.2f}"
                else:
                    value_str = f"{value:.4f}"
                
                msg.table_row({
                    'Métrica': name,
                    'Valor': value_str,
                    'Descripción': ''
                }, {'Métrica': 20, 'Valor': 15, 'Descripción': 25})

def show_startup_banner():
    """Muestra banner de inicio del sistema."""
    msg = MessageFormatter()
    
    msg.header("SISTEMA DE TRADING CON IA", 70)
    print(f"{msg._colorize('    Optimización Genética de Estrategias de Trading', 'CYAN')}")
    print(f"{msg._colorize('    Versión 2.0 - Desarrollado con Amazon Q', 'CYAN')}")
    print()
    
    msg.info("Sistema iniciado correctamente")
    msg.info("Ejecuta 'python run_optimization_enhanced.py --help' para ver opciones")

def show_help_commands():
    """Muestra comandos de ayuda disponibles."""
    msg = MessageFormatter()
    
    msg.section("COMANDOS DISPONIBLES")
    
    commands = [
        ("python run_optimization_enhanced.py", "Optimización completa"),
        ("python run_optimization_enhanced.py --quick", "Optimización rápida (pruebas)"),
        ("python run_optimization_enhanced.py --strategy 'Nombre'", "Optimizar estrategia específica"),
        ("python run_tests.py", "Ejecutar tests de validación"),
        ("python run_optimization_enhanced.py --profile", "Optimización con profiling")
    ]
    
    for command, description in commands:
        print(f"  {msg._colorize(command, 'GREEN')}")
        print(f"    {description}\n")