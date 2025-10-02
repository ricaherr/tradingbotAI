import sys
import os
import copy
import random
import signal
import logging
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count

# Add src directory to path to allow imports to work
project_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
src_path = os.path.join(project_root_path, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from estrategia_ia.backtesting.backtester import run_backtest
from estrategia_ia.optimization.evaluator import Evaluator
from estrategia_ia.optimization.adjuster import Adjuster
from estrategia_ia.optimization.fitness_worker import run_fitness_calculation
from estrategia_ia import config


def worker_init():
    """
    Initializer for worker processes to ignore interrupt signals.
    This allows the main process to handle KeyboardInterrupt gracefully.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


# La función run_fitness_calculation ahora está en fitness_worker.py


class IntelligentOptimizer:
    def __init__(self, strategy_config, data_file_path):
        self.original_strategy_config = copy.deepcopy(strategy_config)
        self.strategy_config = strategy_config
        self.data_file_path = data_file_path

        if "optimizable_params" in self.strategy_config:
            for param, values in self.strategy_config["optimizable_params"].items():
                if param not in self.strategy_config:
                    self.strategy_config[param] = values["min"]

        self.results_history = []
        self.convergence_history = []
        self.best_result = None
        self.best_config = None
        self.tested_configs = set()

    def run_optimization_cycles(self, cycles=10):
        print(f"Iniciando optimización para la estrategia: {self.strategy_config['nombre']}")

        for i in range(cycles):
            print(f"  Ciclo {i + 1}/{cycles}")

            config_tuple = tuple(
                self.strategy_config.get(p) for p in self.original_strategy_config["optimizable_params"].keys())

            attempts = 0
            max_attempts = 10
            param_keys = list(self.original_strategy_config["optimizable_params"].keys())
            
            while config_tuple in self.tested_configs and attempts < max_attempts:
                adjuster = Adjuster(self.strategy_config, self.results_history[-1] if self.results_history else {})
                self.strategy_config = adjuster.propose_adjustments(exploration_vs_exploitation=0.9)
                config_tuple = tuple(self.strategy_config.get(p) for p in param_keys)
                attempts += 1
                
            if attempts >= max_attempts:
                adjuster = Adjuster(self.strategy_config, {})
                self.strategy_config = adjuster._propose_random_mutation()
                config_tuple = tuple(self.strategy_config.get(p) for p in param_keys)

            self.tested_configs.add(config_tuple)
            reporte = self._run_backtest()

            if reporte:
                evaluator = Evaluator(reporte)
                evaluation_report = evaluator.evaluate()
                self.results_history.append(evaluation_report)

                
                

                if self.best_result is None or evaluation_report['profit_neto'] > self.best_result['profit_neto']:
                    
                    self.best_result = evaluation_report
                    self.best_config = copy.deepcopy(self.strategy_config)

                adjuster = Adjuster(self.strategy_config, evaluation_report)
                self.strategy_config = adjuster.propose_adjustments()
            else:
                
                self.strategy_config = copy.deepcopy(self.original_strategy_config)
                if "optimizable_params" in self.strategy_config:
                    for param, values in self.strategy_config["optimizable_params"].items():
                        if param not in self.strategy_config:
                            self.strategy_config[param] = values["min"]

            if self.best_result:
                self.convergence_history.append(self.best_result.get('sharpe_ratio', 0))
            else:
                self.convergence_history.append(0)

        print("\n--- Optimización Finalizada ---")
        if self.best_result:
            print("Mejor configuración encontrada:")
            for param in self.best_config["optimizable_params"].keys():
                print(f"  {param}: {self.best_config[param]}")
            print(f"Mejor Profit Neto: ${self.best_result['profit_neto']:.2f}")
            print(f"Mejor Sharpe Ratio: {self.best_result['sharpe_ratio']:.2f}")
            print(f"Mejor Sortino Ratio: {self.best_result['sortino_ratio']:.2f}")
            print(f"Mejor Calmar Ratio: {self.best_result['calmar_ratio']:.2f}")
            print(f"Mejor Win/Loss Ratio: {self.best_result['win_loss_ratio']:.2f}")
        else:
            print("No se pudo completar la optimización.")

        return self.best_result, self.best_config

    def _run_backtest(self):
        reporte = run_backtest(
            self.data_file_path,
            self.strategy_config,
            show_plot=False,
            verbose=False
        )
        return reporte


class GeneticOptimizer:
    def __init__(self, strategy_config, data_file_path, population_size=50, generations=20, mutation_rate=0.1,
                 crossover_rate=0.8, tournament_size=3, cpu_core_usage=0.7, backtest_period_years=None, 
                 test_mode=False):
        self.strategy_config_base = copy.deepcopy(strategy_config)
        self.data_file_path = data_file_path
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.cpu_core_usage = cpu_core_usage
        self.param_ranges = self.strategy_config_base["optimizable_params"]
        self.backtest_period_years = backtest_period_years
        self.test_mode = test_mode
        self.best_individual = None
        self.best_fitness = -float('inf')
        self.best_report = None
        self.convergence_history = []

    def run_optimization(self):
        start_time = datetime.now()
        optimization_start = time.time()
        print(f"[{start_time.strftime('%H:%M:%S')}] Iniciando optimización genética para: {self.strategy_config_base['nombre']}")
        print(f"Configuración: {self.population_size} individuos × {self.generations} generaciones = {self.population_size * self.generations} evaluaciones")
        
        population = self._create_initial_population()

        for gen in range(self.generations):
            gen_start_time = time.time()
            elapsed_total = (gen_start_time - optimization_start) / 60
            print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] Generación {gen + 1}/{self.generations} (Tiempo transcurrido: {elapsed_total:.1f}m)")

            valid_population = [ind for ind in population if ind is not None]

            fitness_scores = self._evaluate_population(valid_population)

            self._update_best_individual(valid_population, fitness_scores)

            self.convergence_history.append(self.best_fitness if self.best_fitness > -float('inf') else 0)

            population = self._create_next_generation(valid_population, fitness_scores)
            
            gen_elapsed = (time.time() - gen_start_time) / 60
            if fitness_scores:
                print(f"    Mejor Fitness: {max(fitness_scores):.2f} | Tiempo generación: {gen_elapsed:.1f}m")
                # Estimar tiempo restante
                if gen > 0:
                    avg_time_per_gen = elapsed_total / (gen + 1)
                    remaining_gens = self.generations - (gen + 1)
                    estimated_remaining = avg_time_per_gen * remaining_gens
                    print(f"    Tiempo estimado restante: {estimated_remaining:.1f}m")
            else:
                print("    No se encontraron individuos válidos en esta generación.")

        total_elapsed = (time.time() - optimization_start) / 60
        end_time = datetime.now()
        print(f"\n--- Optimización Genética Finalizada [{end_time.strftime('%H:%M:%S')}] ---")
        print(f"Tiempo total: {total_elapsed:.1f} minutos")
        if self.best_individual:
            print("Mejor configuración encontrada:")
            for param, value in self.best_individual.items():
                if param == 'timeframe':
                    from estrategia_ia.config import TIMEFRAMES_CONFIG
                    timeframe_keys = list(TIMEFRAMES_CONFIG.keys())
                    if 0 <= int(value) < len(timeframe_keys):
                        tf_name = TIMEFRAMES_CONFIG[timeframe_keys[int(value)]]['name']
                        print(f"  {param}: {value} ({tf_name})")
                    else:
                        print(f"  {param}: {value}")
                else:
                    print(f"  {param}: {value}")

            if not self.best_report:
                self.best_report = self._run_backtest(self.best_individual)

            if self.best_report:
                # Agregar backtest_days al reporte si está disponible
                if 'backtest_days' in self.strategy_config_base:
                    self.best_report['periodo_dias'] = self.strategy_config_base['backtest_days']
                
                evaluator = Evaluator(self.best_report)
                evaluation_report = evaluator.evaluate()

                print(f"Mejor Fitness (Sharpe Ratio): {evaluation_report.get('sharpe_ratio', 0):.2f}")
                print(f"Profit Neto: ${evaluation_report.get('profit_neto', 0):.2f}")
                print(f"ROI Mensual: {evaluation_report.get('roi_mensual_pct', 0):.2f}%")
                print(f"Sortino Ratio: {evaluation_report.get('sortino_ratio', 0):.2f}")
                print(f"Calmar Ratio: {evaluation_report.get('calmar_ratio', 0):.2f}")
                print(f"Win/Loss Ratio: {evaluation_report.get('win_loss_ratio', 0):.2f}")

                return evaluation_report, self.best_individual
            else:
                print("Error: No se pudo generar el reporte final.")
                return None, self.best_individual
        else:
            print("No se pudo encontrar una solución viable.")
            return None, None

    def _create_next_generation(self, valid_population, fitness_scores):
        """Crea la siguiente generación usando selección, cruce y mutación."""
        new_population = []
        
        # Elitismo: mantener el mejor individuo
        if self.best_individual is not None:
            new_population.append(self.best_individual)

        while len(new_population) < self.population_size:
            parent1 = self._selection(valid_population, fitness_scores)
            parent2 = self._selection(valid_population, fitness_scores)

            if random.random() < self.crossover_rate:
                child = self._crossover(parent1, parent2)
            else:
                child = copy.deepcopy(parent1)

            if random.random() < self.mutation_rate:
                child = self._mutate(child)

            new_population.append(child)

        return new_population
    
    def _update_best_individual(self, valid_population, fitness_scores):
        """Actualiza el mejor individuo si se encuentra uno mejor."""
        if any(f > -float('inf') for f in fitness_scores):
            current_best_idx = max(range(len(fitness_scores)), key=fitness_scores.__getitem__)
            current_best_fitness = fitness_scores[current_best_idx]

            if current_best_fitness > self.best_fitness:
                self.best_fitness = current_best_fitness
                self.best_individual = valid_population[current_best_idx]
                self.best_report = self._run_backtest(self.best_individual)
                print(f"  ¡Nuevo mejor individuo! Fitness (Sharpe): {self.best_fitness:.2f}")
    
    def _evaluate_population(self, valid_population):
        """Evalúa una población usando procesamiento paralelo con fallback secuencial."""
        
        # En modo test o poblaciones pequeñas, usar evaluación secuencial directamente
        if self.test_mode or self.population_size <= 10 or self.cpu_core_usage == 0.0:
            eval_start = time.time()
            print(f"    Evaluando {len(valid_population)} individuos (secuencial)...")
            fitness_scores = []
            for i, individual in enumerate(valid_population):
                ind_start = time.time()
                fitness = self._calculate_fitness(individual)
                fitness_scores.append(fitness)
                
                # Mostrar progreso cada 5 individuos con tiempo
                if (i + 1) % 5 == 0 or (i + 1) == len(valid_population):
                    elapsed = (time.time() - eval_start) / 60
                    avg_time = elapsed / (i + 1) * len(valid_population)
                    print(f"      Progreso: {i + 1}/{len(valid_population)} | {elapsed:.1f}m transcurridos | ETA: {avg_time:.1f}m")
            return fitness_scores
        
        # Para poblaciones grandes, intentar multiprocessing
        args_for_pool = [
            (ind, self.strategy_config_base, self.data_file_path, self.backtest_period_years, self.test_mode) for
            ind in valid_population
        ]

        try:
            total_cores = cpu_count()
            num_cores = max(1, int(total_cores * self.cpu_core_usage))
            
            eval_start = time.time()
            print(f"    Evaluando {len(valid_population)} individuos (paralelo con {num_cores} cores)...")
            
            with Pool(processes=num_cores, initializer=worker_init) as pool:
                result = pool.map_async(run_fitness_calculation, args_for_pool)

                # Mostrar progreso mientras espera
                check_count = 0
                while not result.ready():
                    result.wait(timeout=10)
                    check_count += 1
                    elapsed = (time.time() - eval_start) / 60
                    print(f"      Procesando en paralelo... ({elapsed:.1f}m transcurridos)")
                    
                    # Si toma más de 5 minutos, mostrar advertencia
                    if elapsed > 5 and check_count % 3 == 0:
                        print(f"      [ADVERTENCIA] Evaluación tomando más tiempo del esperado: {elapsed:.1f}m")

                return result.get()

        except KeyboardInterrupt:
            print("\n  Interrupción de teclado detectada. Guardando progreso...")
            if self.best_individual and self.best_fitness > -float('inf'):
                print(f"  Mejor resultado hasta ahora: Fitness={self.best_fitness:.2f}")
            raise

        except Exception as e:
            print(f"  Error durante la evaluación en paralelo: {e}")
            print("  Volviendo a evaluación secuencial para esta generación.")
            fitness_scores = []
            for i, individual in enumerate(valid_population):
                fitness = self._calculate_fitness(individual)
                fitness_scores.append(fitness)
                if (i + 1) % 5 == 0:
                    print(f"      Progreso fallback: {i + 1}/{len(valid_population)}")
            return fitness_scores
    
    def _create_initial_population(self):
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param, values in self.param_ranges.items():
                step = values.get("step", 1)
                is_float = any(isinstance(v, float) for v in [values["min"], values["max"], step])

                if is_float:
                    val = random.uniform(values["min"], values["max"])
                    if step > 0:
                        val = round(val / step) * step
                    individual[param] = max(values["min"], min(values["max"], val))
                else:
                    individual[param] = random.randrange(values["min"], values["max"] + 1, step)
            population.append(individual)
        return population

    def _calculate_fitness(self, individual):
        report = self._run_backtest(individual)
        if not report or report['operaciones_totales'] < 1:
            return -float('inf')

        # Agregar backtest_days al reporte si está disponible
        if 'backtest_days' in self.strategy_config_base:
            report['periodo_dias'] = self.strategy_config_base['backtest_days']

        evaluator = Evaluator(report)
        evaluation = evaluator.evaluate()
        return evaluation.get('sharpe_ratio', -float('inf'))

    def _selection(self, population, fitness_scores):
        # Tournament Selection
        if not population or not fitness_scores: 
            return random.choice(population) if population else None
        
        # Ajustar tournament_size si es mayor que la población
        actual_tournament_size = min(self.tournament_size, len(population))
        tournament = random.sample(list(zip(population, fitness_scores)), actual_tournament_size)
        winner = max(tournament, key=lambda x: x[1])
        return winner[0]

    def _crossover(self, parent1, parent2):
        child = {}
        params = list(self.param_ranges.keys())
        if len(params) <= 1: return copy.deepcopy(parent1)
        crossover_point = random.randint(1, len(params) - 1)

        for i, param in enumerate(params):
            if i < crossover_point:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child

    def _mutate(self, individual):
        mutated_individual = copy.deepcopy(individual)
        param_to_mutate = random.choice(list(self.param_ranges.keys()))
        values = self.param_ranges[param_to_mutate]
        step = values.get("step", 1)

        is_float = any(isinstance(v, float) for v in [values["min"], values["max"], step])

        if is_float:
            val = random.uniform(values["min"], values["max"])
            if step > 0:
                val = round(val / step) * step
            mutated_individual[param_to_mutate] = max(values["min"], min(values["max"], val))
        else:
            mutated_individual[param_to_mutate] = random.randrange(values["min"], values["max"] + 1, step)

        return mutated_individual

    def _run_backtest(self, individual_params):
        strategy_config = copy.deepcopy(self.strategy_config_base)
        strategy_config.update(individual_params)
        
        # Convertir días a años si está especificado
        backtest_years = self.backtest_period_years
        if 'backtest_days' in strategy_config:
            backtest_years = strategy_config['backtest_days'] / 365.25

        report = run_backtest(
            self.data_file_path,
            strategy_config,
            show_plot=False,
            verbose=False,
            backtest_period_years=backtest_years
        )
        return report


if __name__ == '__main__':
    # --- CONFIGURACIÓN PARA LA PRUEBA DEL OPTIMIZADOR ---
    NOMBRE_ARCHIVO_DATOS = "EURUSD_M1.csv" 

    datos_historicos_csv = os.path.join(project_root_path, "data", "datos_historicos", NOMBRE_ARCHIVO_DATOS)

    estrategia_para_optimizar = copy.deepcopy(config.ESTRATEGIAS[0])

    print("\n" + "=" * 50)
    print("--- INICIANDO OPTIMIZADOR GENÉTICO ---")
    print("=" * 50 + "\n")

    genetic_optimizer = GeneticOptimizer(
        strategy_config=estrategia_para_optimizar,
        data_file_path=datos_historicos_csv,
        population_size=20,
        generations=5,
        mutation_rate=0.2,
        crossover_rate=0.8
    )

    best_report_ga, best_config_ga = genetic_optimizer.run_optimization()