import sys
import os
import copy

# Add src directory to path to allow imports to work
project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
src_path = os.path.join(project_root_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from estrategia_ia.backtesting.backtester import run_backtest
from estrategia_ia.optimization.evaluator import Evaluator
from estrategia_ia.optimization.adjuster import Adjuster
from estrategia_ia import config

class IntelligentOptimizer:
    def __init__(self, strategy_config, data_file_path):
        self.original_strategy_config = copy.deepcopy(strategy_config)
        self.strategy_config = strategy_config
        self.data_file_path = data_file_path

        # --- FIX: Inicializar la configuración con valores de partida ---
        # Esto asegura que el Adjuster siempre tenga un valor numérico con el que trabajar.
        if "optimizable_params" in self.strategy_config:
            for param, values in self.strategy_config["optimizable_params"].items():
                # Si el parámetro no está definido en el nivel superior, lo inicializamos.
                if param not in self.strategy_config:
                    # Usamos el valor 'min' como punto de partida inicial.
                    self.strategy_config[param] = values["min"]

        self.results_history = []
        self.best_result = None
        self.best_config = None
        self.tested_configs = set()

    def run_optimization_cycles(self, cycles=10):
        """
        Orquesta el proceso de optimización.
        """
        print(f"Iniciando optimización para la estrategia: {self.strategy_config['nombre']}")
        
        for i in range(cycles):
            print(f"\n--- Ciclo de Optimización {i+1}/{cycles} ---")

            # Convertir configuración a una forma hasheable para poder guardarla y compararla
            config_tuple = tuple(self.strategy_config.get(p) for p in self.original_strategy_config["optimizable_params"].keys())

            # Si ya hemos probado esta configuración, intentamos obtener una nueva
            attempts = 0
            while config_tuple in self.tested_configs:
                print("  Configuración ya probada. Intentando un nuevo ajuste...")
                adjuster = Adjuster(self.strategy_config, self.results_history[-1] if self.results_history else {})
                self.strategy_config = adjuster.propose_adjustments(exploration_vs_exploitation=0.9) # Forzar más exploración
                config_tuple = tuple(self.strategy_config.get(p) for p in self.original_strategy_config["optimizable_params"].keys())
                attempts += 1
                if attempts > 10: # Evitar bucles infinitos
                    print("  No se pudo encontrar una configuración nueva después de 10 intentos. Continuando con una mutación aleatoria.")
                    adjuster = Adjuster(self.strategy_config, {})
                    self.strategy_config = adjuster._propose_random_mutation()
                    config_tuple = tuple(self.strategy_config.get(p) for p in self.original_strategy_config["optimizable_params"].keys())
                    break
            
            self.tested_configs.add(config_tuple)

            # Ejecuta el backtest con la configuración actual
            reporte = self._run_backtest()
            
            if reporte:
                # Evalúa los resultados
                evaluator = Evaluator(reporte)
                evaluation_report = evaluator.evaluate()
                self.results_history.append(evaluation_report)
                
                # Imprime un resumen con las métricas evaluadas
                print(f"  Profit Neto: ${evaluation_report['profit_neto']:.2f}")
                print(f"  Sharpe Ratio: {evaluation_report['sharpe_ratio']:.2f}")

                # Comprueba si este resultado es el mejor hasta ahora (usando profit_neto como métrica)
                if self.best_result is None or evaluation_report['profit_neto'] > self.best_result['profit_neto']:
                    print("  ¡Nuevo mejor resultado encontrado!")
                    self.best_result = evaluation_report
                    self.best_config = copy.deepcopy(self.strategy_config)

                # Propone nuevos ajustes para el siguiente ciclo
                adjuster = Adjuster(self.strategy_config, evaluation_report)
                self.strategy_config = adjuster.propose_adjustments()

            else:
                print("  Fallo en la ejecución del backtest.")
                # Si falla, podemos decidir si revertir o intentar algo diferente
                # Por ahora, simplemente no propondremos un nuevo ajuste y dejaremos que el bucle continúe
                # con la misma configuración (que probablemente fallará de nuevo), o podríamos revertir.
                # Revertir puede ser una opción segura.
                self.strategy_config = copy.deepcopy(self.original_strategy_config)

        print("\n--- Optimización Finalizada ---")
        if self.best_result:
            print("Mejor configuración encontrada:")
            # Imprimir solo los parámetros optimizables para claridad
            for param in self.best_config["optimizable_params"].keys():
                print(f"  {param}: {self.best_config[param]}")
            print(f"Mejor Profit Neto: ${self.best_result['profit_neto']:.2f}")
            print(f"Mejor Sharpe Ratio: {self.best_result['sharpe_ratio']:.2f}")
            print(f"Mejor Sortino Ratio: {self.best_result['sortino_ratio']:.2f}")
            print(f"Mejor Calmar Ratio: {self.best_result['calmar_ratio']:.2f}")
            print(f"Mejor Win/Loss Ratio: ${self.best_result['win_loss_ratio']:.2f}")
        else:
            print("No se pudo completar la optimización o encontrar un resultado rentable.")
            
        return self.best_result, self.best_config

    def _run_backtest(self):
        """
        Ejecuta un ciclo de backtesting con la configuración actual de la estrategia.
        """
        reporte = run_backtest(
            self.data_file_path, 
            self.strategy_config, 
            show_plot=False, 
            verbose=False
        )
        return reporte

if __name__ == '__main__':
    # --- CONFIGURACIÓN PARA LA PRUEBA DEL OPTIMIZADOR ---
    NOMBRE_ARCHIVO_DATOS = "EURUSD_M1.csv" 
    
    datos_historicos_csv = os.path.join(project_root_path, "data", "datos_historicos", NOMBRE_ARCHIVO_DATOS)

    # Usamos una copia profunda para no alterar la configuración original
    estrategia_para_optimizar = copy.deepcopy(config.ESTRATEGIAS[0])

    optimizer = IntelligentOptimizer(
        strategy_config=estrategia_para_optimizar, 
        data_file_path=datos_historicos_csv
    )

    # Ejecuta 5 ciclos de optimización
    optimizer.run_optimization_cycles(5)
