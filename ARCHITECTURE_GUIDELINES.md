# GUÍAS ARQUITECTURALES DEL SISTEMA DE TRADING

## CRITERIOS DE ACEPTACIÓN OBLIGATORIOS

### 1. PRINCIPIOS SOLID (Peso: 25%)

#### Single Responsibility Principle (SRP)
- ✅ **DEBE**: Cada clase tiene una sola razón para cambiar
- ❌ **NO DEBE**: Clases que manejan múltiples conceptos (God Objects)
- **Evaluación**: ¿La clase tiene más de 3 responsabilidades diferentes?

#### Open/Closed Principle (OCP)  
- ✅ **DEBE**: Extensible sin modificar código existente
- ❌ **NO DEBE**: Modificar clases base para agregar funcionalidad
- **Evaluación**: ¿Agregar nueva funcionalidad requiere cambiar código existente?

#### Liskov Substitution Principle (LSP)
- ✅ **DEBE**: Subclases intercambiables con clase base
- ❌ **NO DEBE**: Subclases que rompen contratos de la clase base
- **Evaluación**: ¿Las subclases pueden reemplazar la clase base sin problemas?

#### Interface Segregation Principle (ISP)
- ✅ **DEBE**: Interfaces específicas y cohesivas
- ❌ **NO DEBE**: Interfaces gordas que fuercen implementaciones innecesarias
- **Evaluación**: ¿Las clases implementan métodos que no usan?

#### Dependency Inversion Principle (DIP)
- ✅ **DEBE**: Depender de abstracciones, no de concreciones
- ❌ **NO DEBE**: Dependencias directas a implementaciones específicas
- **Evaluación**: ¿Las dependencias son inyectables y testeable?

### 2. CLEAN CODE (Peso: 20%)

#### Nomenclatura
- ✅ **DEBE**: Nombres descriptivos y sin ambigüedad
- ✅ **DEBE**: Consistencia en convenciones (snake_case para Python)
- ❌ **NO DEBE**: Abreviaciones crípticas o nombres genéricos
- **Evaluación**: ¿El código se lee como prosa en inglés/español?

#### Funciones
- ✅ **DEBE**: Funciones pequeñas (< 20 líneas idealmente)
- ✅ **DEBE**: Un solo nivel de abstracción por función
- ❌ **NO DEBE**: Funciones con más de 3 parámetros sin justificación
- **Evaluación**: ¿La función hace exactamente lo que su nombre indica?

#### Comentarios
- ✅ **DEBE**: Docstrings para clases y métodos públicos
- ✅ **DEBE**: Comentarios que explican "por qué", no "qué"
- ❌ **NO DEBE**: Código comentado o comentarios obsoletos
- **Evaluación**: ¿Los comentarios agregan valor real?

### 3. DOMINIO DE TRADING (Peso: 25%)

#### Precisión Financiera
- ✅ **DEBE**: Usar Decimal para cálculos monetarios críticos
- ✅ **DEBE**: Manejar correctamente spreads, slippage, comisiones
- ❌ **NO DEBE**: Usar float para cálculos de dinero
- **Evaluación**: ¿Los cálculos financieros son precisos al pip?

#### Gestión de Riesgo
- ✅ **DEBE**: Validar tamaños de posición antes de ejecutar
- ✅ **DEBE**: Implementar stop-loss y take-profit obligatorios
- ❌ **NO DEBE**: Permitir posiciones sin gestión de riesgo
- **Evaluación**: ¿Es imposible perder más del riesgo definido?

#### Timeframes y Datos
- ✅ **DEBE**: Manejar diferentes timeframes dinámicamente
- ✅ **DEBE**: Validar integridad de datos históricos
- ❌ **NO DEBE**: Hardcodear parámetros específicos de timeframe
- **Evaluación**: ¿Funciona correctamente en todos los timeframes?

#### Backtesting Realista
- ✅ **DEBE**: Simular condiciones reales de mercado
- ✅ **DEBE**: Evitar look-ahead bias y data snooping
- ❌ **NO DEBE**: Usar datos futuros para decisiones pasadas
- **Evaluación**: ¿Los resultados son replicables en vivo?

### 4. PERFORMANCE Y ESCALABILIDAD (Peso: 15%)

#### Eficiencia Algorítmica
- ✅ **DEBE**: Complejidad temporal razonable (O(n log n) máximo para operaciones críticas)
- ✅ **DEBE**: Uso eficiente de memoria
- ❌ **NO DEBE**: Algoritmos O(n²) en loops críticos
- **Evaluación**: ¿Escala bien con más datos/estrategias?

#### Paralelización
- ✅ **DEBE**: Operaciones CPU-intensivas paralelizables
- ✅ **DEBE**: Thread-safety en componentes compartidos
- ❌ **NO DEBE**: Bloqueos innecesarios o race conditions
- **Evaluación**: ¿Aprovecha múltiples cores eficientemente?

### 5. TESTABILIDAD Y MANTENIBILIDAD (Peso: 15%)

#### Testing
- ✅ **DEBE**: Cobertura de tests > 80% en lógica crítica
- ✅ **DEBE**: Tests unitarios independientes y rápidos
- ✅ **DEBE**: Tests de integración para flujos completos
- **Evaluación**: ¿Los tests fallan cuando el código está roto?

