# DIAGNÓSTICOS DEL SISTEMA DE TRADING

Este directorio contiene scripts de diagnóstico para validar diferentes aspectos del sistema de trading.

## SCRIPTS DISPONIBLES

### `diagnostic_metrics.py`
**Propósito**: Valida MetricsCalculator y cálculos financieros
**Uso**: `python diagnostics/diagnostic_metrics.py`
**Valida**:
- Creación correcta de calculadoras por timeframe
- Consistencia de Sharpe Ratio entre timeframes
- Funcionamiento del Evaluator con timeframes
- Manejo de casos extremos
- Comparación con implementación anterior

### `diagnostic_system_flow.py`
**Propósito**: Auditoría completa del flujo de optimización
**Uso**: `python diagnostics/diagnostic_system_flow.py`
**Valida**:
- CLI parsing correcto
- Selección de estrategias
- Inicialización de componentes
- Obtención de datos por timeframe
- Creación de configuraciones
- Cálculo de fitness
- Consistencia end-to-end

### `diagnostic_timeframes.py`
**Propósito**: Análisis de variables dependientes del timeframe
**Uso**: `python diagnostics/diagnostic_timeframes.py`
**Valida**:
- Identificación de variables hardcodeadas
- Propuestas de soluciones dinámicas
- Análisis de impacto por timeframe

### `diagnostic_architecture.py`
**Propósito**: Evaluación de soluciones arquitecturales
**Uso**: `python diagnostics/diagnostic_architecture.py`
**Valida**:
- Cumplimiento de principios SOLID
- Evaluación de patrones de diseño
- Análisis de mantenibilidad
- Recomendaciones de implementación

### `diagnostic_risk_management.py`
**Propósito**: Validación de gestión de riesgo dinámica (FASE 2)
**Uso**: `python diagnostics/diagnostic_risk_management.py`
**Valida**:
- RiskCalculator y configuración por timeframe
- Cálculo dinámico de lotes
- SL/TP adaptativos por timeframe
- Validación de límites de riesgo
- Integración con strategies y backtesting
- Consistencia entre timeframes

## CONVENCIONES

### Nomenclatura
- Formato: `diagnostic_[componente].py`
- Nombres descriptivos y específicos
- Sin abreviaciones ambiguas

### Estructura de Scripts
```python
#!/usr/bin/env python3
"""
Descripción clara del propósito del diagnóstico.
"""

def main():
    """Función principal del diagnóstico."""
    try:
        # Lógica de diagnóstico
        print("[OK] Diagnóstico completado exitosamente")
        return True
    except Exception as e:
        print(f"[ERROR] Diagnóstico falló: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

### Códigos de Salida
- `0`: Diagnóstico exitoso
- `1`: Diagnóstico falló o encontró problemas

### Formato de Salida
- `[OK]`: Operación exitosa
- `[ERROR]`: Error crítico
- `[WARNING]`: Advertencia no crítica
- `[INFO]`: Información general

## EJECUCIÓN

### Individual
```bash
python diagnostics/diagnostic_metrics.py
```

### Todos los diagnósticos
```bash
# Windows
for %f in (diagnostics\diagnostic_*.py) do python "%f"

# PowerShell
Get-ChildItem diagnostics\diagnostic_*.py | ForEach-Object { python $_.FullName }
```

## INTEGRACIÓN CON CI/CD

Los scripts están diseñados para integrarse fácilmente en pipelines de CI/CD:

```yaml
# Ejemplo GitHub Actions
- name: Run Diagnostics
  run: |
    python diagnostics/diagnostic_metrics.py
    python diagnostics/diagnostic_system_flow.py
```

## DESARROLLO DE NUEVOS DIAGNÓSTICOS

### Checklist para Nuevos Scripts
- [ ] Nombre sigue convención `diagnostic_[componente].py`
- [ ] Incluye docstring descriptivo
- [ ] Función main() con manejo de errores
- [ ] Códigos de salida apropiados (0/1)
- [ ] Formato de salida consistente
- [ ] Documentación en este README
- [ ] Tests de validación incluidos

### Plantilla
```python
#!/usr/bin/env python3
"""
diagnostic_[componente].py

Descripción detallada del propósito del diagnóstico.
Qué valida, cómo lo usa, qué problemas detecta.
"""

import sys
import os

# Agregar src al path si es necesario
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def validate_component():
    """Valida el componente específico."""
    # Lógica de validación
    pass

def main():
    """Ejecuta el diagnóstico completo."""
    print("=== DIAGNÓSTICO: [COMPONENTE] ===")
    
    try:
        validate_component()
        print("[OK] Diagnóstico completado exitosamente")
        return True
    except Exception as e:
        print(f"[ERROR] Diagnóstico falló: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## MANTENIMIENTO

- Ejecutar diagnósticos después de cambios significativos
- Actualizar scripts cuando se modifiquen componentes relacionados
- Revisar y actualizar este README regularmente
- Archivar diagnósticos obsoletos en lugar de eliminarlos