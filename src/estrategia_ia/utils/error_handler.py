import time
import functools
from estrategia_ia.utils.logger import broker_logger, data_logger

def retry_on_failure(max_retries=3, delay=1, exceptions=(Exception,)):
    """Decorador para reintentar operaciones que fallan."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        broker_logger.warning(f"Intento {attempt + 1} falló para {func.__name__}: {e}. Reintentando en {delay}s...")
                        time.sleep(delay)
                    else:
                        broker_logger.error(f"Todos los intentos fallaron para {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator

def safe_execute(func, default_return=None, log_errors=True):
    """Ejecuta una función de forma segura, devolviendo un valor por defecto si falla."""
    try:
        return func()
    except Exception as e:
        if log_errors:
            data_logger.error(f"Error en ejecución segura de {func.__name__ if hasattr(func, '__name__') else 'función'}: {e}")
        return default_return

def validate_mt5_response(response, operation_name="operación MT5"):
    """Valida respuestas de MT5 y maneja errores comunes."""
    if response is None:
        raise ConnectionError(f"MT5 devolvió None para {operation_name}")
    
    if hasattr(response, 'retcode'):
        if response.retcode != 10009:  # TRADE_RETCODE_DONE
            error_msg = getattr(response, 'comment', f'Error código: {response.retcode}')
            raise RuntimeError(f"{operation_name} falló: {error_msg}")
    
    return response