#### Configurabilidad
- ✅ **DEBE**: Parámetros externalizados en configuración
- ✅ **DEBE**: Validación de configuraciones al inicio
- ❌ **NO DEBE**: Magic numbers en el código
- **Evaluación**: ¿Se puede cambiar comportamiento sin recompilar?

#### Logging y Monitoreo
- ✅ **DEBE**: Logs estructurados con niveles apropiados
- ✅ **DEBE**: Métricas de performance y errores
- ❌ **NO DEBE**: Print statements en código de producción
- **Evaluación**: ¿Es fácil diagnosticar problemas en producción?

## PROCESO DE EVALUACIÓN

### Checklist de Revisión (Usar antes de implementar)

```
CRITERIOS OBLIGATORIOS (Todos deben ser ✅):
□ No viola ningún principio SOLID
□ Nombres descriptivos y consistentes  
□ Funciones < 20 líneas con responsabilidad única
□ Cálculos financieros precisos
□ Gestión de riesgo implementada
□ Manejo dinámico de timeframes
□ Tests unitarios incluidos
□ Configuración externalizada
□ Documentación actualizada

CRITERIOS DESEABLES (Al menos 7/10 deben ser ✅):
□ Complejidad algorítmica óptima
□ Paralelizable donde sea beneficioso
□ Cobertura de tests > 80%
□ Logs estructurados implementados
□ Métricas de performance incluidas
□ Validación de entrada robusta
□ Manejo de errores graceful
□ Compatibilidad con versiones anteriores
□ Documentación de API completa
□ Ejemplos de uso incluidos
```

### Sistema de Puntuación

**PUNTUACIÓN MÍNIMA PARA ACEPTACIÓN: 7.0/10**

- **9.0-10.0**: Excelente - Implementación ejemplar
- **8.0-8.9**: Muy Bueno - Cumple todos los criterios con calidad alta
- **7.0-7.9**: Aceptable - Cumple criterios mínimos, puede tener mejoras menores
- **6.0-6.9**: Necesita Mejoras - Requiere cambios antes de aceptar
- **< 6.0**: Rechazado - Requiere rediseño significativo

### Cálculo de Puntuación

```python
def calculate_score(solid_score, clean_code_score, trading_score, performance_score, maintainability_score):
    weights = {
        'solid': 0.25,
        'clean_code': 0.20, 
        'trading': 0.25,
        'performance': 0.15,
        'maintainability': 0.15
    }
    
    total_score = (
        solid_score * weights['solid'] +
        clean_code_score * weights['clean_code'] +
        trading_score * weights['trading'] +
        performance_score * weights['performance'] +
        maintainability_score * weights['maintainability']
    )
    
    return round(total_score, 1)
```

## PATRONES ARQUITECTURALES PREFERIDOS

### 1. Strategy Pattern
- **Cuándo usar**: Diferentes algoritmos para la misma tarea
- **Ejemplo**: Diferentes estrategias de trading, calculadoras de métricas

### 2. Factory Pattern  
- **Cuándo usar**: Creación de objetos complejos
- **Ejemplo**: Creación de calculadoras por timeframe

### 3. Observer Pattern
- **Cuándo usar**: Notificaciones de eventos
- **Ejemplo**: Notificaciones de señales de trading

### 4. Command Pattern
- **Cuándo usar**: Operaciones que pueden ser deshechas/rehechas
- **Ejemplo**: Órdenes de trading, operaciones de optimización

### 5. Repository Pattern
- **Cuándo usar**: Acceso a datos
- **Ejemplo**: Acceso a datos históricos, configuraciones

## ANTIPATRONES PROHIBIDOS

### 1. God Object
- **Descripción**: Clase que hace demasiadas cosas
- **Ejemplo**: TimeframeContext que maneja todo
- **Solución**: Dividir en clases especializadas

### 2. Magic Numbers
- **Descripción**: Números hardcodeados sin explicación
- **Ejemplo**: periods_per_year = 252
- **Solución**: Constantes nombradas o configuración

### 3. Shotgun Surgery
- **Descripción**: Un cambio requiere modificar muchas clases
- **Ejemplo**: Cambiar timeframe requiere tocar 10 archivos
- **Solución**: Centralizar lógica relacionada

### 4. Feature Envy
- **Descripción**: Clase que usa más métodos de otra clase que propios
- **Ejemplo**: Evaluator que accede constantemente a datos de Report
- **Solución**: Mover funcionalidad a la clase correcta

## REGLAS DE IMPLEMENTACIÓN

### Antes de Escribir Código
1. **Definir**: ¿Qué problema específico resuelve?
2. **Diseñar**: ¿Cómo encaja en la arquitectura existente?
3. **Evaluar**: ¿Cumple los criterios de aceptación?
4. **Planificar**: ¿Cómo se va a testear?

### Durante la Implementación
1. **Escribir tests primero** (TDD cuando sea posible)
2. **Refactorizar continuamente** para mantener calidad
3. **Documentar decisiones** arquitecturales importantes
4. **Validar** contra checklist regularmente

### Después de Implementar
1. **Ejecutar suite completa** de tests
2. **Revisar métricas** de calidad de código
3. **Actualizar documentación** si es necesario
4. **Planificar mejoras** futuras identificadas

---

**NOTA**: Estas reglas son evolutivas. Se actualizan basándose en lecciones aprendidas y nuevos requerimientos del dominio de trading.