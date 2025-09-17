# gestion_riesgo.py
# Gestión de riesgo global y por estrategia
import csv
from datetime import datetime, timedelta

class GestionRiesgo:
    def __init__(self, limite_global=None, limites_estrategias=None, modo_porcentaje=False, capital_inicial=10000,
                 cooldown_activo=False, cooldown_minutos=60,
                 reducir_posicion_activo=False, perdidas_consecutivas_reduccion=3, factor_reduccion=0.5,
                 limite_perdidas_consecutivas_activo=False, limite_perdidas_consecutivas=3):
        """
        limite_global: float (valor absoluto o porcentaje)
        limites_estrategias: dict {nombre_estrategia: limite}
        modo_porcentaje: bool (True si los límites son porcentajes)
        capital_inicial: float (para cálculo de porcentajes)
        """
        self.limite_global = limite_global
        self.limites_estrategias = limites_estrategias or {}
        self.modo_porcentaje = modo_porcentaje
        self.capital_inicial = capital_inicial
        self.cooldown_activo = cooldown_activo
        self.cooldown_minutos = cooldown_minutos
        self.reducir_posicion_activo = reducir_posicion_activo
        self.perdidas_consecutivas_reduccion = perdidas_consecutivas_reduccion
        self.factor_reduccion = factor_reduccion
        self.limite_perdidas_consecutivas_activo = limite_perdidas_consecutivas_activo
        self.limite_perdidas_consecutivas = limite_perdidas_consecutivas

        # Estados dinámicos
        self.perdida_global = 0.0
        self.perdidas_estrategias = {est: 0.0 for est in self.limites_estrategias}
        self.cooldowns = {}
        self.fecha_actual = datetime.now().date()
        self.perdidas_consecutivas = {est: 0 for est in self.limites_estrategias}
    
    def cargar_desde_csv(self, ruta_csv):
        """
        Carga el historial de operaciones desde el CSV para recalcular los límites.
        """
        try:
            with open(ruta_csv, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fecha_cierre = datetime.strptime(row['fecha_cierre'], '%Y-%m-%d %H:%M:%S').date()
                    # Si la fecha es de hoy, registra la operación
                    if fecha_cierre == self.fecha_actual:
                        estrategia = row['estrategia']
                        resultado_dinero = float(row['resultado_dinero'])
                        self.registrar_operacion(estrategia, resultado_dinero, cargar=True)
        except FileNotFoundError:
            print(f"Advertencia: El archivo CSV '{ruta_csv}' no se encontró. Iniciando sin historial.")
        except Exception as e:
            print(f"Error al cargar el CSV: {e}")

    def registrar_operacion(self, nombre_estrategia, resultado, cargar=False):
        """
        Registra el resultado de una operación y actualiza los límites de riesgo.
        """
        fecha_operacion = datetime.now().date()
        if not cargar and fecha_operacion != self.fecha_actual:
            self.reiniciar_limites()
            self.fecha_actual = fecha_operacion

        # Actualiza las pérdidas globales
        self.perdida_global += resultado

        # Actualiza las pérdidas por estrategia
        if nombre_estrategia in self.limites_estrategias:
            self.perdidas_estrategias[nombre_estrategia] = self.perdidas_estrategias.get(nombre_estrategia, 0) + resultado
            
            # Gestión de pérdidas consecutivas
            if resultado < 0:
                self.perdidas_consecutivas[nombre_estrategia] = self.perdidas_consecutivas.get(nombre_estrategia, 0) + 1
                if self.limite_perdidas_consecutivas_activo and self.perdidas_consecutivas[nombre_estrategia] >= self.limite_perdidas_consecutivas:
                    self.cooldowns[nombre_estrategia] = datetime.now() + timedelta(minutes=self.cooldown_minutos)
                    print(f"⚠️ La estrategia '{nombre_estrategia}' ha alcanzado el límite de pérdidas consecutivas. Entra en cooldown.")
            else:
                self.perdidas_consecutivas[nombre_estrategia] = 0

    def reiniciar_limites(self):
        """Reinicia los límites de pérdidas para el nuevo día."""
        self.perdida_global = 0.0
        self.perdidas_estrategias = {est: 0.0 for est in self.limites_estrategias}
        self.perdidas_consecutivas = {est: 0 for est in self.limites_estrategias}
        # Los cooldowns se mantienen hasta que expiren
        
    def puede_operar(self, nombre_estrategia=None):
        """
        Verifica si se puede abrir una nueva operación.
        Si nombre_estrategia es None, verifica el límite global.
        """
        # Cooldown
        if self.cooldown_activo and nombre_estrategia in self.cooldowns and self.cooldowns[nombre_estrategia] > datetime.now():
            return False
            
        # Límite global
        if self.limite_global:
            limite = self.limite_global
            if self.modo_porcentaje:
                limite = self.capital_inicial * self.limite_global
            if self.perdida_global <= -abs(limite): # Si la pérdida es mayor que el límite
                return False

        # Por estrategia
        if nombre_estrategia in self.limites_estrategias:
            limite = self.limites_estrategias[nombre_estrategia]
            if self.modo_porcentaje:
                limite = self.capital_inicial * limite / 100
            if self.perdidas_estrategias.get(nombre_estrategia, 0) <= -abs(limite):
                return False
        
        return True

    def factor_posicion(self, nombre_estrategia):
        """Devuelve el factor de reducción de posición para la estrategia (1.0 = normal, <1.0 = reducir)"""
        if self.reducir_posicion_activo:
            if self.perdidas_consecutivas.get(nombre_estrategia, 0) >= self.perdidas_consecutivas_reduccion:
                return self.factor_reduccion
        return 1.0

    def resumen(self):
        return {
            'perdida_global': self.perdida_global,
            'perdidas_estrategias': self.perdidas_estrategias.copy(),
            'fecha': str(self.fecha_actual),
            'cooldowns': {k: str(v) for k, v in self.cooldowns.items() if v > datetime.now()},
            'perdidas_consecutivas': self.perdidas_consecutivas
        }

# Ejemplo de uso:
# riesgo = GestionRiesgo(limite_global=500, limites_estrategias={'estrategia1': 200, 'estrategia2': 150}, modo_porcentaje=False)
# riesgo.registrar_operacion('estrategia1', -50)
# riesgo.puede_operar('estrategia1')
# riesgo.resumen()
