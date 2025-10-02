# config.py

import os
import MetaTrader5 as mt5

# --- CONFIGURACIÓN DE CONEXIÓN Y ENTORNO ---
TIMEFRAME = mt5.TIMEFRAME_M1
MONEDA_DE_CUENTA = "USD"

# --- CONFIGURACIÓN DE LOGS Y ARCHIVOS ---
directorio_documentos = os.path.join(os.path.expanduser("~"), "Documents")
LOG_FILE_PATH = os.path.join(directorio_documentos, "trading_agent.log")
OPERACIONES_CSV = os.path.join(os.path.dirname(__file__), 'operaciones_trading.csv')

# --- PARÁMETROS DE TRADING ---
PARES_A_OPERAR = ["EURUSD", "GBPUSD", "USDJPY"]
NUM_VELAS = 200
MAX_OPERACIONES_SIMULTANEAS = 5
RELACION_RIESGO_BENEFICIO = 1.5 # Por cada $1 arriesgado, se buscan $1.5 de beneficio
TIEMPO_ESPERA_NUEVA_VELA = 5 # Segundos para esperar antes de buscar una nueva vela en modo live

# --- PARÁMETROS DE GESTIÓN DE RIESGO GLOBAL ---
CAPITAL_INICIAL = 1000
CAPITAL_INICIAL_BACKTESTING = 1000
RIESGO_PORCENTAJE = 1.0  # Riesgo por operación como porcentaje del capital
PERDIDA_MAXIMA_DIARIA = 0.02  # 2% del capital

# --- PARÁMETROS DE LOTE Y SPREAD ---
MAX_LOTE = 0.1
MIN_LOTE = 0.01
VALIDAR_SPREAD = False
MAX_SPREAD_PORCENTAJE_BENEFICIO = 0.05 # 5%

# --- PARÁMETROS DE GESTIÓN EN OPERACIÓN (TRAILING, BREAK-EVEN) ---
TRAILING_ACTIVO = True
BREAK_EVEN_ACTIVO = True
BREAK_EVEN_ATR_FACTOR = 0.5  # Mover a BE cuando el beneficio es 0.5 * ATR
TRAILING_ATR_FACTOR = 1.0    # Mantener el trailing a 1.0 * ATR
DEVIATION_ATR_FACTOR = 0.1   # Multiplicador del ATR para la desviación de la orden

# --- PARÁMETROS DE REDUCCIÓN DE POSICIÓN ---
REDUCIR_POSICION_ACTIVO = True
PERDIDAS_CONSECUTIVAS_REDUCCION = 3  # Reducir lote después de N pérdidas
FACTOR_REDUCCION_LOTE = 0.75         # Reducir el lote al 75%

# --- PARÁMETROS BASE DE ESTRATEGIAS ---
ATR_PERIOD = 14
MULTI_VELA_ELEFANTE = 2.0
EMA_PERIOD_DEFAULT = 20
DESVIACION_THRESHOLD_DEFAULT = 1.0

ESTRATEGIAS = [
    {
        "nombre": "Cruce EMA + Vela Elefante",
        "modo": "backtest", # Activada para pruebas multi-timeframe
        "pares": ["EURUSD", "GBPUSD", "USDJPY", "EURJPY"],
        "optimizable_params": {
            "timeframe": {"min": 0, "max": 5, "step": 1}, # 0=M1, 1=M5, 2=M15, 3=M30, 4=H1, 5=H4
            "ema_corta": {"min": 5, "max": 25, "step": 2},
            "ema_larga": {"min": 26, "max": 60, "step": 3},
            "atr_period": {"min": 8, "max": 25, "step": 2},
            "multi_vela_elefante": {"min": 1.2, "max": 4.0, "step": 0.2},
            "riesgo_porcentaje": {"min": 0.5, "max": 3.0, "step": 0.25},
            "relacion_riesgo_beneficio": {"min": 1.0, "max": 3.0, "step": 0.25}
        }
    },
    {
        "nombre": "Rompimiento de la EMA 20",
        "modo": "backtest", # Cambiar a backtest para pruebas
        "pares": ["EURUSD", "GBPUSD", "USDJPY"],
        "ema_period": 23, # Optimizado
        "ATR_PERIOD": 8, # Optimizado
        "riesgo_porcentaje": 2.0, # Optimizado
        "relacion_riesgo_beneficio": 2.0, # Optimizado
        "confirmacion_velas": 3, # Optimizado
        "optimizable_params": {
            "timeframe": {"min": 0, "max": 5, "step": 1}, # 0=M1, 1=M5, 2=M15, 3=M30, 4=H1, 5=H4
            "ema_period": {"min": 15, "max": 30, "step": 2},
            "ATR_PERIOD": {"min": 8, "max": 25, "step": 2},
            "riesgo_porcentaje": {"min": 0.5, "max": 3.0, "step": 0.25},
            "relacion_riesgo_beneficio": {"min": 1.0, "max": 3.0, "step": 0.25},
            "confirmacion_velas": {"min": 1, "max": 3, "step": 1}
        }
    },
    {
        "nombre": "Reversión a la Media",
        "modo": "backtest", # Activada para pruebas multi-timeframe
        "pares": ["EURUSD", "USDJPY", "AUDUSD", "NZDUSD"],
        "ema_reversion": 20,  # Parámetro base
        "desviacion_threshold": 1.5,  # Parámetro base
        "usar_filtro_tendencia": 1,  # Parámetro base
        "riesgo_porcentaje": 2.0,  # Parámetro base
        "relacion_riesgo_beneficio": 2.0,  # Parámetro base
        "min_distancia_ema": 0.002,  # Parámetro base
        "optimizable_params": {
            "timeframe": {"min": 0, "max": 5, "step": 1}, # 0=M1, 1=M5, 2=M15, 3=M30, 4=H1, 5=H4
            "ema_reversion": {"min": 14, "max": 30, "step": 2},  # Rango más enfocado
            "desviacion_threshold": {"min": 1.0, "max": 2.0, "step": 0.1},  # Rango más preciso
            "usar_filtro_tendencia": {"min": 0, "max": 1, "step": 1}, # 0=False, 1=True
            "riesgo_porcentaje": {"min": 1.0, "max": 2.5, "step": 0.25},  # Riesgo más conservador
            "relacion_riesgo_beneficio": {"min": 1.5, "max": 2.5, "step": 0.25},  # RR más realista
            "min_distancia_ema": {"min": 0.001, "max": 0.003, "step": 0.0002}  # Distancia más realista
        }
    }
]

