"""
Optimizador Multi-Timeframe con 4 modos de operación:
- single: Todos los timeframes en una optimización (modo actual)
- screening: Screening rápido de todos los timeframes
- hybrid: Screening + optimización profunda de mejores timeframes
- full: Optimización completa separada por timeframe
"""

import time
from typing import Dict, List, Tuple, Any
from ..config import TIMEFRAME_OPTIMIZATION, OPTIMIZER_SETTINGS, TIMEFRAMES_CONFIG
from .optimizer import GeneticOptimizer
from ..core.data_manager import asegurar_datos_historicos

class TimeframeOptimizer:
    def __init__(self, strategy_config: Dict[str, Any], timeframes: List[str] = None, backtest_days: int = None, generations: int = None, population_size: int = None):
        self.strategy_config = strategy_config
        self.strategy_name = strategy_config.get("nombre", "Estrategia")
        self.timeframes = timeframes or TIMEFRAME_OPTIMIZATION["default_timeframes"]
        self.backtest_days = backtest_days or TIMEFRAME_OPTIMIZATION["backtest_period_days"]
        self.generations = generations or OPTIMIZER_SETTINGS["generations"]
        self.population_size = population_size or OPTIMIZER_SETTINGS["population_size"]
        self.results = {}
        
    def optimize(self, mode: str = None) -> Dict[str, Any]:
        """Ejecuta optimización según el modo especificado."""
        mode = mode or TIMEFRAME_OPTIMIZATION["mode"]
        
        print(f"\n=== OPTIMIZACIÓN MULTI-TIMEFRAME: {self.strategy_name} ===")
        print(f"Modo: {mode.upper()}")
        print(f"Timeframes: {', '.join(self.timeframes)}")
        print(f"Período backtest: {self.backtest_days} días")
        
        if mode == "single":
            return self._optimize_single()
        elif mode == "screening":
            return self._optimize_screening()
        elif mode == "hybrid":
            return self._optimize_hybrid()
        elif mode == "full":
            return self._optimize_full_separate()
        else:
            raise ValueError(f"Modo '{mode}' no válido. Usar: single, screening, hybrid, full")
    
    def _optimize_single(self) -> Dict[str, Any]:
        """Modo SINGLE: Todos los timeframes en una optimización (modo actual)."""
        print("Ejecutando optimización con todos los timeframes simultáneamente...")
        
        # Obtener datos por defecto (H1)
        data_file = asegurar_datos_historicos(
            simbolo="EURUSD",
            timeframe=16385,  # H1
            num_velas=800,
            min_velas=400,
            max_age_days=7
        )
        
        if not data_file:
            raise Exception("No se pudieron obtener datos para optimización")
        
        optimizer = GeneticOptimizer(self.strategy_config, data_file, 
                                   population_size=self.population_size, 
                                   generations=self.generations)
        start_time = time.time()
        
        result, _ = optimizer.run_optimization()
        
        execution_time = time.time() - start_time
        
        return {
            "mode": "single",
            "execution_time": execution_time,
            "best_result": result,
            "timeframes_tested": self.timeframes,
            "backtest_days": self.backtest_days,
            "total_evaluations": OPTIMIZER_SETTINGS["population_size"] * OPTIMIZER_SETTINGS["generations"]
        }
    
    def _optimize_screening(self) -> Dict[str, Any]:
        """Modo SCREENING: Screening rápido de todos los timeframes."""
        print("Ejecutando screening rápido en todos los timeframes...")
        
        screening_results = {}
        total_time = 0
        
        for timeframe in self.timeframes:
            print(f"\n--- Screening {timeframe} ({TIMEFRAMES_CONFIG[timeframe]['name']}) ---")
            
            # Crear configuración específica para este timeframe
            tf_config = self._create_single_timeframe_config(timeframe)
            
            # Obtener datos para este timeframe
            data_file = self._get_timeframe_data(timeframe)
            if not data_file:
                print(f"[ERROR] No se pudieron obtener datos para {timeframe}")
                continue
            
            optimizer = GeneticOptimizer(tf_config, data_file,
                                       population_size=self.population_size,
                                       generations=TIMEFRAME_OPTIMIZATION["screening_generations"])
            start_time = time.time()
            
            # Optimización con pocas generaciones
            original_generations = OPTIMIZER_SETTINGS["generations"]
            OPTIMIZER_SETTINGS["generations"] = TIMEFRAME_OPTIMIZATION["screening_generations"]
            
            result, _ = optimizer.run_optimization()
            
            # Restaurar configuración original
            OPTIMIZER_SETTINGS["generations"] = original_generations
            
            execution_time = time.time() - start_time
            total_time += execution_time
            
            screening_results[timeframe] = {
                "result": result,
                "execution_time": execution_time,
                "evaluations": OPTIMIZER_SETTINGS["population_size"] * TIMEFRAME_OPTIMIZATION["screening_generations"]
            }
            
            roi_mensual = result.get("roi_mensual_pct", result.get("roi_mensual", 0))
            print(f"ROI Mensual: {roi_mensual:.2f}%")
        
        # Ranking de timeframes
        ranked_timeframes = self._rank_timeframes(screening_results)
        
        return {
            "mode": "screening",
            "execution_time": total_time,
            "timeframe_results": screening_results,
            "timeframe_ranking": ranked_timeframes,
            "total_evaluations": len(self.timeframes) * OPTIMIZER_SETTINGS["population_size"] * TIMEFRAME_OPTIMIZATION["screening_generations"]
        }
    
    def _optimize_hybrid(self) -> Dict[str, Any]:
        """Modo HYBRID: Screening + optimización profunda de mejores timeframes."""
        print("Ejecutando optimización híbrida...")
        
        # Fase 1: Screening
        print("\n=== FASE 1: SCREENING ===")
        screening_result = self._optimize_screening()
        
        # Seleccionar mejores timeframes
        top_timeframes = screening_result["timeframe_ranking"][:TIMEFRAME_OPTIMIZATION["top_timeframes_to_optimize"]]
        
        print(f"\n=== FASE 2: OPTIMIZACIÓN PROFUNDA ===")
        print(f"Timeframes seleccionados: {[tf['timeframe'] for tf in top_timeframes]}")
        
        # Fase 2: Optimización profunda
        deep_results = {}
        deep_time = 0
        
        for tf_data in top_timeframes:
            timeframe = tf_data["timeframe"]
            print(f"\n--- Optimización profunda {timeframe} ---")
            
            tf_config = self._create_single_timeframe_config(timeframe)
            
            # Obtener datos para este timeframe
            data_file = self._get_timeframe_data(timeframe)
            if not data_file:
                print(f"[ERROR] No se pudieron obtener datos para {timeframe}")
                continue
            
            optimizer = GeneticOptimizer(tf_config, data_file,
                                       population_size=self.population_size,
                                       generations=TIMEFRAME_OPTIMIZATION["hybrid_deep_generations"])
            start_time = time.time()
            
            # Optimización con más generaciones
            original_generations = OPTIMIZER_SETTINGS["generations"]
            OPTIMIZER_SETTINGS["generations"] = TIMEFRAME_OPTIMIZATION["hybrid_deep_generations"]
            
            result, _ = optimizer.run_optimization()
            
            OPTIMIZER_SETTINGS["generations"] = original_generations
            
            execution_time = time.time() - start_time
            deep_time += execution_time
            
            deep_results[timeframe] = {
                "result": result,
                "execution_time": execution_time,
                "evaluations": OPTIMIZER_SETTINGS["population_size"] * TIMEFRAME_OPTIMIZATION["hybrid_deep_generations"]
            }
        
        total_time = screening_result["execution_time"] + deep_time
        
        return {
            "mode": "hybrid",
            "execution_time": total_time,
            "screening_results": screening_result["timeframe_results"],
            "deep_optimization_results": deep_results,
            "final_ranking": self._rank_timeframes(deep_results),
            "total_evaluations": screening_result["total_evaluations"] + sum(r["evaluations"] for r in deep_results.values())
        }
    
    def _optimize_full_separate(self) -> Dict[str, Any]:
        """Modo FULL: Optimización completa separada por timeframe."""
        print("Ejecutando optimización completa separada por timeframe...")
        
        full_results = {}
        total_time = 0
        
        for timeframe in self.timeframes:
            print(f"\n--- Optimización completa {timeframe} ({TIMEFRAMES_CONFIG[timeframe]['name']}) ---")
            
            tf_config = self._create_single_timeframe_config(timeframe)
            
            # Obtener datos para este timeframe
            data_file = self._get_timeframe_data(timeframe)
            if not data_file:
                print(f"[ERROR] No se pudieron obtener datos para {timeframe}")
                continue
            
            optimizer = GeneticOptimizer(tf_config, data_file,
                                       population_size=self.population_size,
                                       generations=self.generations)
            start_time = time.time()
            
            # Usar configuración completa
            result, _ = optimizer.run_optimization()
            
            execution_time = time.time() - start_time
            total_time += execution_time
            
            full_results[timeframe] = {
                "result": result,
                "execution_time": execution_time,
                "evaluations": OPTIMIZER_SETTINGS["population_size"] * OPTIMIZER_SETTINGS["generations"]
            }
            
            roi_mensual = result.get("roi_mensual_pct", result.get("roi_mensual", 0))
            print(f"ROI Mensual: {roi_mensual:.2f}%")
        
        # Ranking final
        ranked_timeframes = self._rank_timeframes(full_results)
        
        return {
            "mode": "full",
            "execution_time": total_time,
            "timeframe_results": full_results,
            "timeframe_ranking": ranked_timeframes,
            "total_evaluations": len(self.timeframes) * OPTIMIZER_SETTINGS["population_size"] * OPTIMIZER_SETTINGS["generations"]
        }
    
    def _create_single_timeframe_config(self, timeframe: str) -> Dict[str, Any]:
        """Crea configuración para optimizar un solo timeframe."""
        config = self.strategy_config.copy()
        
        # Remover timeframe de parámetros optimizables
        if "optimizable_params" in config and "timeframe" in config["optimizable_params"]:
            config["optimizable_params"] = config["optimizable_params"].copy()
            del config["optimizable_params"]["timeframe"]
        
        # Fijar timeframe específico
        timeframe_index = self.timeframes.index(timeframe)
        config["fixed_timeframe"] = timeframe_index
        config["timeframe_name"] = timeframe
        config["backtest_days"] = self.backtest_days
        
        return config
    
    def _get_timeframe_data(self, timeframe: str) -> str:
        """Obtiene archivo de datos para el timeframe especificado."""
        tf_config = TIMEFRAMES_CONFIG[timeframe]
        
        data_file = asegurar_datos_historicos(
            simbolo="EURUSD",
            timeframe=tf_config['mt5_code'],
            num_velas=tf_config['velas_needed'],
            min_velas=tf_config['velas_needed'] // 2,
            max_age_days=7
        )
        
        return data_file
    
    def _rank_timeframes(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rankea timeframes por rendimiento."""
        ranking = []
        
        for timeframe, data in results.items():
            result = data["result"]
            # Usar roi_mensual_pct como fuente principal
            roi_mensual = result.get("roi_mensual_pct", result.get("roi_mensual", 0))
            ranking.append({
                "timeframe": timeframe,
                "timeframe_name": TIMEFRAMES_CONFIG[timeframe]["name"],
                "roi_mensual": roi_mensual,
                "profit_neto": result.get("profit_neto", 0),
                "sharpe_ratio": result.get("sharpe_ratio", 0),
                "max_drawdown": result.get("max_drawdown", 0),
                "num_trades": result.get("num_trades", 0),
                "win_rate": result.get("win_rate", 0),
                "execution_time": data["execution_time"]
            })
        
        # Ordenar por ROI mensual descendente
        ranking.sort(key=lambda x: x["roi_mensual"], reverse=True)
        
        return ranking
    
    def print_summary(self, results: Dict[str, Any]):
        """Imprime resumen de resultados."""
        mode = results["mode"]
        
        print(f"\n=== RESUMEN OPTIMIZACIÓN {mode.upper()} ===")
        print(f"Estrategia: {self.strategy_name}")
        print(f"Tiempo total: {results['execution_time']:.1f}s")
        print(f"Evaluaciones totales: {results['total_evaluations']:,}")
        
        if mode == "single":
            best = results["best_result"]
            print(f"Mejor resultado: ROI {best.get('roi_mensual', 0):.2f}%")
        else:
            ranking = results.get("timeframe_ranking", results.get("final_ranking", []))
            
            print("\nRanking de Timeframes:")
            for i, tf in enumerate(ranking[:3], 1):
                print(f"{i}. {tf['timeframe']} ({tf['timeframe_name']}): ROI {tf['roi_mensual']:.2f}%")
        
        print("=" * 50)