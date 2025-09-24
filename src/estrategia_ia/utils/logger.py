import logging
import os
from estrategia_ia import config

def setup_logger(name, level=logging.INFO):
    """Configura un logger específico para cada módulo."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Evitar duplicar handlers
        logger.setLevel(level)
        
        # Handler para archivo
        file_handler = logging.FileHandler(config.LOG_FILE_PATH, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formato detallado para archivo
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
        logger.propagate = False  # Evitar logging duplicado
    
    return logger

# Loggers específicos por módulo
engine_logger = setup_logger('engine')
broker_logger = setup_logger('broker')
strategy_logger = setup_logger('strategy')
optimizer_logger = setup_logger('optimizer')
data_logger = setup_logger('data')