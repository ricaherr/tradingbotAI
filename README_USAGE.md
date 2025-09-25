# 🚀 Guía de Uso - Sistema de Trading con IA

## 📋 Comandos Principales

### 🔧 Utilidades del Sistema
```bash
# Validar configuración completa del sistema
python trading_utils.py validate

# Mostrar información del sistema
python trading_utils.py info

# Ejecutar test rápido
python trading_utils.py test

# Limpiar archivos temporales
python trading_utils.py clean

# Mostrar ayuda
python trading_utils.py help
```

### 🧪 Ejecutar Tests
```bash
# Ejecutar todos los tests
python run_tests.py

# Ejecutar test específico
python -m unittest tests.test_config
python -m unittest tests.test_indicadores
```

### ⚡ Optimización de Estrategias

#### Optimización Completa
```bash
# Optimización completa (configuración por defecto)
python run_optimization_enhanced.py

# Optimización con salida detallada
python run_optimization_enhanced.py --verbose
```

#### Optimización Rápida (Para Pruebas)
```bash
# Optimización rápida (5 generaciones, 20 individuos)
python run_optimization_enhanced.py --quick

# Optimización rápida de estrategia específica
python run_optimization_enhanced.py --quick --strategy "Reversión a la Media"
```

#### Optimización Personalizada
```bash
# Configurar generaciones y población
python run_optimization_enhanced.py --generations 15 --population 30

# Optimizar solo una estrategia
python run_optimization_enhanced.py --strategy "Reversión a la Media"

# Optimización con profiling de rendimiento
python run_optimization_enhanced.py --profile

# Desactivar barra de progreso
python run_optimization_enhanced.py --no-progress
```

#### Optimización Original (Compatibilidad)
```bash
# Modo de prueba (parámetros reducidos)
python run_optimization.py --test

# Modo verbose
python run_optimization.py --verbose
```

## 📊 Interpretación de Resultados

### Métricas Principales
- **Fitness (Sharpe Ratio)**: >1.0 excelente, >0.5 bueno, <0.1 malo
- **Profit Neto**: Beneficio total en USD
- **Max Drawdown**: Pérdida máxima (menor es mejor)
- **Win Rate**: Porcentaje de operaciones ganadoras
- **Total Trades**: Número total de operaciones

### Archivos de Salida
- `Reversión_a_la_Media.json`: Resultados de optimización
- `convergence_plot.png`: Gráfico de convergencia
- `trading_agent.log`: Logs técnicos del sistema

## 🛠️ Configuración

### Archivo Principal: `src/estrategia_ia/config.py`

#### Parámetros del Optimizador
```python
OPTIMIZER_SETTINGS = {
    "population_size": 50,    # Individuos por generación
    "generations": 20,        # Número de generaciones
    "mutation_rate": 0.1,     # Probabilidad de mutación (10%)
    "crossover_rate": 0.8,    # Probabilidad de cruce (80%)
    "cpu_core_usage": 0.7     # Uso de CPU (70%)
}
```

#### Activar/Desactivar Estrategias
```python
{
    "nombre": "Reversión a la Media",
    "modo": "backtest",  # "backtest" = activa, "inactiva" = desactivada
    "pares": ["EURUSD", "USDJPY"],
    "optimizable_params": {
        "ema_reversion": {"min": 10, "max": 50, "step": 2}
    }
}
```

## 🚨 Solución de Problemas

### Errores Comunes

#### Error de Configuración
```bash
# Validar configuración
python trading_utils.py validate
```

#### Error de Imports
```bash
# Verificar estructura del proyecto
python trading_utils.py info

# Ejecutar test rápido
python trading_utils.py test
```

#### Optimización Lenta
```bash
# Usar modo rápido para pruebas
python run_optimization_enhanced.py --quick

# Reducir parámetros manualmente
python run_optimization_enhanced.py --generations 5 --population 10
```

#### Problemas de Memoria
```bash
# Limpiar archivos temporales
python trading_utils.py clean

# Usar menos núcleos de CPU (modificar config.py)
"cpu_core_usage": 0.5  # Usar solo 50% de CPU
```

## 📈 Flujo de Trabajo Recomendado

### 1. Configuración Inicial
```bash
# Validar sistema
python trading_utils.py validate

# Ejecutar tests
python run_tests.py
```

### 2. Prueba Rápida
```bash
# Test rápido de optimización
python run_optimization_enhanced.py --quick --verbose
```

### 3. Optimización Completa
```bash
# Optimización completa
python run_optimization_enhanced.py --verbose
```

### 4. Análisis de Resultados
- Revisar archivo JSON generado
- Analizar gráfico de convergencia
- Verificar métricas de rendimiento

## 🎯 Consejos de Uso

### Para Desarrollo
- Usar `--quick` para pruebas rápidas
- Ejecutar `run_tests.py` después de cambios
- Usar `--verbose` para debugging

### Para Producción
- Validar configuración antes de ejecutar
- Usar configuración completa (sin --quick)
- Monitorear logs para errores

### Para Optimización
- Empezar con pocos parámetros
- Incrementar generaciones gradualmente
- Usar profiling para identificar cuellos de botella

## 📞 Soporte

Si encuentras problemas:
1. Ejecuta `python trading_utils.py validate`
2. Revisa los logs en `trading_agent.log`
3. Ejecuta `python run_tests.py` para verificar integridad
4. Usa `python trading_utils.py clean` para limpiar archivos temporales