# --- PARÁMETROS DEL OPTIMIZADOR GENÉTICO ---
OPTIMIZER_SETTINGS = {
    "population_size": 50,    # Tamaño de la población por generación
    "generations": 20,        # Número de generaciones a evolucionar
    "mutation_rate": 0.1,      # Probabilidad de que un gen mute (10%)
    "crossover_rate": 0.8,     # Probabilidad de que dos padres se crucen (80%)
    "tournament_size": 3,      # Número de individuos a seleccionar para el torneo
    "cpu_core_usage": 0.7      # Porcentaje de núcleos de CPU a utilizar (0.7 = 70%)
}

# --- CONFIGURACIÓN DE TIMEFRAMES ---
TIMEFRAMES_CONFIG = {
    "M1": {"mt5_code": 1, "name": "1 Minuto", "velas_needed": 2000},
    "M5": {"mt5_code": 5, "name": "5 Minutos", "velas_needed": 1500},
    "M15": {"mt5_code": 15, "name": "15 Minutos", "velas_needed": 1200},
    "M30": {"mt5_code": 30, "name": "30 Minutos", "velas_needed": 1000},
    "H1": {"mt5_code": 16385, "name": "1 Hora", "velas_needed": 800},
    "H4": {"mt5_code": 16388, "name": "4 Horas", "velas_needed": 500}
}

# --- CONFIGURACIÓN DE OPTIMIZACIÓN MULTI-ESTRATEGIA ---
MULTI_STRATEGY_SETTINGS = {
    "optimization_mode": "sequential",  # "sequential", "parallel", "portfolio"
    "strategy_selection": "active_only", # "active_only", "all", "custom"
    "portfolio_weights": "equal",       # "equal", "optimized", "manual"
    "comparison_metric": "sharpe_ratio", # "sharpe_ratio", "profit_neto", "calmar_ratio"
    "enable_strategy_ranking": True,     # Generar ranking de estrategias
    "save_individual_results": True,     # Guardar resultados por estrategia
    "cross_validation": False,           # Validación cruzada (más lento)
    "test_all_timeframes": True,         # Probar todos los timeframes
    "timeframes_to_test": ["M1", "M5", "M15", "M30", "H1"]
}

# --- CONFIGURACIÓN DE OPTIMIZACIÓN POR TIMEFRAMES ---
TIMEFRAME_OPTIMIZATION = {
    "mode": "full",  # "single", "screening", "hybrid", "full"
    "screening_generations": 4,    # Generaciones para screening inicial
    "full_generations": 20,        # Generaciones para análisis completo
    "hybrid_deep_generations": 15,  # Generaciones para fase profunda en modo hybrid
    "min_profitability_threshold": 0.5,  # ROI mínimo % para pasar screening
    "top_timeframes_to_optimize": 3,      # Cuántos mejores timeframes optimizar completamente
    "enable_timeframe_comparison": True,   # Generar reporte comparativo
    "statistical_confidence": 0.95,       # Nivel de confianza estadística
    "save_detailed_results": True,        # Guardar resultados detallados por timeframe
    "backtest_period_days": 365,          # Período de backtest en días (default: 1 año)
    "default_timeframes": ["M1", "M5", "M15", "M30", "H1"]  # Timeframes por defecto
}

