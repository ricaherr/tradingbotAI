"""
CacheManager - Sistema de cache para optimización de performance
Evita recálculos costosos en FASE 3
"""

import hashlib
import pickle
import os
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps


class CacheManager:
    """Gestor de cache para resultados de backtesting y cálculos costosos"""
    
    def __init__(self, cache_dir: str = "cache", max_age_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_age_seconds = max_age_hours * 3600
        self.stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "evictions": 0
        }
        
        # Crear directorio de cache si no existe
        os.makedirs(cache_dir, exist_ok=True)
    
    def _generate_key(self, data: Any) -> str:
        """Genera clave única para los datos"""
        # Convertir a string determinístico
        if isinstance(data, dict):
            # Ordenar claves para consistencia
            sorted_items = sorted(data.items())
            data_str = str(sorted_items)
        else:
            data_str = str(data)
        
        # Generar hash
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """Obtiene ruta del archivo de cache"""
        return os.path.join(self.cache_dir, f"{key}.cache")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Verifica si el cache es válido (no expirado)"""
        if not os.path.exists(cache_path):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_path)
        return file_age < self.max_age_seconds
    
    def get(self, key_data: Any) -> Optional[Any]:
        """Obtiene valor del cache"""
        key = self._generate_key(key_data)
        cache_path = self._get_cache_path(key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    result = pickle.load(f)
                self.stats["hits"] += 1
                return result
            except Exception:
                # Cache corrupto, eliminar
                try:
                    os.remove(cache_path)
                except:
                    pass
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key_data: Any, value: Any) -> None:
        """Guarda valor en cache"""
        key = self._generate_key(key_data)
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            self.stats["saves"] += 1
        except Exception as e:
            print(f"[WARNING] Error guardando cache: {e}")
    
    def clear_expired(self) -> int:
        """Limpia cache expirado"""
        cleared = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_path = os.path.join(self.cache_dir, filename)
                    if not self._is_cache_valid(cache_path):
                        os.remove(cache_path)
                        cleared += 1
                        self.stats["evictions"] += 1
        except Exception as e:
            print(f"[WARNING] Error limpiando cache: {e}")
        
        return cleared
    
    def clear_all(self) -> int:
        """Limpia todo el cache"""
        cleared = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
                    cleared += 1
        except Exception as e:
            print(f"[WARNING] Error limpiando cache: {e}")
        
        return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percent": hit_rate,
            "total_requests": total_requests
        }


# Cache global para backtesting
backtest_cache = CacheManager(cache_dir="cache/backtest", max_age_hours=24)
indicators_cache = CacheManager(cache_dir="cache/indicators", max_age_hours=48)


def cached_backtest(cache_manager: CacheManager = backtest_cache):
    """Decorador para cachear resultados de backtesting"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crear clave de cache basada en argumentos
            cache_key = {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Intentar obtener del cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


def cached_indicators(cache_manager: CacheManager = indicators_cache):
    """Decorador para cachear cálculos de indicadores"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Crear clave de cache
            cache_key = {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Intentar obtener del cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


class PerformanceMonitor:
    """Monitor de performance para identificar cuellos de botella"""
    
    def __init__(self):
        self.timings = {}
        self.call_counts = {}
    
    def time_function(self, name: str):
        """Decorador para medir tiempo de ejecución"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                if name not in self.timings:
                    self.timings[name] = []
                    self.call_counts[name] = 0
                
                self.timings[name].append(execution_time)
                self.call_counts[name] += 1
                
                return result
            return wrapper
        return decorator
    
    def get_report(self) -> Dict[str, Any]:
        """Genera reporte de performance"""
        report = {}
        
        for name, times in self.timings.items():
            total_time = sum(times)
            avg_time = total_time / len(times)
            max_time = max(times)
            min_time = min(times)
            call_count = self.call_counts[name]
            
            report[name] = {
                'total_time': total_time,
                'avg_time': avg_time,
                'max_time': max_time,
                'min_time': min_time,
                'call_count': call_count,
                'time_per_call': total_time / call_count
            }
        
        return report
    
    def print_report(self):
        """Imprime reporte de performance"""
        report = self.get_report()
        
        print("\n=== PERFORMANCE REPORT ===")
        print(f"{'Function':<25} {'Calls':<8} {'Total(s)':<10} {'Avg(s)':<10} {'Max(s)':<10}")
        print("-" * 70)
        
        # Ordenar por tiempo total descendente
        sorted_items = sorted(report.items(), key=lambda x: x[1]['total_time'], reverse=True)
        
        for name, stats in sorted_items:
            print(f"{name:<25} {stats['call_count']:<8} "
                  f"{stats['total_time']:<10.4f} {stats['avg_time']:<10.4f} "
                  f"{stats['max_time']:<10.4f}")
        
        print("-" * 70)


# Monitor global de performance
performance_monitor = PerformanceMonitor()