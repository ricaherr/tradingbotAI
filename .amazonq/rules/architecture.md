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

**NOTA**: Estas reglas son obligatorias para TODAS las implementaciones y deben ser seguidas sin excepción.