# --- VALIDACIÓN DE CONFIGURACIÓN ---
def validar_configuracion():
    """Valida la configuración al inicio del sistema."""
    errores = []
    
    # Validar parámetros básicos
    if CAPITAL_INICIAL <= 0:
        errores.append("CAPITAL_INICIAL debe ser mayor a 0")
    if RIESGO_PORCENTAJE <= 0 or RIESGO_PORCENTAJE > 100:
        errores.append("RIESGO_PORCENTAJE debe estar entre 0 y 100")
    if MIN_LOTE <= 0 or MAX_LOTE <= MIN_LOTE:
        errores.append("MIN_LOTE debe ser positivo y menor que MAX_LOTE")
    if RELACION_RIESGO_BENEFICIO <= 0:
        errores.append("RELACION_RIESGO_BENEFICIO debe ser mayor a 0")
    
    # Validar estrategias
    for estrategia in ESTRATEGIAS:
        if "nombre" not in estrategia:
            errores.append(f"Estrategia sin nombre encontrada")
            continue
            
        nombre = estrategia["nombre"]
        if "optimizable_params" in estrategia:
            for param, config in estrategia["optimizable_params"].items():
                if "min" not in config or "max" not in config:
                    errores.append(f"Estrategia '{nombre}': parámetro '{param}' necesita 'min' y 'max'")
                elif config["min"] >= config["max"]:
                    errores.append(f"Estrategia '{nombre}': '{param}' min debe ser menor que max")
                if "step" in config and config["step"] <= 0:
                    errores.append(f"Estrategia '{nombre}': '{param}' step debe ser mayor a 0")
    
    # Validar optimizador
    if OPTIMIZER_SETTINGS["population_size"] < 2:
        errores.append("population_size debe ser al menos 2")
    if OPTIMIZER_SETTINGS["generations"] < 1:
        errores.append("generations debe ser al menos 1")
    if not (0 <= OPTIMIZER_SETTINGS["mutation_rate"] <= 1):
        errores.append("mutation_rate debe estar entre 0 y 1")
    if not (0 <= OPTIMIZER_SETTINGS["crossover_rate"] <= 1):
        errores.append("crossover_rate debe estar entre 0 y 1")
    if not (0 < OPTIMIZER_SETTINGS["cpu_core_usage"] <= 1):
        errores.append("cpu_core_usage debe estar entre 0 y 1")
    
    # Validar configuración multi-estrategia
    valid_modes = ["sequential", "parallel", "portfolio"]
    if MULTI_STRATEGY_SETTINGS["optimization_mode"] not in valid_modes:
        errores.append(f"optimization_mode debe ser uno de: {valid_modes}")
    
    valid_selections = ["active_only", "all", "custom"]
    if MULTI_STRATEGY_SETTINGS["strategy_selection"] not in valid_selections:
        errores.append(f"strategy_selection debe ser uno de: {valid_selections}")
    
    valid_weights = ["equal", "optimized", "manual"]
    if MULTI_STRATEGY_SETTINGS["portfolio_weights"] not in valid_weights:
        errores.append(f"portfolio_weights debe ser uno de: {valid_weights}")
    
    if errores:
        print("\n[ERROR] ERRORES DE CONFIGURACION DETECTADOS:")
        for error in errores:
            print(f"  • {error}")
        print("\nPor favor corrige estos errores antes de continuar.\n")
        return False
    
    print("[OK] Configuración validada correctamente")
    print(f"[INFO] Modo de optimización: {MULTI_STRATEGY_SETTINGS['optimization_mode']}")
    return True
def validar_estrategia(estrategia_config):
    """Valida una configuración específica de estrategia."""
    errores = []
    
    if not estrategia_config:
        return ["Configuración de estrategia vacía"]
    
    nombre = estrategia_config.get("nombre", "Sin nombre")
    
    # Validar parámetros específicos por estrategia
    if "optimizable_params" in estrategia_config:
        for param, valor in estrategia_config.items():
            if param in estrategia_config["optimizable_params"]:
                config_param = estrategia_config["optimizable_params"][param]
                if valor < config_param["min"] or valor > config_param["max"]:
                    errores.append(f"Estrategia '{nombre}': {param}={valor} fuera del rango [{config_param['min']}, {config_param['max']}]")
    
    # Validaciones específicas por tipo de estrategia
    if "ema_corta" in estrategia_config and "ema_larga" in estrategia_config:
        if estrategia_config["ema_corta"] >= estrategia_config["ema_larga"]:
            errores.append(f"Estrategia '{nombre}': ema_corta debe ser menor que ema_larga")
    
    return errores

def validar_datos_mercado(df):
    """Valida que los datos de mercado sean correctos."""
    errores = []
    
    if df is None or df.empty:
        return ["DataFrame de datos vacío o None"]
    
    columnas_requeridas = ['open', 'high', 'low', 'close']
    for col in columnas_requeridas:
        if col not in df.columns:
            errores.append(f"Columna requerida '{col}' no encontrada")
    
    if not errores:
        # Validar lógica de precios
        if (df['high'] < df['low']).any():
            errores.append("Datos inválidos: high < low detectado")
        if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
            errores.append("Datos inválidos: high menor que open/close detectado")
        if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
            errores.append("Datos inválidos: low mayor que open/close detectado")
    
    return errores