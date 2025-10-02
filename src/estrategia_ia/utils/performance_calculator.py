"""
PerformanceCalculator - Cálculos unificados de métricas de performance
Corrige inconsistencias entre BrokerSimulator y Evaluator
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from ..config import TIMEFRAMES_CONFIG


class PerformanceCalculator:
    """Calculadora unificada de métricas de performance"""
    
    def __init__(self, timeframe: str = "M15"):
        self.timeframe = timeframe
        if timeframe in TIMEFRAMES_CONFIG:
            self.periods_per_year = TIMEFRAMES_CONFIG[timeframe]["periods_per_year"]
        else:
            # Fallback para timeframes no configurados
            self.periods_per_year = 252 * 24 * 4  # M15 por defecto
    
    def calculate_returns(self, equity_curve: List[float]) -> pd.Series:
        """Calcula retornos desde equity curve"""
        if not equity_curve or len(equity_curve) < 2:
            return pd.Series([0])
        
        equity_series = pd.Series(equity_curve)
        returns = equity_series.pct_change().dropna()
        return returns
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0) -> float:
        """Calcula Sharpe Ratio usando periods_per_year correcto"""
        if returns.empty or returns.std() == 0:
            return 0
        
        excess_returns = returns - (risk_free_rate / self.periods_per_year)
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(self.periods_per_year)
        
        # Limitar valores extremos para evitar resultados irreales
        if np.isnan(sharpe) or np.isinf(sharpe):
            return 0
        
        # Limitar Sharpe a rango razonable [-10, 10]
        sharpe = max(-10, min(10, sharpe))
        
        return float(sharpe)
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0) -> float:
        """Calcula Sortino Ratio usando periods_per_year correcto"""
        if returns.empty:
            return 0
        
        excess_returns = returns - (risk_free_rate / self.periods_per_year)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 10 if excess_returns.mean() > 0 else 0  # Limitar en lugar de inf
        
        sortino = excess_returns.mean() / downside_returns.std() * np.sqrt(self.periods_per_year)
        
        # Limitar valores extremos
        if np.isnan(sortino) or np.isinf(sortino):
            return 0
        
        # Limitar Sortino a rango razonable [-10, 10]
        sortino = max(-10, min(10, sortino))
        
        return float(sortino)
    
    def calculate_calmar_ratio(self, total_return: float, max_drawdown: float, num_periods: int) -> float:
        """Calcula Calmar Ratio"""
        if max_drawdown == 0 or num_periods == 0:
            return 0
        
        # Anualizar el retorno total
        periods_in_year = self.periods_per_year
        years = num_periods / periods_in_year
        
        if years <= 0:
            return 0
        
        annualized_return = (1 + total_return) ** (1 / years) - 1
        calmar = annualized_return / abs(max_drawdown)
        
        # Limitar valores extremos
        if np.isnan(calmar) or np.isinf(calmar):
            return 0
        
        # Limitar Calmar a rango razonable [-10, 10]
        calmar = max(-10, min(10, calmar))
        
        return float(calmar)
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict[str, float]:
        """Calcula máximo drawdown"""
        if not equity_curve or len(equity_curve) < 2:
            return {"max_drawdown": 0, "max_drawdown_percent": 0}
        
        equity_series = pd.Series(equity_curve)
        peak_series = equity_series.cummax()
        drawdown_series = (equity_series - peak_series) / peak_series
        
        max_drawdown = abs(drawdown_series.min())
        max_drawdown_value = (peak_series - equity_series).max()
        
        return {
            "max_drawdown": float(max_drawdown),
            "max_drawdown_percent": float(max_drawdown * 100),
            "max_drawdown_value": float(max_drawdown_value)
        }
    
    def calculate_win_loss_ratio(self, ganancia_bruta: float, perdida_bruta: float, 
                                ops_ganadoras: int, ops_perdedoras: int) -> float:
        """Calcula Win/Loss Ratio"""
        if ops_ganadoras == 0 or ops_perdedoras == 0 or perdida_bruta == 0:
            return float('inf') if ops_ganadoras > 0 else 0
        
        avg_win = ganancia_bruta / ops_ganadoras
        avg_loss = abs(perdida_bruta) / ops_perdedoras
        
        return avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    def calculate_comprehensive_metrics(self, reporte: Dict) -> Dict:
        """Calcula todas las métricas de manera consistente"""
        equity_curve = reporte.get('equity_curve', [])
        returns = self.calculate_returns(equity_curve)
        
        # Métricas básicas
        total_return = (reporte['capital_final'] / reporte['capital_inicial']) - 1
        drawdown_metrics = self.calculate_max_drawdown(equity_curve)
        
        # Métricas de riesgo-retorno
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        calmar = self.calculate_calmar_ratio(total_return, drawdown_metrics['max_drawdown'], len(equity_curve))
        
        # Win/Loss metrics
        win_loss_ratio = self.calculate_win_loss_ratio(
            reporte.get('ganancia_bruta', 0),
            reporte.get('perdida_bruta', 0),
            reporte.get('operaciones_ganadoras', 0),
            reporte.get('operaciones_perdedoras', 0)
        )
        
        # Profit Factor
        profit_factor = (reporte.get('ganancia_bruta', 0) / abs(reporte.get('perdida_bruta', 1))) if reporte.get('perdida_bruta', 0) != 0 else float('inf')
        
        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'win_loss_ratio': win_loss_ratio,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'total_return_percent': total_return * 100,
            **drawdown_metrics,
            'periods_per_year': self.periods_per_year,
            'timeframe': self.timeframe
        }
    
    def validate_metrics(self, metrics: Dict) -> Dict[str, bool]:
        """Valida que las métricas sean razonables"""
        validations = {
            'sharpe_reasonable': -10 <= metrics.get('sharpe_ratio', 0) <= 10,
            'sortino_reasonable': -10 <= metrics.get('sortino_ratio', 0) <= 10,
            'calmar_reasonable': -10 <= metrics.get('calmar_ratio', 0) <= 10,
            'drawdown_reasonable': 0 <= metrics.get('max_drawdown', 0) <= 1,
            'profit_factor_reasonable': metrics.get('profit_factor', 0) >= 0,
            'total_return_reasonable': -1 <= metrics.get('total_return', 0) <= 10
        }
        
        return validations