# broker_simulator.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace
from estrategia_ia.core.order_calculations import calcular_lote

class BrokerSimulator:
    """
    Simula un broker de trading para el backtesting, compatible con el TradingEngine.
    """
    def __init__(self, capital_inicial, riesgo_porcentaje, comision_por_lote=0.0, spread=0.0001, verbose=False):
        self.capital_inicial = capital_inicial
        self.balance = capital_inicial
        self.riesgo_porcentaje = riesgo_porcentaje
        self.comision_por_lote = comision_por_lote
        self.spread = spread
        self.verbose = verbose
        
        self.posiciones_abiertas = []
        self.historial_operaciones = []
        self.equity_curve = [capital_inicial]
        self.TICK_COUNTER = 0
        self.vela_actual = None

    def update_vela_actual(self, vela):
        """Actualiza la vela actual para cálculos de precios y SL/TP."""
        self.vela_actual = vela
        if self.vela_actual is not None:
            # Solo registrar equity si el balance cambió o cada N velas para reducir memoria
            if not self.equity_curve or self.balance != self.equity_curve[-1]:
                self.equity_curve.append(self.balance)
            self.check_positions() # Verificar SL/TP en cada nueva vela

    def has_open_positions(self):
        """Verifica si hay posiciones abiertas."""
        return len(self.posiciones_abiertas) > 0

    def get_open_positions(self):
        """Devuelve una copia de las posiciones abiertas."""
        return [p.copy() for p in self.posiciones_abiertas]

    def get_current_price(self, simbolo, tipo_orden):
        """Devuelve el precio de ejecución simulado (ask o bid) según el tipo de orden."""
        if self.vela_actual is None: return 0
        
        # El precio 'close' de la vela se considera el precio BID
        bid_price = self.vela_actual['close']
        
        if tipo_orden == 'compra':
            # Para comprar, se usa el precio ASK (bid + spread)
            return bid_price + self.spread
        else: # 'venta'
            # Para vender, se usa el precio BID
            return bid_price

    def modify_position(self, ticket, new_sl=None, new_tp=None):
        """Modifica el SL o TP de una posición abierta."""
        for pos in self.posiciones_abiertas:
            if pos['ticket'] == ticket:
                if new_sl is not None:
                    pos['sl'] = new_sl
                if new_tp is not None:
                    pos['tp'] = new_tp
                # print(f"SIM: Posición {ticket} modificada. Nuevo SL: {new_sl}, Nuevo TP: {new_tp}")
                return True
        return False

    def check_positions(self):
        """Verifica si alguna posición abierta ha tocado su SL o TP con la vela actual."""
        if self.vela_actual is None: return

        posiciones_a_cerrar = []
        for pos in self.posiciones_abiertas:
            precio_cierre, razon_cierre = None, ""
            if pos['tipo'] == 'compra':
                if self.vela_actual['low'] <= pos['sl']:
                    precio_cierre, razon_cierre = pos['sl'], "Stop Loss"
                elif self.vela_actual['high'] >= pos['tp']:
                    precio_cierre, razon_cierre = pos['tp'], "Take Profit"
            elif pos['tipo'] == 'venta':
                if self.vela_actual['high'] >= pos['sl']:
                    precio_cierre, razon_cierre = pos['sl'], "Stop Loss"
                elif self.vela_actual['low'] <= pos['tp']:
                    precio_cierre, razon_cierre = pos['tp'], "Take Profit"

            if precio_cierre:
                self.cerrar_posicion(pos, precio_cierre, razon_cierre, self.vela_actual.name)
                posiciones_a_cerrar.append(pos)

        self.posiciones_abiertas = [p for p in self.posiciones_abiertas if p not in posiciones_a_cerrar]

    def execute_order(self, simbolo, tipo_orden_str, sl, tp, nombre_estrategia, atr_apertura):
        """Simula la ejecución de una orden, calculando el lote internamente."""
        precio_entrada = self.get_current_price(simbolo, tipo_orden_str)
        
        # Simular la información del símbolo que MT5 proporcionaría
        info_simulada = SimpleNamespace(point=0.00001, trade_tick_value=1.0, volume_step=0.01, volume_min=0.01, volume_max=100.0)
        
        lote_calculado = calcular_lote(
            self.balance, self.riesgo_porcentaje, sl, precio_entrada, info_simulada
        )
        if lote_calculado < info_simulada.volume_min:
            # print(f"SIM: Lote calculado ({lote_calculado}) es menor al mínimo. Orden no ejecutada.")
            return False

        self.TICK_COUNTER += 1
        posicion = {
            'ticket': self.TICK_COUNTER,
            'simbolo': simbolo,
            'tipo': tipo_orden_str,
            'lote': lote_calculado,
            'precio_apertura': precio_entrada,
            'sl': sl,
            'tp': tp,
            'fecha_apertura': self.vela_actual.name,
            'estrategia': nombre_estrategia,
            'atr_apertura': atr_apertura
        }
        self.posiciones_abiertas.append(posicion)
        
        return True

    def cerrar_posicion(self, posicion, precio_cierre, razon, fecha_cierre):
        """Simula el cierre de una posición y calcula el resultado."""
        pips = (precio_cierre - posicion['precio_apertura']) if posicion['tipo'] == 'compra' else (posicion['precio_apertura'] - precio_cierre)
        
        # Simplificación del valor del pip para backtesting (ej. para EURUSD)
        valor_pip_por_lote = 10
        resultado_dinero = pips * 10000 * posicion['lote'] * valor_pip_por_lote
        resultado_dinero -= self.comision_por_lote * posicion['lote']
        
        self.balance += resultado_dinero
        
        operacion_cerrada = posicion.copy()
        operacion_cerrada.update({
            'precio_cierre': precio_cierre,
            'fecha_cierre': fecha_cierre,
            'resultado_dinero': resultado_dinero,
            'razon_cierre': razon
        })
        self.historial_operaciones.append(operacion_cerrada)
        

    def get_reporte(self, show_plot=True, verbose=True):
        """Genera un reporte de resultados del backtesting."""
        total_ops = len(self.historial_operaciones)
        ops_ganadoras = sum(1 for op in self.historial_operaciones if op['resultado_dinero'] > 0)
        ops_perdedoras = total_ops - ops_ganadoras

        ganancia_bruta = sum(op['resultado_dinero'] for op in self.historial_operaciones if op['resultado_dinero'] > 0)
        perdida_bruta = abs(sum(op['resultado_dinero'] for op in self.historial_operaciones if op['resultado_dinero'] < 0))

        profit_factor = ganancia_bruta / perdida_bruta if perdida_bruta > 0 else np.inf
        profit_total = self.balance - self.capital_inicial
        tasa_acierto = (ops_ganadoras / total_ops * 100) if total_ops > 0 else 0

        equity_series = pd.Series(self.equity_curve)
        peak_series = equity_series.cummax()
        drawdown_series = (equity_series - peak_series) / peak_series
        max_drawdown = abs(drawdown_series.min()) if not drawdown_series.empty else 0

        # Cálculo de Sharpe, Sortino, Calmar
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0 # Asumiendo datos diarios
        sortino_ratio = returns.mean() / returns[returns < 0].std() * np.sqrt(252) if len(returns[returns < 0]) > 1 else 0
        calmar_ratio = (profit_total / self.capital_inicial) / max_drawdown if max_drawdown > 0 else 0
        
        # Win/Loss Ratio
        avg_win = ganancia_bruta / ops_ganadoras if ops_ganadoras > 0 else 0
        avg_loss = perdida_bruta / ops_perdedoras if ops_perdedoras > 0 else 0
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf

        reporte = {
            "capital_inicial": self.capital_inicial, "capital_final": self.balance,
            "profit_neto": profit_total, "operaciones_totales": total_ops,
            "operaciones_ganadoras": ops_ganadoras, "operaciones_perdedoras": ops_perdedoras,
            "tasa_acierto": tasa_acierto, "ganancia_bruta": ganancia_bruta,
            "perdida_bruta": perdida_bruta, "profit_factor": profit_factor,
            "max_drawdown": max_drawdown, "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio, "calmar_ratio": calmar_ratio,
            "win_loss_ratio": win_loss_ratio,
            "historial_operaciones": self.historial_operaciones, "equity_curve": self.equity_curve
        }

        if verbose:
            print("\n--- REPORTE DE BACKTESTING ---")
            print(f"Capital Final: ${self.balance:,.2f} | Profit Neto: ${profit_total:,.2f}")
            print(f"Operaciones: {total_ops} | Tasa Acierto: {tasa_acierto:.2f}%")
            print(f"Profit Factor: {profit_factor:.2f} | W/L Ratio: {win_loss_ratio:.2f}")
            print(f"Max Drawdown: {max_drawdown:.2%}")
            print(f"Sharpe: {sharpe_ratio:.2f} | Sortino: {sortino_ratio:.2f} | Calmar: {calmar_ratio:.2f}")
            print("---------------------------------")

        if show_plot: self.plot_equity_curve()
        return reporte

    def plot_equity_curve(self):
        """Genera y muestra un gráfico de la curva de capital."""
        plt.figure(figsize=(12, 6))
        plt.plot(self.equity_curve, label='Equity Curve', color='blue')
        plt.title('Curva de Capital del Backtest')
        plt.xlabel('Número de Velas')
        plt.ylabel('Capital')
        plt.legend()
        plt.grid(True)
        plt.show()
