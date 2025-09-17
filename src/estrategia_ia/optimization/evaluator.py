import numpy as np
import pandas as pd

class Evaluator:
    def __init__(self, backtest_report):
        self.report = backtest_report
        self.returns = pd.Series(self.report['equity_curve']).pct_change().dropna()

    def evaluate(self):
        """
        Analiza los resultados de un backtest y devuelve un reporte de evaluación.
        """
        evaluation_report = {}
        evaluation_report.update(self.report)
        evaluation_report.update(self._calculate_sharpe_ratio())
        evaluation_report.update(self._calculate_sortino_ratio())
        evaluation_report.update(self._calculate_calmar_ratio())
        evaluation_report.update(self._calculate_win_loss_ratio())
        evaluation_report.update(self._identify_patterns())
        
        return evaluation_report

    def _calculate_sharpe_ratio(self, risk_free_rate=0, periods_per_year=252*60*24): # Assuming M1 data, 252 trading days
        """
        Calcula el Sharpe Ratio a partir de la curva de equity.
        """
        if len(self.returns) < 2:
            return {"sharpe_ratio": 0}

        mean_return = self.returns.mean()
        std_dev_return = self.returns.std()

        if std_dev_return == 0:
            return {"sharpe_ratio": np.inf if mean_return > 0 else 0}

        sharpe_ratio = (mean_return - risk_free_rate) / std_dev_return
        annualized_sharpe_ratio = sharpe_ratio * np.sqrt(periods_per_year)

        return {"sharpe_ratio": annualized_sharpe_ratio}

    def _calculate_sortino_ratio(self, risk_free_rate=0, periods_per_year=252*60*24):
        """
        Calcula el Sortino Ratio, que solo penaliza la volatilidad a la baja.
        """
        if len(self.returns) < 2:
            return {"sortino_ratio": 0}

        mean_return = self.returns.mean()
        
        # Calcular la desviación estándar solo de los retornos negativos
        negative_returns = self.returns[self.returns < 0]
        downside_std = negative_returns.std()

        if downside_std == 0:
            return {"sortino_ratio": np.inf if mean_return > 0 else 0}

        sortino_ratio = (mean_return - risk_free_rate) / downside_std
        annualized_sortino_ratio = sortino_ratio * np.sqrt(periods_per_year)

        return {"sortino_ratio": annualized_sortino_ratio}

    def _calculate_calmar_ratio(self, periods_per_year=252*60*24):
        """
        Calcula el Calmar Ratio (Retorno Anualizado / Máximo Drawdown).
        """
        if len(self.returns) < 2 or self.report['max_drawdown'] == 0:
            return {"calmar_ratio": 0}

        # Calcular el retorno anualizado
        total_return = (self.report['capital_final'] / self.report['capital_inicial']) - 1
        num_periods = len(self.report['equity_curve'])
        annualized_return = (1 + total_return) ** (periods_per_year / num_periods) - 1

        calmar_ratio = annualized_return / self.report['max_drawdown']

        return {"calmar_ratio": calmar_ratio}

    def _calculate_win_loss_ratio(self):
        """
        Calcula la relación entre la ganancia promedio y la pérdida promedio.
        """
        ganancia_bruta = self.report.get('ganancia_bruta', 0)
        perdida_bruta = self.report.get('perdida_bruta', 0)
        operaciones_ganadoras = self.report.get('operaciones_ganadoras', 0)
        operaciones_perdedoras = self.report.get('operaciones_perdedoras', 0)

        if operaciones_ganadoras == 0 or operaciones_perdedoras == 0:
            return {"win_loss_ratio": 0}

        avg_win = ganancia_bruta / operaciones_ganadoras
        avg_loss = abs(perdida_bruta / operaciones_perdedoras)

        win_loss_ratio = avg_win / avg_loss if avg_loss != 0 else np.inf

        return {"win_loss_ratio": win_loss_ratio}

    def _identify_patterns(self):
        """
        Identifica patrones básicos en las operaciones. (Placeholder)
        """
        # Futuras implementaciones:
        # - Analizar profit/loss por día de la semana, por hora.
        # - Analizar drawdown periods.
        # - Analizar correlación de pérdidas.
        
        return {"patterns": "No patterns identified yet."}

if __name__ == '__main__':
    # Ejemplo de uso
    # Crear un reporte de backtest de ejemplo
    ejemplo_reporte = {
        "capital_inicial": 10000,
        "capital_final": 11000,
        "profit_neto": 1000,
        "operaciones_totales": 50,
        "operaciones_ganadoras": 30,
        "operaciones_perdedoras": 20,
        "tasa_acierto": 60.0,
        "ganancia_bruta": 2000,
        "perdida_bruta": -1000, # Las pérdidas brutas suelen ser negativas
        "profit_factor": 2.0,
        "max_drawdown": 0.05,
        "historial_operaciones": [],
        "equity_curve": np.linspace(10000, 11000, 1000).tolist()
    }

    evaluator = Evaluator(ejemplo_reporte)
    evaluation = evaluator.evaluate()

    print("--- Reporte de Evaluación ---")
    for key, value in evaluation.items():
        if key not in ["historial_operaciones", "equity_curve"]:
            print(f"{key}: {value:.2f}" if isinstance(value, (int, float)) else f"{key}: {value}")