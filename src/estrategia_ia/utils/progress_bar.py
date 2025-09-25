import sys
import time
from datetime import datetime, timedelta

class ProgressBar:
    """Barra de progreso simple para operaciones largas."""
    
    def __init__(self, total, description="Progreso", width=50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
        
    def update(self, increment=1, status=""):
        """Actualiza la barra de progreso."""
        self.current += increment
        self._render(status)
        
    def set_progress(self, current, status=""):
        """Establece el progreso actual directamente."""
        self.current = current
        self._render(status)
        
    def _render(self, status=""):
        """Renderiza la barra de progreso."""
        if self.total == 0:
            return
            
        percent = min(100, (self.current / self.total) * 100)
        filled = int(self.width * self.current // self.total)
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calcular tiempo estimado
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta_seconds = (elapsed / self.current) * (self.total - self.current)
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = "calculando..."
            
        # Formatear línea de progreso
        line = f"\r{self.description}: |{bar}| {percent:5.1f}% ({self.current}/{self.total}) ETA: {eta}"
        if status:
            line += f" - {status}"
            
        sys.stdout.write(line)
        sys.stdout.flush()
        
        if self.current >= self.total:
            print()  # Nueva línea al completar
            
    def finish(self, message="Completado"):
        """Finaliza la barra de progreso."""
        self.current = self.total
        self._render(message)

class OptimizationProgress:
    """Progreso específico para optimización genética."""
    
    def __init__(self, total_generations, population_size):
        self.total_generations = total_generations
        self.population_size = population_size
        self.current_generation = 0
        self.current_individual = 0
        self.best_fitness = None
        self.start_time = time.time()
        
    def start_generation(self, generation):
        """Inicia una nueva generación."""
        self.current_generation = generation
        self.current_individual = 0
        
    def update_individual(self, fitness=None):
        """Actualiza el progreso de evaluación individual."""
        self.current_individual += 1
        if fitness is not None and (self.best_fitness is None or fitness > self.best_fitness):
            self.best_fitness = fitness
        self._render()
        
    def _render(self):
        """Renderiza el progreso de optimización."""
        # Progreso de generación
        gen_percent = (self.current_generation / self.total_generations) * 100
        
        # Progreso dentro de la generación actual
        ind_percent = (self.current_individual / self.population_size) * 100
        
        # Tiempo transcurrido
        elapsed = time.time() - self.start_time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        
        # Mejor fitness
        fitness_str = f"{self.best_fitness:.4f}" if self.best_fitness else "N/A"
        
        # Línea de progreso
        line = (f"\rGen {self.current_generation}/{self.total_generations} "
                f"({gen_percent:5.1f}%) | "
                f"Ind {self.current_individual}/{self.population_size} "
                f"({ind_percent:5.1f}%) | "
                f"Mejor: {fitness_str} | "
                f"Tiempo: {elapsed_str}")
                
        sys.stdout.write(line)
        sys.stdout.flush()
        
    def finish(self):
        """Finaliza el progreso de optimización."""
        print("\n[OK] Optimización completada")