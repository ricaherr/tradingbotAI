"""
MetricsCalculator: Calculadora de métricas financieras específica por timeframe.
Implementa cálculos precisos de Sharpe, Sortino, Calmar y otras métricas.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional


class MetricsCalculator:
    """
    Calculadora de métricas financieras que ajusta cálculos según el timeframe.
    
    Responsabilidades:
    - Calcular Sharpe Ratio con periods_per_year correcto
    - Calcular Sortino Ratio ajustado por timeframe
    - Calcular Calmar Ratio con anualización apropiada
    - Calcular métricas de rentabilidad mensual
    """
    
    def __init__(self, timeframe_config: Dict[str, Any]):
        """
        Inicializa calculadora con configuración específica del timeframe.
        
        Args:
            timeframe_config: Configuración del timeframe desde TIMEFRAMES_CONFIG
        """
        self.config = timeframe_config
        self.periods_per_year = timeframe_config["periods_per_year"]
        self.timeframe_name = timeframe_config["name"]
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Calcula Sharpe Ratio anualizado correctamente para el timeframe.
        
        Args:
            returns: Serie de retornos
            risk_free_rate: Tasa libre de riesgo anualizada
            
        Returns:
            Sharpe Ratio anualizado
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0 or np.isnan(std_return):
            if mean_return > risk_free_per_period:
                return float('inf')
            elif mean_return < risk_free_per_period:
                return float('-inf')
            else:
                return 0.0
        
        # Convertir risk_free_rate anual a rate por período
        risk_free_per_period = risk_free_rate / self.periods_per_year
        
        # Calcular Sharpe y anualizar
        sharpe_ratio = (mean_return - risk_free_per_period) / std_return
        annualized_sharpe = sharpe_ratio * np.sqrt(self.periods_per_year)
        
        return float(annualized_sharpe)
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """
        Calcula Sortino Ratio (penaliza solo volatilidad negativa).
        
        Args:
            returns: Serie de retornos
            risk_free_rate: Tasa libre de riesgo anualizada
            
        Returns:
            Sortino Ratio anualizado
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = returns.mean()
        
        # Solo retornos negativos para downside deviation
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return np.inf if mean_return > 0 else 0.0
        
        downside_std = negative_returns.std()
        if downside_std == 0:
            return np.inf if mean_return > 0 else 0.0
        
        # Convertir risk_free_rate anual a rate por período
        risk_free_per_period = risk_free_rate / self.periods_per_year
        
        # Calcular Sortino y anualizar
        sortino_ratio = (mean_return - risk_free_per_period) / downside_std
        annualized_sortino = sortino_ratio * np.sqrt(self.periods_per_year)
        
        return float(annualized_sortino)
    
    def calculate_calmar_ratio(self, total_return: float, max_drawdown: float, 
                             num_periods: int) -> float:
        """
        Calcula Calmar Ratio (Retorno Anualizado / Máximo Drawdown).
        
        Args:
            total_return: Retorno total del período
            max_drawdown: Máximo drawdown (como decimal positivo)
            num_periods: Número de períodos en el backtest
            
        Returns:
            Calmar Ratio
        """
        if max_drawdown == 0 or num_periods <= 0:
            return 0.0
        
        if total_return <= -1:  # Pérdida total
            return -np.inf
        
        try:
            # Anualizar el retorno
            annualized_return = (1 + total_return) ** (self.periods_per_year / num_periods) - 1
            calmar_ratio = annualized_return / max_drawdown
            return float(calmar_ratio)
        except (ValueError, OverflowError, ZeroDivisionError):
            return 0.0
    
    def calculate_monthly_roi(self, profit_neto: float, capital_inicial: float, 
                            periodo_dias: int) -> Dict[str, float]:
        """
        Calcula métricas de ROI mensual y anual.
        
        Args:
            profit_neto: Profit neto en dinero
            capital_inicial: Capital inicial
            periodo_dias: Días del backtest
            
        Returns:
            Dict con roi_total_pct, roi_mensual_pct, roi_anual_pct
        """
        if capital_inicial <= 0 or periodo_dias <= 0:
            return {"roi_total_pct": 0.0, "roi_mensual_pct": 0.0, "roi_anual_pct": 0.0}
        
        roi_total_pct = (profit_neto / capital_inicial) * 100
        periodo_meses = periodo_dias / 30.44  # Promedio días por mes
        
        roi_mensual_pct = roi_total_pct / periodo_meses if periodo_meses > 0 else 0.0
        roi_anual_pct = roi_mensual_pct * 12
        
        return {
            "roi_total_pct": float(roi_total_pct),
            "roi_mensual_pct": float(roi_mensual_pct), 
            "roi_anual_pct": float(roi_anual_pct)
        }
    
    def calculate_win_loss_ratio(self, ganancia_bruta: float, perdida_bruta: float,
                               operaciones_ganadoras: int, operaciones_perdedoras: int) -> float:
        """
        Calcula relación ganancia promedio / pérdida promedio.
        
        Args:
            ganancia_bruta: Ganancia bruta total
            perdida_bruta: Pérdida bruta total (valor negativo)
            operaciones_ganadoras: Número de operaciones ganadoras
            operaciones_perdedoras: Número de operaciones perdedoras
            
        Returns:
            Win/Loss Ratio
        """
        if operaciones_ganadoras == 0 or operaciones_perdedoras == 0:
            return 0.0
        
        avg_win = ganancia_bruta / operaciones_ganadoras
        avg_loss = abs(perdida_bruta / operaciones_perdedoras)
        
        if avg_loss == 0:
            return np.inf if avg_win > 0 else 0.0
        
        return float(avg_win / avg_loss)
    
    def get_timeframe_info(self) -> Dict[str, Any]:
        """
        Retorna información del timeframe para debugging.
        
        Returns:
            Dict con información del timeframe
        """
        return {
            "timeframe_name": self.timeframe_name,
            "periods_per_year": self.periods_per_year,
            "minutes_per_period": self.config.get("minutes_per_period", 0)
        }


class CalculatorFactory:
    """
    Factory para crear calculadoras de métricas según timeframe.
    Implementa patrón Factory para mantener Single Responsibility.
    """
    
    @staticmethod
    def create_metrics_calculator(timeframe: str) -> MetricsCalculator:
        """
        Crea calculadora de métricas para el timeframe especificado.
        
        Args:
            timeframe: Nombre del timeframe (M1, M5, M15, M30, H1, H4)
            
        Returns:
            MetricsCalculator configurado para el timeframe
            
        Raises:
            ValueError: Si el timeframe no es válido
        """
        from ..config import TIMEFRAMES_CONFIG
        
        if timeframe not in TIMEFRAMES_CONFIG:
            raise ValueError(f"Timeframe '{timeframe}' no válido. Válidos: {list(TIMEFRAMES_CONFIG.keys())}")
        
        config = TIMEFRAMES_CONFIG[timeframe]
        return MetricsCalculator(config)