# backtester.py
from estrategia_ia import config
from estrategia_ia.core.engine import TradingEngine
from estrategia_ia.core.data_source import HistoricalDataSource
from estrategia_ia.trading.broker_simulator import BrokerSimulator
from estrategia_ia.utils.risk_calculator import RiskCalculator

def run_backtest(file_path, estrategia_config, show_plot=True, verbose=False, backtest_period_years=None):
    """
    Ejecuta el backtesting utilizando el TradingEngine unificado.
    Configura los componentes (DataSource, Broker) y ejecuta el motor.
    """
    # 0. Validar configuración de estrategia
    errores_estrategia = config.validar_estrategia(estrategia_config)
    if errores_estrategia:
        if verbose:
            print(f"Errores en estrategia: {errores_estrategia}")
        return None
    
    # 1. Configurar la fuente de datos históricos
    data_source = HistoricalDataSource(
        file_path=file_path,
        backtest_period_years=backtest_period_years,
        verbose=verbose
    )
    
    # Validar datos cargados
    if hasattr(data_source, 'df_data'):
        errores_datos = config.validar_datos_mercado(data_source.df_data)
        if errores_datos:
            if verbose:
                print(f"Errores en datos: {errores_datos}")
            return None

    # 2. Configurar el calculador de riesgo
    risk_calculator = RiskCalculator(capital_inicial=config.CAPITAL_INICIAL_BACKTESTING)
    
    # 3. Configurar el broker simulado con RiskCalculator y timeframe
    # Determinar timeframe desde estrategia_config
    timeframe_map = {0: "M1", 1: "M5", 2: "M15", 3: "M30", 4: "H1", 5: "H4"}
    timeframe_index = estrategia_config.get('timeframe', estrategia_config.get('fixed_timeframe', 2))
    timeframe = timeframe_map.get(timeframe_index, "M15")
    
    broker = BrokerSimulator(
        capital_inicial=config.CAPITAL_INICIAL_BACKTESTING,
        riesgo_porcentaje=config.RIESGO_PORCENTAJE,
        spread=0.0001, # Valor de spread añadido, futuramente configurable
        verbose=verbose,
        risk_calculator=risk_calculator,  # Integrar RiskCalculator
        timeframe=timeframe  # Pasar timeframe para cálculos correctos
    )

    # 4. Configurar el motor de trading con RiskCalculator
    risk_manager_config = {
        "TRAILING_ACTIVO": config.TRAILING_ACTIVO,
        "BREAK_EVEN_ACTIVO": config.BREAK_EVEN_ACTIVO,
        "BREAK_EVEN_ATR_FACTOR": config.BREAK_EVEN_ATR_FACTOR,
        "TRAILING_ATR_FACTOR": config.TRAILING_ATR_FACTOR,
        "risk_calculator": risk_calculator  # Pasar RiskCalculator al motor
    }

    engine = TradingEngine(
        strategy_config=estrategia_config,
        broker=broker,
        data_source=data_source,
        risk_manager_config=risk_manager_config,
        verbose=verbose
    )

    # 5. Ejecutar el motor y obtener el reporte
    reporte = engine.run(show_plot=show_plot)

    if verbose:
        print("Backtest finalizado. Procesando reporte...")

    # Opcional: añadir información extra al reporte si es necesario
    if reporte and not data_source.df_data.empty:
        try:
            start_date = data_source.df_data.index[0]
            end_date = data_source.df_data.index[-1]
            reporte['periodo_inicio'] = start_date.strftime('%Y-%m-%d')
            reporte['periodo_fin'] = end_date.strftime('%Y-%m-%d')
            reporte['periodo_dias'] = (end_date - start_date).days
        except (IndexError, AttributeError):
            if verbose:
                print("Advertencia: No se pudo añadir información del período al reporte.")

    return reporte



