# mt5_broker.py
import MetaTrader5 as mt5
from estrategia_ia.utils.notificaciones import enviar_notificacion
from estrategia_ia.utils.registro_operaciones import registrar_operacion_abierta
from estrategia_ia import config
from estrategia_ia.utils.logger import broker_logger
from estrategia_ia.utils.error_handler import retry_on_failure, validate_mt5_response

class MT5Broker:
    """
    Implementación del broker para operar en vivo con MetaTrader 5.
    """
    def __init__(self, capital_inicial, riesgo_porcentaje, verbose=False):
        self.capital_inicial = capital_inicial
        self.riesgo_porcentaje = riesgo_porcentaje
        self.verbose = verbose
        self.vela_actual = None

    def update_vela_actual(self, vela):
        self.vela_actual = vela

    @retry_on_failure(max_retries=3, delay=0.5, exceptions=(ConnectionError, RuntimeError))
    def get_current_price(self, simbolo, tipo_operacion):
        tick = mt5.symbol_info_tick(simbolo)
        if tick is None:
            raise ConnectionError(f"No se pudo obtener tick para {simbolo}")
        return tick.ask if tipo_operacion == 'compra' else tick.bid

    def has_open_positions(self):
        return mt5.positions_total() > 0

    def get_open_positions(self):
        positions = mt5.positions_get()
        if not positions:
            return []
        
        # Adaptar el formato al esperado por el motor
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                'ticket': pos.ticket,
                'simbolo': pos.symbol,
                'tipo': 'compra' if pos.type == mt5.ORDER_TYPE_BUY else 'venta',
                'precio_apertura': pos.price_open,
                'sl': pos.sl,
                'tp': pos.tp
            })
        return formatted_positions

    def execute_order(self, simbolo, tipo_orden_str, sl, tp, nombre_estrategia, atr_apertura):
        if mt5.positions_total() >= config.MAX_OPERACIONES_SIMULTANEAS:
            if self.verbose:
                logging.warning(f"Máximo de operaciones simultáneas alcanzado. No se abre nueva orden en {simbolo}.")
            return

        symbol_info = mt5.symbol_info(simbolo)
        if symbol_info is None:
            logging.error(f"No se pudo obtener información del símbolo {simbolo}.")
            return

        tick = mt5.symbol_info_tick(simbolo)
        if tick is None:
            logging.error(f"No se pudo obtener el tick para {simbolo}.")
            return

        tipo_orden = mt5.ORDER_TYPE_BUY if tipo_orden_str == 'compra' else mt5.ORDER_TYPE_SELL
        precio_actual = tick.ask if tipo_orden == mt5.ORDER_TYPE_BUY else tick.bid

        # Cálculo de lote
        lote = self._calculate_lot_size(simbolo, sl, precio_actual)
        if lote is None or lote < symbol_info.volume_min:
            logging.warning(f"Lote calculado ({lote}) es inválido o menor al mínimo. No se ejecuta la orden.")
            return

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": simbolo,
            "volume": lote,
            "type": tipo_orden,
            "price": precio_actual,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "comment": f"Estrategia: {nombre_estrategia}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        try:
            resultado = mt5.order_send(request)
            validate_mt5_response(resultado, "envío de orden")
        except (ConnectionError, RuntimeError) as e:
            broker_logger.error(f"Error al enviar orden: {e}")
            return

        if resultado.retcode == mt5.TRADE_RETCODE_DONE:
            if self.verbose:
                logging.info(f"Orden ejecutada: {simbolo} {tipo_orden_str} | Lote: {lote:.2f} | SL: {sl} | TP: {tp}")
            
            registrar_operacion_abierta(
                ticket=resultado.order,
                simbolo=simbolo,
                estrategia=nombre_estrategia,
                lote=lote,
                tipo=tipo_orden_str,
                precio_apertura=precio_actual,
                sl=sl,
                tp=tp
            )
            mensaje = f"[OK] NUEVA OPERACIÓN\nPar: {simbolo}\nTipo: {tipo_orden_str.upper()}\nLote: {lote:.2f}\nEstrategia: {nombre_estrategia}"
            enviar_notificacion(mensaje)
        else:
            logging.error(f"Fallo al ejecutar la orden: {resultado.retcode} | {resultado.comment}")
            mensaje_error = f"[FALLO] ERROR en OPERACIÓN\nPar: {simbolo}\nError: {resultado.retcode} - {resultado.comment}"
            enviar_notificacion(mensaje_error)

    def modify_position(self, ticket, new_sl=None, new_tp=None):
        position = mt5.positions_get(ticket=ticket)
        if not position:
            logging.warning(f"No se encontró la posición con ticket {ticket} para modificar.")
            return

        position = position[0]
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "sl": new_sl if new_sl is not None else position.sl,
            "tp": new_tp if new_tp is not None else position.tp,
            "position": ticket,
        }

        try:
            resultado = mt5.order_send(request)
            validate_mt5_response(resultado, "modificación de posición")
        except (ConnectionError, RuntimeError) as e:
            broker_logger.error(f"Error al modificar posición: {e}")
            return
            
        if resultado.retcode == mt5.TRADE_RETCODE_DONE:
            if self.verbose:
                logging.info(f"Stop loss actualizado para el ticket {ticket} a {new_sl}")
        else:
            logging.error(f"Fallo al actualizar SL para el ticket {ticket}. Código: {resultado.retcode}")

    def get_reporte(self, show_plot=False, verbose=False):
        # En modo live, el reporte se genera a partir de los archivos de registro
        if verbose:
            print("Modo live: El reporte se consulta en los archivos de registro.")
        return {}

    def _calculate_lot_size(self, simbolo, sl, precio_actual):
        account_info = mt5.account_info()
        if account_info is None:
            return None

        capital = account_info.balance
        riesgo_dinero = capital * (self.riesgo_porcentaje / 100)

        symbol_info = mt5.symbol_info(simbolo)
        if symbol_info is None:
            return None

        distancia_stop_pips = abs(precio_actual - sl) / symbol_info.point
        if distancia_stop_pips == 0:
            return None

        valor_pip = symbol_info.trade_tick_value_profit
        if valor_pip <= 0:
            return None

        lote = (riesgo_dinero / (distancia_stop_pips * valor_pip))
        
        lote = max(symbol_info.volume_min, min(lote, symbol_info.volume_max))
        lote = round(lote, 2)

        return lote