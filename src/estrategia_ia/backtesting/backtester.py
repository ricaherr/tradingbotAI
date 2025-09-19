# backtester.py
import pandas as pd
import MetaTrader5 as mt5
import sys
import time
import os

# Importar lógica del agente
from estrategia_ia import config
from estrategia_ia.core.indicadores import calcular_indicadores
from estrategia_ia.core.strategies import determinar_senales
from estrategia_ia.core.order_calculations import calcular_riesgo_dinamico, calcular_lote
from estrategia_ia.trading.broker_simulator import BrokerSimulator # Asegúrate de que broker_simulator.py esté creado

def run_backtest(file_path, estrategia_config, show_plot=True, verbose=False, backtest_period_years=None):
    """
    Ejecuta el backtesting para una estrategia y un conjunto de datos.
    Modificado para ser llamado desde el optimizador.
    """
    # 1. Cargar y preparar datos
    try:
        # Cargar usando 'time' como índice
        df_historico = pd.read_csv(file_path, index_col='time', parse_dates=['time'])
        
        # Filtrar por período si se especifica
        if backtest_period_years is not None and backtest_period_years > 0:
            if not df_historico.empty:
                end_date = df_historico.index.max()
                start_date = end_date - pd.DateOffset(years=backtest_period_years)
                df_historico = df_historico[df_historico.index >= start_date]
                if verbose:
                    print(f"Backtest limitado a los últimos {backtest_period_years} año(s) de datos.")

    except FileNotFoundError:
        if verbose:
            print(f"Error: No se encontró el archivo de datos en '{file_path}'")
        return None
    except ValueError:
        if verbose:
            print(f"Error: La columna 'timestamp' no se encontró en '{file_path}'. Verifique el CSV.")
        return None

    # 2. Inicializar el simulador y las variables
    simulador = BrokerSimulator(df_data=df_historico, capital_inicial=config.CAPITAL_INICIAL_BACKTESTING)
    nombre_estrategia = estrategia_config["nombre"]

    if verbose and not df_historico.empty:
        print(f"BACKTEST: Datos cargados desde {df_historico.index.min().strftime('%Y-%m-%d %H:%M')} hasta {df_historico.index.max().strftime('%Y-%m-%d %H:%M')}. Total de {len(df_historico)} velas.")

    # 3. Bucle principal de simulación (vela por vela)
    if verbose:
        print(f"--- Iniciando Backtest para '{nombre_estrategia}' con params {estrategia_config.get('parametros')} ---")
    
    candle_count = 0
    total_candles = len(df_historico)
    
    while True:
        vela_actual = simulador.tick()
        if vela_actual is None:
            break # Fin de los datos

        candle_count += 1
        if verbose and candle_count % 1000 == 0:
            print(f"BACKTEST: Procesadas {candle_count}/{total_candles} velas ({candle_count/total_candles:.1%}). Balance: {simulador.balance:.2f}")

        # Determinar el número de velas necesarias para los indicadores
        # CORRECTO: Extraer los valores de los parámetros EMA desde la config principal
        optimizable_params = estrategia_config.get("optimizable_params", {})
        ema_keys = [k for k in optimizable_params.keys() if 'ema' in k]
        ema_periods = [estrategia_config.get(k) for k in ema_keys if estrategia_config.get(k) is not None]
        
        num_velas_requeridas = max(ema_periods) if ema_periods else 20 # Mínimo de 20 velas

        df_ventana = simulador.get_current_data(num_velas_requeridas + 5) # +5 de margen
        if len(df_ventana) < num_velas_requeridas:
            continue # No hay suficientes datos al principio

        # Extraer otros parámetros para indicadores
        atr_period = estrategia_config.get("atr_period", 14)
        multi_vela_elefante = estrategia_config.get("multi_vela_elefante", 2.0)

        # Calcular indicadores dinámicamente
        df_indicadores = calcular_indicadores(
            df_ventana,
            ema_periods=ema_periods,
            atr_period=atr_period,
            multi_vela_elefante=multi_vela_elefante
        )

        # Determinar señal
        senal, razon = determinar_senales(df_indicadores, estrategia_config)

        if senal and not simulador.posiciones_abiertas:
            if verbose:
                print(f"BACKTEST: [SENAL] Señal de {senal.upper()} en {vela_actual.name} | Razón: {razon}")
            
            stop_loss, take_profit = calcular_riesgo_dinamico(df_indicadores, senal)
            
            symbol_info_mock = {
                'point': 0.00001, 'trade_tick_value': 1.0, 'volume_step': 0.01,
                'volume_min': 0.01, 'volume_max': 100.0,
            }
            from types import SimpleNamespace
            info_simulada = SimpleNamespace(**symbol_info_mock)
            
            tipo_orden_sim = 0 if senal == "compra" else 1
            precio_entrada = vela_actual['close']
            
            lote_calculado = calcular_lote(
                simulador.balance, config.RIESGO_PORCENTAJE, stop_loss, precio_entrada, info_simulada
            )

            simulador.ejecutar_orden(
                simbolo="EURUSD_BACKTEST", tipo_orden=tipo_orden_sim, lote=lote_calculado,
                sl=stop_loss, tp=take_profit, precio_actual=precio_entrada,
                nombre_estrategia=nombre_estrategia
            )
            if verbose:
                print(f"BACKTEST: Orden {senal.upper()} ejecutada en {vela_actual.name}. Lote: {lote_calculado:.2f}, SL: {stop_loss:.5f}, TP: {take_profit:.5f}")

    # 4. Obtener y devolver el reporte final
    reporte = simulador.get_reporte(show_plot=show_plot, verbose=verbose)

    # 5. Añadir información del período al reporte
    if reporte is not None:
        try:
            start_date = df_historico.index[0]
            end_date = df_historico.index[-1]
            reporte['periodo_inicio'] = start_date.strftime('%Y-%m-%d')
            reporte['periodo_fin'] = end_date.strftime('%Y-%m-%d')
            reporte['periodo_dias'] = (end_date - start_date).days
        except (IndexError, AttributeError) as e:
            if verbose:
                print(f"Advertencia: No se pudo añadir información del período al reporte: {e}")

    return reporte



