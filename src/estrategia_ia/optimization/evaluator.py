import numpy as np
import pandas as pd
from ..core.metrics_calculator import CalculatorFactory

class Evaluator:
    def __init__(self, backtest_report, timeframe: str = "H1"):
        """
        Inicializa evaluador con reporte de backtest y timeframe.
        
        Args:
            backtest_report: Reporte del backtest
            timeframe: Timeframe usado (M1, M5, M15, M30, H1, H4)
        """
        self.report = backtest_report
        self.timeframe = timeframe
        self.metrics_calc = CalculatorFactory.create_metrics_calculator(timeframe)
        
        # Usar retornos diarios si están disponibles, sino calcular desde equity_curve
        if 'retornos_diarios' in self.report and len(self.report['retornos_diarios']) > 0:
            self.returns = pd.Series(self.report['retornos_diarios'])
        elif 'equity_curve' in self.report and len(self.report['equity_curve']) > 0:
            self.returns = pd.Series(self.report['equity_curve']).pct_change().dropna()
        else:
            # Fallback: crear retornos sintéticos basados en profit_neto
            profit_neto = self.report.get('profit_neto', 0)
            capital_inicial = self.report.get('capital_inicial', 1000)
            operaciones_totales = self.report.get('operaciones_totales', 1)
            if operaciones_totales > 0:
                retorno_promedio = (profit_neto / capital_inicial) / operaciones_totales
                self.returns = pd.Series([retorno_promedio] * operaciones_totales)
            else:
                self.returns = pd.Series([0])

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
        evaluation_report.update(self._calculate_monthly_metrics())
        evaluation_report.update(self._evaluate_profitability())
        evaluation_report.update(self._identify_patterns())
        
        return evaluation_report

    def _calculate_sharpe_ratio(self, risk_free_rate=0):
        """
        Calcula el Sharpe Ratio usando MetricsCalculator.
        """
        sharpe_ratio = self.metrics_calc.calculate_sharpe_ratio(self.returns, risk_free_rate)
        return {"sharpe_ratio": sharpe_ratio}

    def _calculate_sortino_ratio(self, risk_free_rate=0):
        """
        Calcula el Sortino Ratio usando MetricsCalculator.
        """
        sortino_ratio = self.metrics_calc.calculate_sortino_ratio(self.returns, risk_free_rate)
        return {"sortino_ratio": sortino_ratio}

    def _calculate_calmar_ratio(self):
        """
        Calcula el Calmar Ratio usando MetricsCalculator.
        """
        total_return = (self.report['capital_final'] / self.report['capital_inicial']) - 1
        max_drawdown = self.report.get('max_drawdown', 0)
        num_periods = len(self.report.get('equity_curve', []))
        
        calmar_ratio = self.metrics_calc.calculate_calmar_ratio(total_return, max_drawdown, num_periods)
        return {"calmar_ratio": calmar_ratio}

    def _calculate_win_loss_ratio(self):
        """
        Calcula la relación entre la ganancia promedio y la pérdida promedio usando MetricsCalculator.
        """
        ganancia_bruta = self.report.get('ganancia_bruta', 0)
        perdida_bruta = self.report.get('perdida_bruta', 0)
        operaciones_ganadoras = self.report.get('operaciones_ganadoras', 0)
        operaciones_perdedoras = self.report.get('operaciones_perdedoras', 0)
        
        win_loss_ratio = self.metrics_calc.calculate_win_loss_ratio(
            ganancia_bruta, perdida_bruta, operaciones_ganadoras, operaciones_perdedoras
        )
        
        return {"win_loss_ratio": win_loss_ratio}

    def _calculate_monthly_metrics(self):
        """
        Calcula métricas de rentabilidad mensual usando MetricsCalculator.
        """
        capital_inicial = self.report.get('capital_inicial', 1000)
        profit_neto = self.report.get('profit_neto', 0)
        
        # Obtener período de diferentes fuentes posibles
        periodo_dias = self.report.get('periodo_dias')
        if periodo_dias is None:
            # Calcular desde fechas si están disponibles
            fecha_inicio = self.report.get('fecha_inicio')
            fecha_fin = self.report.get('fecha_fin')
            if fecha_inicio and fecha_fin:
                from datetime import datetime
                if isinstance(fecha_inicio, str):
                    fecha_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                if isinstance(fecha_fin, str):
                    fecha_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                periodo_dias = (fecha_fin - fecha_inicio).days
            else:
                # Usar 90 días como default (3 meses)
                periodo_dias = 90
        
        # Calcular ROI usando MetricsCalculator
        roi_metrics = self.metrics_calc.calculate_monthly_roi(profit_neto, capital_inicial, periodo_dias)
        
        # Calcular win rate
        operaciones_totales = self.report.get('operaciones_totales', 0)
        operaciones_ganadoras = self.report.get('operaciones_ganadoras', 0)
        win_rate_pct = (operaciones_ganadoras / operaciones_totales * 100) if operaciones_totales > 0 else 0
        
        # Max drawdown en porcentaje
        max_drawdown_pct = abs(self.report.get('max_drawdown_percent', 0))
        
        return {
            **roi_metrics,
            'win_rate_pct': win_rate_pct,
            'max_drawdown_pct': max_drawdown_pct,
            'periodo_meses': periodo_dias / 30.44
        }
    
    def _evaluate_profitability(self, min_monthly_return=0.2, max_drawdown=25.0, min_win_rate=30.0):
        """
        Evalúa si la estrategia cumple criterios de rentabilidad.
        """
        roi_mensual = getattr(self, '_roi_mensual_pct', 0)
        max_dd = getattr(self, '_max_drawdown_pct', 0) 
        win_rate = getattr(self, '_win_rate_pct', 0)
        sharpe = self._calculate_sharpe_ratio().get('sharpe_ratio', 0)
        operaciones = self.report.get('operaciones_totales', 0)
        
        # Recalcular si no están disponibles
        if roi_mensual == 0:
            monthly_metrics = self._calculate_monthly_metrics()
            roi_mensual = monthly_metrics['roi_mensual_pct']
            max_dd = monthly_metrics['max_drawdown_pct']
            win_rate = monthly_metrics['win_rate_pct']
        
        criterios = {
            'roi_mensual_ok': roi_mensual >= min_monthly_return,
            'drawdown_ok': max_dd <= max_drawdown,
            'win_rate_ok': win_rate >= min_win_rate,
            'sharpe_ok': sharpe > 0.5,  # Más realista
            'operaciones_ok': operaciones >= 10  # Menos estricto
        }
        
        criterios_cumplidos = sum(criterios.values())
        # Priorizar ROI positivo sobre criterios estrictos
        viable = roi_mensual > 0 and criterios_cumplidos >= 3  # 3 de 5 criterios + ROI positivo
        score = (criterios_cumplidos / len(criterios)) * 100
        
        return {
            'viable': viable,
            'profitability_score': score,
            'criterios_rentabilidad': criterios
        }
    
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
        if key not in ["historial_operaciones", "equity_curve", "criterios_rentabilidad"]:
            if isinstance(value, (int, float)):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
    
    print(f"\nViable: {'SÍ' if evaluation['viable'] else 'NO'}")
    print(f"Score: {evaluation['profitability_score']:.1f}%")