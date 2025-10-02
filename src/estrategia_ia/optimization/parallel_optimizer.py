"""
ParallelOptimizer - Optimizador genético con paralelización
Mejora significativa de performance para FASE 3
"""

import multiprocessing as mp
import numpy as np
import time
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from ..config import OPTIMIZER_SETTINGS
from .fitness_worker import fitness_worker


class ParallelOptimizer:
    """Optimizador genético paralelo para mejor performance"""
    
    def __init__(self, data_file_path: str, strategy_config: Dict, 
                 population_size: Optional[int] = None, 
                 generations: Optional[int] = None,
                 cpu_usage: Optional[float] = None):
        
        self.data_file_path = data_file_path
        self.strategy_config = strategy_config
        
        # Configuración del optimizador
        self.population_size = population_size or OPTIMIZER_SETTINGS["population_size"]
        self.generations = generations or OPTIMIZER_SETTINGS["generations"]
        self.mutation_rate = OPTIMIZER_SETTINGS["mutation_rate"]
        self.crossover_rate = OPTIMIZER_SETTINGS["crossover_rate"]
        self.tournament_size = OPTIMIZER_SETTINGS["tournament_size"]
        
        # Configuración de paralelización
        cpu_usage = cpu_usage or OPTIMIZER_SETTINGS["cpu_core_usage"]
        max_workers = max(1, int(mp.cpu_count() * cpu_usage))
        self.max_workers = min(max_workers, self.population_size)
        
        # Extraer parámetros optimizables
        self.optimizable_params = strategy_config.get("optimizable_params", {})
        if not self.optimizable_params:
            raise ValueError("No hay parámetros optimizables definidos")
        
        # Estadísticas
        self.stats = {
            "generation_times": [],
            "best_fitness_history": [],
            "avg_fitness_history": [],
            "total_evaluations": 0
        }
    
    def create_individual(self) -> Dict:
        """Crea un individuo aleatorio"""
        individual = {}
        for param, config in self.optimizable_params.items():
            min_val = config["min"]
            max_val = config["max"]
            step = config.get("step", 0.01)
            
            # Generar valor aleatorio respetando el step
            if step > 0:
                num_steps = int((max_val - min_val) / step)
                random_step = np.random.randint(0, num_steps + 1)
                value = min_val + (random_step * step)
            else:
                value = np.random.uniform(min_val, max_val)
            
            individual[param] = value
        
        return individual
    
    def create_population(self) -> List[Dict]:
        """Crea población inicial"""
        return [self.create_individual() for _ in range(self.population_size)]
    
    def evaluate_population_parallel(self, population: List[Dict]) -> List[float]:
        """Evalúa población en paralelo"""
        start_time = time.time()
        
        # Preparar argumentos para workers
        tasks = []
        for individual in population:
            # Crear configuración completa para el individuo
            individual_config = self.strategy_config.copy()
            individual_config.update(individual)
            
            tasks.append((self.data_file_path, individual_config))
        
        # Ejecutar en paralelo
        fitness_scores = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_individual = {
                executor.submit(fitness_worker, task[0], task[1]): i 
                for i, task in enumerate(tasks)
            }
            
            # Recoger resultados manteniendo el orden
            results = [None] * len(population)
            for future in as_completed(future_to_individual):
                index = future_to_individual[future]
                try:
                    fitness = future.result()
                    results[index] = fitness
                except Exception as e:
                    print(f"[WARNING] Error evaluando individuo {index}: {e}")
                    results[index] = -1000  # Penalizar individuos con errores
        
        # Filtrar None values (por si acaso)
        fitness_scores = [score if score is not None else -1000 for score in results]
        
        eval_time = time.time() - start_time
        self.stats["generation_times"].append(eval_time)
        self.stats["total_evaluations"] += len(population)
        
        return fitness_scores
    
    def tournament_selection(self, population: List[Dict], fitness_scores: List[float]) -> Dict:
        """Selección por torneo"""
        tournament_indices = np.random.choice(
            len(population), 
            size=self.tournament_size, 
            replace=False
        )
        
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[np.argmax(tournament_fitness)]
        
        return population[winner_index].copy()
    
    def crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """Cruzamiento uniforme"""
        child1, child2 = parent1.copy(), parent2.copy()
        
        for param in self.optimizable_params:
            if np.random.random() < 0.5:
                child1[param], child2[param] = child2[param], child1[param]
        
        return child1, child2
    
    def mutate(self, individual: Dict) -> Dict:
        """Mutación gaussiana"""
        mutated = individual.copy()
        
        for param, config in self.optimizable_params.items():
            if np.random.random() < self.mutation_rate:
                min_val = config["min"]
                max_val = config["max"]
                step = config.get("step", 0.01)
                
                # Mutación gaussiana con 10% del rango como desviación
                std_dev = (max_val - min_val) * 0.1
                mutation = np.random.normal(0, std_dev)
                new_value = individual[param] + mutation
                
                # Aplicar límites
                new_value = max(min_val, min(max_val, new_value))
                
                # Ajustar al step si está definido
                if step > 0:
                    new_value = min_val + round((new_value - min_val) / step) * step
                
                mutated[param] = new_value
        
        return mutated
    
    def optimize(self, verbose: bool = True) -> Dict:
        """Ejecuta optimización genética paralela"""
        if verbose:
            print(f"[INFO] Iniciando optimización paralela")
            print(f"[INFO] Población: {self.population_size}, Generaciones: {self.generations}")
            print(f"[INFO] Workers: {self.max_workers}/{mp.cpu_count()}")
            print(f"[INFO] Parámetros: {list(self.optimizable_params.keys())}")
        
        start_time = time.time()
        
        # Crear población inicial
        population = self.create_population()
        
        best_individual = None
        best_fitness = float('-inf')
        
        for generation in range(self.generations):
            gen_start = time.time()
            
            # Evaluar población en paralelo
            fitness_scores = self.evaluate_population_parallel(population)
            
            # Estadísticas de la generación
            max_fitness = max(fitness_scores)
            avg_fitness = np.mean(fitness_scores)
            
            self.stats["best_fitness_history"].append(max_fitness)
            self.stats["avg_fitness_history"].append(avg_fitness)
            
            # Actualizar mejor individuo
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_index = fitness_scores.index(max_fitness)
                best_individual = population[best_index].copy()
            
            if verbose:
                gen_time = time.time() - gen_start
                print(f"[GEN {generation+1:2d}] Best: {max_fitness:8.4f} | "
                      f"Avg: {avg_fitness:8.4f} | Time: {gen_time:5.2f}s")
            
            # Crear nueva generación (excepto la última)
            if generation < self.generations - 1:
                new_population = []
                
                # Elitismo: mantener mejor individuo
                new_population.append(best_individual.copy())
                
                # Generar resto de la población
                while len(new_population) < self.population_size:
                    # Selección
                    parent1 = self.tournament_selection(population, fitness_scores)
                    parent2 = self.tournament_selection(population, fitness_scores)
                    
                    # Cruzamiento
                    if np.random.random() < self.crossover_rate:
                        child1, child2 = self.crossover(parent1, parent2)
                    else:
                        child1, child2 = parent1.copy(), parent2.copy()
                    
                    # Mutación
                    child1 = self.mutate(child1)
                    child2 = self.mutate(child2)
                    
                    new_population.extend([child1, child2])
                
                # Ajustar tamaño si es necesario
                population = new_population[:self.population_size]
        
        total_time = time.time() - start_time
        
        if verbose:
            print(f"\n[COMPLETED] Optimización finalizada en {total_time:.2f}s")
            print(f"[RESULT] Mejor fitness: {best_fitness:.4f}")
            print(f"[STATS] Evaluaciones totales: {self.stats['total_evaluations']}")
            print(f"[STATS] Evaluaciones/segundo: {self.stats['total_evaluations']/total_time:.1f}")
        
        # Crear configuración final
        final_config = self.strategy_config.copy()
        final_config.update(best_individual)
        
        return {
            "best_individual": best_individual,
            "best_fitness": best_fitness,
            "best_config": final_config,
            "optimization_stats": self.stats,
            "total_time": total_time,
            "evaluations_per_second": self.stats['total_evaluations'] / total_time
        }