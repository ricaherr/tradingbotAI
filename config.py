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

# --- PARÁMETROS DE GESTIÓN DE RIESGO GLOBAL ---
CAPITAL_INICIAL = 11000
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

# --- PARÁMETROS DE ESTRATEGIAS ---
ATR_PERIOD = 14
MULTI_VELA_ELEFANTE = 2.0

ESTRATEGIAS = [
    {
        "nombre": "Cruce EMA + Vela Elefante",
        "activa": True,
        "pares": ["EURUSD", "GBPUSD", "USDJPY", "EURJPY"]
    },
    {
        "nombre": "Rompimiento de la EMA 20",
        "activa": True,
        "pares": ["EURUSD", "GBPUSD", "USDJPY"]
    },
    {
        "nombre": "Reversión a la Media",
        "activa": True,
        "criterios": { # Criterios específicos que no están en config
            "usar_filtro_tendencia_200_ema": True
        },
        "pares": ["EURUSD", "USDJPY", "AUDUSD", "NZDUSD"]
    }
]