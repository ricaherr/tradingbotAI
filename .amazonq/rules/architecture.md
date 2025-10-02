# REGLAS ARQUITECTURALES OBLIGATORIAS

## CRITERIOS DE ACEPTACIÓN MÍNIMOS (Puntuación ≥ 7.0/10)

### SOLID Principles (25%)
- ✅ Single Responsibility: Una clase, una razón para cambiar
- ✅ Open/Closed: Extensible sin modificar código existente  
- ✅ Liskov Substitution: Subclases intercambiables
- ✅ Interface Segregation: Interfaces específicas y cohesivas
- ✅ Dependency Inversion: Depender de abstracciones

### Clean Code (20%)
- ✅ Nombres descriptivos y consistentes
- ✅ Funciones < 20 líneas con responsabilidad única
- ✅ Docstrings para métodos públicos
- ❌ NO magic numbers o código hardcodeado

### Dominio Trading (25%)
- ✅ Cálculos financieros precisos (usar Decimal para dinero)
- ✅ Gestión de riesgo obligatoria (SL/TP)
- ✅ Manejo dinámico de timeframes (NO hardcodear)
- ✅ Backtesting realista sin look-ahead bias

### Performance (15%)
- ✅ Complejidad algorítmica razonable (≤ O(n log n))
- ✅ Operaciones CPU-intensivas paralelizables
- ✅ Thread-safety en componentes compartidos

### Mantenibilidad (15%)
- ✅ Tests unitarios para lógica crítica
- ✅ Configuración externalizada
- ✅ Logs estructurados con niveles apropiados
- ✅ Documentación actualizada

## CHECKLIST OBLIGATORIO ANTES DE IMPLEMENTAR

```
CRITERIOS OBLIGATORIOS (Todos ✅):
□ No viola principios SOLID
□ Nombres descriptivos y consistentes  
□ Funciones < 20 líneas
□ Cálculos financieros precisos
□ Gestión de riesgo implementada
□ Manejo dinámico de timeframes
□ Tests unitarios incluidos
□ Configuración externalizada
□ Documentación actualizada
□ Diagnósticos relacionados ejecutados
□ Diagnóstico específico creado (si aplica)
```

## ANTIPATRONES PROHIBIDOS
- ❌ God Objects (clases que hacen todo)
- ❌ Magic Numbers (valores hardcodeados)
- ❌ Shotgun Surgery (un cambio afecta muchas clases)
- ❌ Feature Envy (clase usa más métodos de otra que propios)

## PATRONES PREFERIDOS
- ✅ Strategy Pattern (diferentes algoritmos)
- ✅ Factory Pattern (creación de objetos complejos)
- ✅ Repository Pattern (acceso a datos)
- ✅ Observer Pattern (notificaciones de eventos)

## REGLAS DE IMPLEMENTACIÓN
1. **Evaluar** contra criterios ANTES de escribir código
2. **Diseñar** cómo encaja en arquitectura existente
3. **Escribir tests** primero cuando sea posible
4. **Refactorizar** continuamente para mantener calidad
5. **Documentar** decisiones arquitecturales importantes
6. **Ejecutar diagnósticos** relacionados con la solución terminada
7. **Crear diagnóstico específico** si la solución lo amerita y no existe uno equivalente

## REGLAS DE DIAGNÓSTICOS (OBLIGATORIAS)

### Cuándo Ejecutar Diagnósticos
- ✅ **SIEMPRE** después de completar una solución significativa
- ✅ **SIEMPRE** después de cambios arquitecturales importantes
- ✅ **SIEMPRE** antes de considerar una fase como "completada"
- ✅ Antes de hacer merge a rama principal
- ✅ Después de refactoring mayor

### Cuándo Crear Nuevo Diagnóstico
- ✅ La solución introduce **componentes nuevos** críticos
- ✅ La solución modifica **flujos principales** del sistema
- ✅ **NO existe** diagnóstico que valide la misma funcionalidad
- ✅ La solución tiene **riesgo alto** de regresión
- ❌ **NO crear** si ya existe diagnóstico equivalente

### Ubicación y Nomenclatura
- ✅ **Ubicación**: `diagnostics/diagnostic_[componente].py`
- ✅ **Nomenclatura**: Descriptiva y específica
- ✅ **Estructura**: Seguir plantilla estándar del README
- ✅ **Documentación**: Actualizar `diagnostics/README.md`

### Criterios de Calidad para Diagnósticos
- ✅ **Cobertura completa** del componente/funcionalidad
- ✅ **Tests independientes** que no dependan de estado externo
- ✅ **Mensajes claros** de éxito/fallo
- ✅ **Códigos de salida** apropiados (0=éxito, 1=fallo)
- ✅ **Validación de casos extremos**

**NOTA**: Estas reglas son obligatorias para TODAS las implementaciones y deben ser seguidas sin excepción.