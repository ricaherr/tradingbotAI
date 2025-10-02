"""
Módulo separado para la función de cálculo de fitness en multiprocessing.
Esto evita problemas de serialización en Windows.
"""

def run_fitness_calculation(args):
    """
    Función aislada para ser usada por multiprocessing.Pool.
    Ejecuta un backtest y calcula el fitness para un único individuo.
    """
    try:
        individual_params, strategy_config_base, data_file_path, backtest_period_years, test_mode = args
        
        # Convertir días a años si se especificó en días
        if 'backtest_days' in strategy_config_base:
            backtest_period_years = strategy_config_base['backtest_days'] / 365.25

        # Re-importar dependencias es una buena práctica para evitar problemas de pickling
        from estrategia_ia.backtesting.backtester import run_backtest
        from estrategia_ia.optimization.evaluator import Evaluator
        from estrategia_ia.core.data_manager import asegurar_datos_historicos
        from estrategia_ia.config import TIMEFRAMES_CONFIG
        import copy
        import sys
        import MetaTrader5 as mt5

        # Lógica de _run_backtest
        strategy_config = copy.deepcopy(strategy_config_base)
        strategy_config.update(individual_params)
        
        # Usar el archivo de datos que ya se pasó (ya contiene el timeframe correcto)
        current_data_file = data_file_path
        
        # Para modo fixed_timeframe, usar siempre el archivo que se pasó
        # Solo cambiar archivo si hay timeframe dinámico en individual_params
        if 'timeframe' in individual_params and 'fixed_timeframe' not in strategy_config_base:
            timeframe_idx = int(individual_params['timeframe'])
            timeframe_keys = list(TIMEFRAMES_CONFIG.keys())
            
            if 0 <= timeframe_idx < len(timeframe_keys):
                timeframe_key = timeframe_keys[timeframe_idx]
                timeframe_config = TIMEFRAMES_CONFIG[timeframe_key]
                
                # Solo obtener datos diferentes si es necesario
                current_data_file = asegurar_datos_historicos(
                    simbolo="EURUSD",
                    timeframe=timeframe_config['mt5_code'],
                    num_velas=timeframe_config['velas_needed'],
                    min_velas=timeframe_config['velas_needed'] // 2,
                    max_age_days=7
                )
                
                if not current_data_file:
                    return -float('inf')

        report = run_backtest(
            current_data_file,
            strategy_config,
            show_plot=False,
            verbose=False,
            backtest_period_years=backtest_period_years
        )

        # Lógica de _calculate_fitness
        if not report or report.get('operaciones_totales', 0) < 1:
            return -float('inf')

        evaluator = Evaluator(report)
        evaluation = evaluator.evaluate()
        # Usar Sharpe Ratio como fitness. Podría ser otra métrica.
        return evaluation.get('sharpe_ratio', -float('inf'))
    except KeyboardInterrupt:
        # This is to prevent the worker from printing a traceback.
        # The main process will handle the cleanup.
        sys.exit(1)
    except Exception as e:
        # En caso de error, devolver fitness muy bajo
        return -float('inf')