# broker_simulator.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class BrokerSimulator:
    """
    Simula un broker de trading para el backtesting.
    Reemplaza las llamadas a MetaTrader 5.
    """
    def __init__(self, df_data, capital_inicial, comision_por_lote=0.0):
        self.df_data = df_data
        self.capital_inicial = capital_inicial
        self.balance = capital_inicial
        self.comision_por_lote = comision_por_lote
        
        self.posiciones_abiertas = []
        self.historial_operaciones = []
        self.current_index = 0
        
        # Para cálculo de Drawdown
        self.equity_curve = [capital_inicial]
        self.peak_equity = capital_inicial
        self.TICK_COUNTER = 0

    def tick(self):
        """Avanza un 'tick' en los datos históricos (una vela)."""
        if self.current_index < len(self.df_data) - 1:
            self.current_index += 1
            # Comprobar si las posiciones abiertas deben cerrarse (SL/TP)
            self.equity_curve.append(self.balance) # Registrar equity antes de cerrar
            self._check_sl_tp()
            return self.df_data.iloc[self.current_index]
        return None

    def get_current_data(self, num_velas):
        """Devuelve un DataFrame con las últimas 'num_velas'."""
        start_index = max(0, self.current_index - num_velas + 1)
        return self.df_data.iloc[start_index : self.current_index + 1]

    def _check_sl_tp(self):
        """Verifica si alguna posición abierta ha tocado su SL o TP."""
        vela_actual = self.df_data.iloc[self.current_index]
        posiciones_a_cerrar = []

        for pos in self.posiciones_abiertas:
            precio_cierre = None
            razon_cierre = ""
            
            if pos['tipo'] == 'compra':
                # Comprobar SL
                if vela_actual['low'] <= pos['sl']:
                    precio_cierre = pos['sl']
                    razon_cierre = "Stop Loss"
                # Comprobar TP
                elif vela_actual['high'] >= pos['tp']:
                    precio_cierre = pos['tp']
                    razon_cierre = "Take Profit"
            
            elif pos['tipo'] == 'venta':
                # Comprobar SL
                if vela_actual['high'] >= pos['sl']:
                    precio_cierre = pos['sl']
                    razon_cierre = "Stop Loss"
                # Comprobar TP
                elif vela_actual['low'] <= pos['tp']:
                    precio_cierre = pos['tp']
                    razon_cierre = "Take Profit"

            if precio_cierre:
                self.cerrar_posicion(pos, precio_cierre, razon_cierre)
                posiciones_a_cerrar.append(pos)

        # Eliminar posiciones cerradas de la lista de abiertas
        self.posiciones_abiertas = [p for p in self.posiciones_abiertas if p not in posiciones_a_cerrar]

    def ejecutar_orden(self, simbolo, tipo_orden, lote, sl, tp, precio_actual, nombre_estrategia):
        """Simula la ejecución de una orden."""
        self.TICK_COUNTER += 1
        posicion = {
            'ticket': self.TICK_COUNTER,
            'simbolo': simbolo,
            'tipo': 'compra' if tipo_orden == 0 else 'venta', # MT5: 0=BUY, 1=SELL
            'lote': lote,
            'precio_apertura': precio_actual,
            'sl': sl,
            'tp': tp,
            'fecha_apertura': self.df_data.index[self.current_index],
            'estrategia': nombre_estrategia
        }
        self.posiciones_abiertas.append(posicion)
        # print(f"BACKTEST: [ORDEN] Orden {posicion['tipo']} abierta en {precio_actual} | Lote: {lote}")
        return True

    def cerrar_posicion(self, posicion, precio_cierre, razon):
        """Simula el cierre de una posición y calcula el resultado."""
        pips = (precio_cierre - posicion['precio_apertura']) if posicion['tipo'] == 'compra' else (posicion['precio_apertura'] - precio_cierre)
        
        # Simplificación del valor del pip para backtesting (ej. para EURUSD)
        valor_pip_por_lote = 10
        resultado_dinero = pips * 10000 * posicion['lote'] * valor_pip_por_lote
        
        # Aplicar comisión
        resultado_dinero -= self.comision_por_lote * posicion['lote']
        
        self.balance += resultado_dinero
        
        operacion_cerrada = posicion.copy()
        operacion_cerrada.update({
            'precio_cierre': precio_cierre,
            'fecha_cierre': self.df_data.index[self.current_index],
            'resultado_dinero': resultado_dinero,
            'razon_cierre': razon
        })
        self.historial_operaciones.append(operacion_cerrada)
        # print(f"BACKTEST: [CERRADA] Posición cerrada en {precio_cierre} | Resultado: ${resultado_dinero:.2f} | Razón: {razon}")

    def get_reporte(self, show_plot=True, verbose=True):
        """Genera un reporte de resultados y opcionalmente lo muestra."""
        total_ops = len(self.historial_operaciones)
        ops_ganadoras = sum(1 for op in self.historial_operaciones if op['resultado_dinero'] > 0)
        ops_perdedoras = total_ops - ops_ganadoras

        ganancia_bruta = sum(op['resultado_dinero'] for op in self.historial_operaciones if op['resultado_dinero'] > 0)
        perdida_bruta = abs(sum(op['resultado_dinero'] for op in self.historial_operaciones if op['resultado_dinero'] < 0))

        profit_factor = ganancia_bruta / perdida_bruta if perdida_bruta > 0 else np.inf
        profit_total = self.balance - self.capital_inicial
        
        tasa_acierto = (ops_ganadoras / total_ops * 100) if total_ops > 0 else 0

        # Cálculo del Drawdown Máximo
        equity_series = pd.Series(self.equity_curve)
        peak_series = equity_series.cummax()
        drawdown_series = (equity_series - peak_series) / peak_series
        max_drawdown = abs(drawdown_series.min())

        reporte = {
            "capital_inicial": self.capital_inicial,
            "capital_final": self.balance,
            "profit_neto": profit_total,
            "operaciones_totales": total_ops,
            "operaciones_ganadoras": ops_ganadoras,
            "operaciones_perdedoras": ops_perdedoras,
            "tasa_acierto": tasa_acierto,
            "ganancia_bruta": ganancia_bruta,
            "perdida_bruta": perdida_bruta,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "historial_operaciones": self.historial_operaciones,
            "equity_curve": self.equity_curve
        }

        if verbose:
            print("\n--- REPORTE DE BACKTESTING ---")
            print(f"Capital Inicial:       $\"{self.capital_inicial:10.2f}")
            print(f"Capital Final:         $\"{self.balance:10.2f}")
            print(f"Profit Neto:           $\"{profit_total:10.2f}")
            print("-" * 30)
            print(f"Operaciones Totales:   {total_ops}")
            print(f"Operaciones Ganadoras: {ops_ganadoras}")
            print(f"Operaciones Perdedoras:{ops_perdedoras}")
            print(f"Tasa de Acierto:       {tasa_acierto:.2f}%")
            print("-" * 30)
            print(f"Ganancia Bruta:        $\"{ganancia_bruta:10.2f}")
            print(f"Pérdida Bruta:         $\"{perdida_bruta:10.2f}")
            print(f"Profit Factor:         {profit_factor:.2f}")
            print(f"Drawdown Máximo:       {max_drawdown:.2%}")
            print("---------------------------------")

        if show_plot:
            self.plot_equity_curve()
            
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