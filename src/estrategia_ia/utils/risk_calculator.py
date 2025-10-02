"""
RiskCalculator - Gestión dinámica de riesgo por timeframe
Implementa cálculos de lotes, SL/TP adaptativos según volatilidad y timeframe
"""

from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from typing import Dict, Tuple, Optional
from ..config import TIMEFRAMES_CONFIG, CAPITAL_INICIAL, MIN_LOTE, MAX_LOTE


class RiskCalculator:
    """Calculadora de riesgo adaptativa por timeframe"""
    
    def __init__(self, capital_inicial: float = CAPITAL_INICIAL):
        self.capital_inicial = Decimal(str(capital_inicial))
        self.min_lote = Decimal(str(MIN_LOTE))
        self.max_lote = Decimal(str(MAX_LOTE))
    
    def calcular_lote_dinamico(self, 
                              timeframe: str, 
                              riesgo_porcentaje: float, 
                              atr_value: float, 
                              precio_actual: float,
                              capital_actual: Optional[float] = None) -> float:
        """Calcula lote dinámico basado en timeframe y volatilidad"""
        
        if timeframe not in TIMEFRAMES_CONFIG:
            raise ValueError(f"Timeframe {timeframe} no configurado")
        
        config = TIMEFRAMES_CONFIG[timeframe]
        capital = Decimal(str(capital_actual or self.capital_inicial))
        
        # Aplicar multiplicador de riesgo por timeframe
        riesgo_ajustado = riesgo_porcentaje * config["risk_multiplier"]
        
        # Limitar riesgo máximo por operación
        riesgo_final = min(riesgo_ajustado, config["max_risk_per_trade"])
        
        # Calcular monto en riesgo
        monto_riesgo = capital * Decimal(str(riesgo_final / 100))
        
        # Calcular lote basado en ATR y volatilidad
        atr_ajustado = atr_value * config["volatility_adjustment"]
        
        if atr_ajustado > 0:
            # Lote = Monto_Riesgo / (ATR_Ajustado * Valor_Punto)
            # Asumiendo valor punto = precio_actual / 10000 para forex
            valor_punto = Decimal(str(precio_actual / 10000))
            lote_calculado = monto_riesgo / (Decimal(str(atr_ajustado)) * valor_punto)
        else:
            lote_calculado = self.min_lote
        
        # Aplicar límites
        lote_final = max(self.min_lote, min(lote_calculado, self.max_lote))
        
        return float(lote_final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def calcular_sl_tp_adaptativos(self, 
                                   timeframe: str, 
                                   atr_value: float, 
                                   precio_entrada: float, 
                                   direccion: str,
                                   relacion_rr: float = 2.0) -> Tuple[float, float]:
        """Calcula SL y TP adaptativos según timeframe y ATR"""
        
        if timeframe not in TIMEFRAMES_CONFIG:
            raise ValueError(f"Timeframe {timeframe} no configurado")
        
        config = TIMEFRAMES_CONFIG[timeframe]
        
        # ATR ajustado por timeframe
        atr_ajustado = atr_value * config["volatility_adjustment"]
        
        # Multiplicadores base por timeframe
        sl_multipliers = {
            "M1": 1.5, "M5": 1.8, "M15": 2.0, 
            "M30": 2.2, "H1": 2.5, "H4": 3.0
        }
        
        sl_multiplier = sl_multipliers.get(timeframe, 2.0)
        distancia_sl = atr_ajustado * sl_multiplier
        
        if direccion.upper() in ["BUY", "COMPRA"]:
            stop_loss = precio_entrada - distancia_sl
            take_profit = precio_entrada + (distancia_sl * relacion_rr)
        else:  # SELL/VENTA
            stop_loss = precio_entrada + distancia_sl
            take_profit = precio_entrada - (distancia_sl * relacion_rr)
        
        return round(stop_loss, 5), round(take_profit, 5)
    
    def validar_riesgo_operacion(self, 
                                timeframe: str, 
                                lote: float, 
                                distancia_sl: float, 
                                precio_actual: float,
                                capital_actual: Optional[float] = None) -> Dict[str, any]:
        """Valida si la operación cumple límites de riesgo"""
        
        if timeframe not in TIMEFRAMES_CONFIG:
            return {"valido": False, "razon": f"Timeframe {timeframe} no configurado"}
        
        config = TIMEFRAMES_CONFIG[timeframe]
        capital = capital_actual or self.capital_inicial
        
        # Calcular riesgo real de la operación
        valor_punto = precio_actual / 10000  # Para forex
        riesgo_monetario = lote * distancia_sl * valor_punto
        riesgo_porcentual = (riesgo_monetario / float(capital)) * 100
        
        # Validaciones
        if riesgo_porcentual > config["max_risk_per_trade"]:
            return {
                "valido": False, 
                "razon": f"Riesgo {riesgo_porcentual:.2f}% excede máximo {config['max_risk_per_trade']}%",
                "riesgo_actual": riesgo_porcentual,
                "riesgo_maximo": config["max_risk_per_trade"]
            }
        
        if lote < float(MIN_LOTE) or lote > float(MAX_LOTE):
            return {
                "valido": False, 
                "razon": f"Lote {lote} fuera del rango [{MIN_LOTE}, {MAX_LOTE}]",
                "lote_actual": lote,
                "lote_min": float(MIN_LOTE),
                "lote_max": float(MAX_LOTE)
            }
        
        return {
            "valido": True, 
            "riesgo_porcentual": riesgo_porcentual,
            "riesgo_monetario": riesgo_monetario,
            "lote_validado": lote
        }
    
    def calcular_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcula ATR (Average True Range)"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def ajustar_riesgo_por_drawdown(self, 
                                   drawdown_actual: float, 
                                   riesgo_base: float,
                                   timeframe: str) -> float:
        """Ajusta riesgo según drawdown actual"""
        
        if timeframe not in TIMEFRAMES_CONFIG:
            return riesgo_base
        
        config = TIMEFRAMES_CONFIG[timeframe]
        
        # Reducir riesgo si hay drawdown significativo
        if drawdown_actual > 10:  # 10% drawdown
            factor_reduccion = 0.5
        elif drawdown_actual > 5:   # 5% drawdown
            factor_reduccion = 0.7
        else:
            factor_reduccion = 1.0
        
        riesgo_ajustado = riesgo_base * factor_reduccion * config["risk_multiplier"]
        
        # Aplicar límite máximo
        return min(riesgo_ajustado, config["max_risk_per_trade"])