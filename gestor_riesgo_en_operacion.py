# gestor_riesgo_en_operacion.py
# Gestión activa del riesgo durante la operación (stop loss dinámico, break-even, trailing stop, IA)

class GestorRiesgoEnOperacion:
    def __init__(self, modo_trailing=True, break_even_activo=True, atr_factor_trailing=1.0, atr_factor_break_even=0.5, modelo_ia=None):
        """
        modo_trailing: activa el trailing stop
        break_even_activo: mueve el stop al punto de entrada tras cierto beneficio
        atr_factor_trailing: multiplicador del ATR para el trailing stop
        atr_factor_break_even: multiplicador del ATR para el umbral de break-even
        modelo_ia: función o modelo que puede sugerir mover el stop o cerrar la operación
        """
        self.modo_trailing = modo_trailing
        self.break_even_activo = break_even_activo
        self.atr_factor_trailing = atr_factor_trailing
        self.atr_factor_break_even = atr_factor_break_even
        self.modelo_ia = modelo_ia

    def actualizar_stop(self, precio_entrada, stop_actual, precio_actual, tipo='compra', atr_value=0.0):
        """
        Devuelve el nuevo stop loss sugerido según la lógica activa.
        atr_value: El valor actual del ATR para el par de la operación.
        tipo: 'compra' o 'venta'
        """
        nuevo_stop = stop_actual
        ganancia = (precio_actual - precio_entrada) if tipo == 'compra' else (precio_entrada - precio_actual)
        
        # Calcular los valores dinámicos basados en el ATR
        umbral_break_even = self.atr_factor_break_even * atr_value
        trailing_distancia = self.atr_factor_trailing * atr_value
        
        # Break-even
        if self.break_even_activo and ganancia >= umbral_break_even:
            # Mover el stop al precio de entrada si aún no lo ha alcanzado
            if (tipo == 'compra' and stop_actual < precio_entrada) or (tipo == 'venta' and stop_actual > precio_entrada):
                nuevo_stop = precio_entrada
        
        # Trailing stop
        if self.modo_trailing:
            if tipo == 'compra':
                trailing = precio_actual - trailing_distancia
                if trailing > nuevo_stop:
                    nuevo_stop = trailing
            else:
                trailing = precio_actual + trailing_distancia
                if trailing < nuevo_stop:
                    nuevo_stop = trailing
        
        # Lógica de IA (si está implementada)
        if self.modelo_ia:
            sugerencia = self.modelo_ia(precio_entrada, stop_actual, precio_actual, tipo)
            if sugerencia is not None:
                nuevo_stop = sugerencia
        
        return nuevo_stop

# Ejemplo de uso:
# gestor = GestorRiesgoEnOperacion(modo_trailing=True, trailing_distancia=15, break_even_activo=True, umbral_break_even=8)
# stop = gestor.actualizar_stop(precio_entrada=100, stop_actual=95, precio_actual=112, tipo='compra')
# print(stop)
