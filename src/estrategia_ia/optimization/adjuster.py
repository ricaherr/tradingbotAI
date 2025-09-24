import random
import copy

class Adjuster:
    def __init__(self, strategy_config, evaluation_report):
        self.strategy_config = strategy_config
        self.evaluation_report = evaluation_report

    def propose_adjustments(self, exploration_vs_exploitation=0.5):
        """
        Propone ajustes a la estrategia, balanceando exploración (aleatoriedad) y 
        explotación (ajustes guiados).
        """
        if "optimizable_params" not in self.strategy_config:
            return self.strategy_config

        if random.random() < exploration_vs_exploitation:
            return self._propose_random_mutation()
        else:
            return self._propose_guided_adjustment()

    def _propose_random_mutation(self):
        """
        Propone una mutación completamente aleatoria a uno de los parámetros.
        """
        new_config = copy.deepcopy(self.strategy_config)
        param_to_adjust = random.choice(list(new_config["optimizable_params"].keys()))
        
        param_info = new_config["optimizable_params"][param_to_adjust]
        min_val, max_val, step = param_info["min"], param_info["max"], param_info["step"]

        if isinstance(min_val, int):
            num_steps = int((max_val - min_val) / step) + 1
            new_value = min_val + random.randrange(num_steps) * step
        else:
            steps = int((max_val - min_val) / step)
            new_value = min_val + random.randint(0, steps) * step
            new_value = round(new_value, 10)

        new_config[param_to_adjust] = new_value
        return new_config

    def _get_adjustment_direction(self):
        """Determina la dirección del ajuste basado en el rendimiento."""
        profit_neto = self.evaluation_report.get("profit_neto", 0)
        sharpe_ratio = self.evaluation_report.get("sharpe_ratio", 0)
        
        if profit_neto < 0 or sharpe_ratio < 0.5:
            return random.choice([-1, 1])  # Exploración aleatoria
        return 1  # Incrementar por defecto
    
    def _adjust_parameter_value(self, param_to_adjust, params, new_config):
        """Ajusta el valor de un parámetro específico."""
        param_info = params[param_to_adjust]
        current_value = new_config.get(param_to_adjust)
        direction = self._get_adjustment_direction()
        
        step = param_info["step"]
        new_value = current_value + (direction * step)
        
        # Aplicar límites
        new_value = max(param_info["min"], min(param_info["max"], new_value))
        
        if isinstance(param_info["min"], float):
            new_value = round(new_value, 10)
        
        return new_value, current_value
    
    def _propose_guided_adjustment(self):
        """Intenta realizar un ajuste más inteligente basado en el último reporte de evaluación."""
        new_config = copy.deepcopy(self.strategy_config)
        params = new_config.get("optimizable_params", {})
        
        if not params:
            return new_config
        
        param_to_adjust = random.choice(list(params.keys()))
        new_value, current_value = self._adjust_parameter_value(param_to_adjust, params, new_config)
        
        # Si el valor no cambió, intentar mutación aleatoria
        if new_value == current_value and len(params) > 1:
            return self._propose_random_mutation()
        
        new_config[param_to_adjust] = new_value
        return new_config

if __name__ == '__main__':
    # Ejemplo de uso
    from estrategia_ia import config

    # Hacemos una copia para no modificar la configuración original durante la prueba
    estrategia_ejemplo = copy.deepcopy(config.ESTRATEGIAS[0])
    reporte_ejemplo = {"profit_neto": -100} # Simular un reporte con pérdidas

    print("--- Configuración Original ---")
    print(f"ATR_PERIOD: {estrategia_ejemplo.get('ATR_PERIOD', config.ATR_PERIOD)}")
    print(f"MULTI_VELA_ELEFANTE: {estrategia_ejemplo.get('MULTI_VELA_ELEFANTE', config.MULTI_VELA_ELEFANTE)}")

    adjuster = Adjuster(estrategia_ejemplo, reporte_ejemplo)
    nueva_configuracion = adjuster.propose_adjustments()

    print("\n--- Configuración Nueva ---")
    print(f"ATR_PERIOD: {nueva_configuracion.get('ATR_PERIOD', config.ATR_PERIOD)}")
    print(f"MULTI_VELA_ELEFANTE: {nueva_configuracion.get('MULTI_VELA_ELEFANTE', config.MULTI_VELA_ELEFANTE)}")