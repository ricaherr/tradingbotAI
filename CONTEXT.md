# CONTEXT.md: Contexto del Proyecto "Estrategia IA"

Este documento sirve como una guía de referencia rápida para entender los objetivos, la arquitectura y las funcionalidades del proyecto `estrategia-IA`.

## 1. Objetivos del Proyecto

El objetivo principal del proyecto es diseñar, desarrollar y operar un **framework para el trading algorítmico** en mercados financieros. Las metas específicas son:

- **Automatización:** Crear y probar estrategias de trading que puedan ejecutarse de forma automática o semi-automática.
- **Optimización:** Encontrar los parámetros óptimos para cada estrategia con el fin de maximizar su rendimiento.
- **Backtesting Riguroso:** Evaluar la viabilidad de las estrategias contra datos históricos antes de ponerlas en operación.
- **Gestión de Riesgo:** Implementar y aplicar reglas de gestión de riesgo de forma sistemática en todas las operaciones.

## 2. Funcionalidades Clave

El proyecto está estructurado en módulos que representan sus funcionalidades principales:

- **Gestión de Datos (`/data`, `download_data.py`):** Descarga y almacenamiento de datos históricos del mercado.
- **Cálculo de Indicadores (`src/estrategia_ia/core/indicadores.py`):** Utiliza la librería `TA-Lib` para calcular una amplia variedad de indicadores técnicos.
- **Motor de Estrategias (`src/estrategia_ia/core/strategies.py`):** Define la lógica de trading. Actualmente se exploran estrategias como "Cruce de EMAs con Vela Elefante" y "Reversión a la Media", configuradas mediante archivos JSON.
- **Backtesting (`src/estrategia_ia/backtesting/backtester.py`):** Permite simular la ejecución de una estrategia sobre datos pasados para medir su rendimiento.
- **Optimización de Parámetros (`src/estrategia_ia/optimization`):** Módulos para evaluar y ajustar los parámetros de una estrategia y encontrar la configuración más rentable.
- **Gestión de Riesgo (`src/estrategia_ia/risk_management`):** Componentes dedicados a calcular el tamaño de la posición, stop-loss, take-profit, etc.
- **Ejecución de Trading (`src/estrategia_ia/trading`):** Incluye un simulador de broker y un agente de trading que puede ejecutar las órdenes.
- **Utilidades (`src/estrategia_ia/utils`):** Módulos para enviar notificaciones y registrar las operaciones realizadas.

## 3. Decisiones de Arquitectura

- **Lenguaje:** Python 3.
- **Librería de Análisis Técnico:** El proyecto depende de una versión específica de **TA-Lib para Windows de 64 bits**, ubicada en el directorio `lib/`. Esta no es una dependencia estándar instalada vía `pip` y es crucial para el cálculo de indicadores.
- **Estructura del Proyecto:** Se sigue una estructura modular con el código fuente principal dentro de la carpeta `src/`, separando claramente las responsabilidades (core, backtesting, optimización, etc.).
- **Configuración de Estrategias:** Las estrategias se pueden configurar mediante archivos **JSON** (`.json`), lo que permite definir o modificar parámetros sin cambiar el código fuente.
- **Testing:** Se utiliza `pytest` para las pruebas unitarias, como se evidencia por la estructura del directorio `tests/` y los archivos de caché.
- **Integración Continua (CI):** Existe una configuración básica para GitHub Actions (`.github/workflows/main.yml`), probablemente para ejecutar tests automáticamente.

## 4. Reglas y Contexto Adicional

- **Dependencia Crítica de TA-Lib:** Cualquier nuevo entorno de desarrollo debe configurar correctamente la ruta a la librería `TA-Lib` local que se encuentra en el proyecto. Sin ella, los cálculos de indicadores fallarán.
- **Flujo de Trabajo:**
    1. Se descargan los datos con `download_data.py`.
    2. Se define o ajusta una estrategia en el código o en su `.json` correspondiente.
    3. Se ejecuta una optimización con `run_optimization.py` para encontrar los mejores parámetros.
    4. Se realiza un backtesting detallado de la estrategia con los parámetros optimizados.
    5. (A futuro) Se activa el `trading_agent` para operar en un entorno simulado o real.
