# engine.py
import pandas as pd
from estrategia_ia.utils.logger import engine_logger

from estrategia_ia.core.indicadores import calcular_indicadores
from estrategia_ia.core.strategies import determinar_senales
from estrategia_ia.core.order_calculations import calcular_riesgo_dinamico, calcular_lote
from estrategia_ia.risk_management.gestor_riesgo_en_operacion import GestorRiesgoEnOperacion

class TradingEngine:
    """
    Motor de trading unificado para backtesting y operaciones en vivo.
    """
    def __init__(self, strategy_config, broker, data_source, risk_manager_config, verbose=False):
        self.strategy_config = strategy_config
        self.broker = broker
        self.data_source = data_source
        self.verbose = verbose
        self.nombre_estrategia = self.strategy_config["nombre"]

        # Inicializar gestor de riesgo en la operación (Trailing Stop, Break Even)
        self.gestor_riesgo_op = GestorRiesgoEnOperacion(
            modo_trailing=risk_manager_config.get("TRAILING_ACTIVO", False),
            break_even_activo=risk_manager_config.get("BREAK_EVEN_ACTIVO", False),
            atr_factor_break_even=risk_manager_config.get("BREAK_EVEN_ATR_FACTOR", 1.5),
            atr_factor_trailing=risk_manager_config.get("TRAILING_ATR_FACTOR", 2.0)
        )
        
        if self.verbose:
            engine_logger.info("TradingEngine inicializado.")

    def run(self, show_plot=False):
        """
        Ejecuta el bucle principal del motor de trading.
        """
        if self.verbose:
            param_keys = self.strategy_config.get("optimizable_params", {}).keys()
            current_params = {key: self.strategy_config.get(key) for key in param_keys}
            print(f"--- Iniciando ejecución para '{self.nombre_estrategia}' con params {current_params} ---")

        while self.data_source.has_next():
            # 1. Obtener la siguiente vela
            vela_actual, df_historico_ventana = self.data_source.get_next_candle_with_history()
            if vela_actual is None:
                break
            
            # 2. Actualizar el estado del broker con la nueva vela (importante para backtesting)
            # En modo live, este método podría no hacer nada o actualizar precios de mercado
            self.broker.update_vela_actual(vela_actual)

            # 3. Gestionar operaciones abiertas (Trailing Stop / Break Even)
            self.manage_open_positions(df_historico_ventana)

            # 4. Buscar nuevas señales si no hay posiciones abiertas
            if not self.broker.has_open_positions():
                self.check_for_new_signals(df_historico_ventana)

        if self.verbose:
            engine_logger.info("Bucle de trading finalizado.")
        
        # Devolver el reporte final del broker (útil para backtesting)
        return self.broker.get_reporte(show_plot=show_plot, verbose=self.verbose)

    def manage_open_positions(self, df_ventana):
        """
        Aplica la lógica de gestión de riesgo a las posiciones abiertas.
        """
        open_positions = self.broker.get_open_positions()
        if not open_positions:
            return

        # Calcular indicadores necesarios para la gestión (ej. ATR)
        df_indicadores = self._calculate_indicators(df_ventana)
        if df_indicadores.empty:
            return
        
        atr_value = df_indicadores.iloc[-1].get('ATR')
        if atr_value is None:
            return # No se puede gestionar sin ATR

        for position in open_positions:
            nuevo_stop = self.gestor_riesgo_op.actualizar_stop(
                precio_entrada=position['precio_apertura'],
                stop_actual=position['sl'],
                precio_actual=self.broker.get_current_price(position['simbolo'], position['tipo']),
                tipo=position['tipo'],
                atr_value=atr_value
            )

            if abs(nuevo_stop - position['sl']) > 0.00001:
                self.broker.modify_position(position['ticket'], new_sl=nuevo_stop)
                

    def check_for_new_signals(self, df_ventana):
        """
        Calcula indicadores y busca nuevas señales de trading.
        """
        df_indicadores = self._calculate_indicators(df_ventana)
        if df_indicadores.empty:
            return

        senal, razon = determinar_senales(df_indicadores, self.strategy_config)

        if senal:
            

            stop_loss, take_profit = calcular_riesgo_dinamico(df_indicadores, senal)
            
            # Aquí, el broker se encargará de calcular el lote y ejecutar la orden
            self.broker.execute_order(
                simbolo=self.strategy_config.get("par", "EURUSD"),
                tipo_orden_str=senal,
                sl=stop_loss,
                tp=take_profit,
                nombre_estrategia=self.nombre_estrategia,
                atr_apertura=df_indicadores.iloc[-1].get('ATR'),
                strategy_config=self.strategy_config
            )

    def _calculate_indicators(self, df_ventana):
        """
        Wrapper para el cálculo de indicadores con caché para evitar recálculos.
        """
        # Verificar si ya tenemos indicadores calculados para esta ventana
        if hasattr(self, '_last_indicators_size') and len(df_ventana) == self._last_indicators_size:
            # Si el tamaño es el mismo, solo necesitamos actualizar la última fila
            if hasattr(self, '_cached_indicators') and not self._cached_indicators.empty:
                return self._cached_indicators
        
        optimizable_params = self.strategy_config.get("optimizable_params", {})
        ema_keys = [k for k in optimizable_params.keys() if 'ema' in k]
        ema_periods = [self.strategy_config.get(k) for k in ema_keys if self.strategy_config.get(k) is not None]
        
        if ema_periods:
            num_velas_requeridas = max(ema_periods)
        else:
            num_velas_requeridas = 20
        if len(df_ventana) < num_velas_requeridas:
            return pd.DataFrame()

        # Calcular indicadores
        indicators = calcular_indicadores(
            df_ventana,
            ema_periods=ema_periods,
            atr_period=self.strategy_config.get("atr_period", 14),
            multi_vela_elefante=self.strategy_config.get("multi_vela_elefante", 2.0)
        )
        
        # Cachear para próxima iteración
        self._cached_indicators = indicators
        self._last_indicators_size = len(df_ventana)
        
        return indicators
