# strategies.py

def determinar_senales(df, estrategia):
    """
    Identifica señales de compra/venta.
    Ahora devuelve una tupla (señal, razón) para un logging más detallado.
    """
    ultima_vela = df.iloc[-1]
    
    if len(df) < 2:
        return None, "Datos insuficientes (menos de 2 velas)"

    nombre_estrategia = estrategia.get("nombre")

    # Lógica para la estrategia 'Cruce EMA + Vela Elefante'
    if nombre_estrategia == "Cruce EMA + Vela Elefante":
        # CORRECTO: Leer parámetros desde el diccionario principal de la estrategia
        ema_corta_periodo = estrategia.get("ema_corta", 9)
        ema_larga_periodo = estrategia.get("ema_larga", 20)

        col_ema_corta = f'EMA_{ema_corta_periodo}'
        col_ema_larga = f'EMA_{ema_larga_periodo}'

        if not all(k in df.columns for k in [col_ema_corta, col_ema_larga, 'es_vela_elefante']):
            return None, f"Faltan columnas de indicadores ({col_ema_corta}, {col_ema_larga}, es_vela_elefante)"

        cruce_alcista = df[col_ema_corta].iloc[-2] < df[col_ema_larga].iloc[-2] and df[col_ema_corta].iloc[-1] > df[col_ema_larga].iloc[-1]
        cruce_bajista = df[col_ema_corta].iloc[-2] > df[col_ema_larga].iloc[-2] and df[col_ema_corta].iloc[-1] < df[col_ema_larga].iloc[-1]
        es_elefante = ultima_vela['es_vela_elefante']
        
        # Lógica de la estrategia original
        if cruce_alcista and es_elefante:
            return "compra", f"Cruce alcista de EMAs ({ema_corta_periodo}/{ema_larga_periodo}) con vela elefante"
        elif cruce_bajista and es_elefante:
            return "venta", f"Cruce bajista de EMAs ({ema_corta_periodo}/{ema_larga_periodo}) con vela elefante"
        else:
            razon = f"No hubo cruce o no fue vela elefante. Elefante: {es_elefante}"
            return None, razon

    # Lógica para la estrategia 'Rompimiento de la EMA 20'
    elif nombre_estrategia == "Rompimiento de la EMA 20":
        if not all(k in df.columns for k in ['EMA_20', 'es_vela_elefante']):
            return None, "Faltan columnas de indicadores (EMA_20, es_vela_elefante)"
        
        es_elefante = ultima_vela['es_vela_elefante']
        
        if es_elefante:
            rompimiento_alcista = df['close'].iloc[-2] < df['EMA_20'].iloc[-2] and ultima_vela['close'] > ultima_vela['EMA_20']
            if rompimiento_alcista:
                return "compra", "Rompimiento alcista de EMA_20 con vela elefante"

            rompimiento_bajista = df['close'].iloc[-2] > df['EMA_20'].iloc[-2] and ultima_vela['close'] < ultima_vela['EMA_20']
            if rompimiento_bajista:
                return "venta", "Rompimiento bajista de EMA_20 con vela elefante"
        else:
            return None, "No fue vela elefante"
    
    # Lógica para la estrategia 'Reversión a la Media'
    elif nombre_estrategia == "Reversión a la Media":
        # Leer parámetros dinámicamente desde la configuración de la estrategia
        ema_reversion_periodo = estrategia.get("ema_reversion", 20)
        col_ema_reversion = f'EMA_{ema_reversion_periodo}'

        if col_ema_reversion not in df.columns:
            return None, f"Falta columna de indicador ({col_ema_reversion})"
        
        # Filtro de tendencia opcional
        precio_sobre_ema_tendencia = True
        precio_bajo_ema_tendencia = True
        if estrategia.get("usar_filtro_tendencia", False):
            ema_tendencia_periodo = estrategia.get("ema_tendencia", 200)
            col_ema_tendencia = f'EMA_{ema_tendencia_periodo}'
            if col_ema_tendencia not in df.columns:
                return None, f"Falta columna de indicador de tendencia ({col_ema_tendencia})"
            
            precio_sobre_ema_tendencia = ultima_vela['close'] > ultima_vela[col_ema_tendencia]
            precio_bajo_ema_tendencia = ultima_vela['close'] < ultima_vela[col_ema_tendencia]
        
        # Lógica de cruce
        cruce_alcista = df['close'].iloc[-2] < df[col_ema_reversion].iloc[-2] and ultima_vela['close'] > ultima_vela[col_ema_reversion]
        if cruce_alcista and precio_sobre_ema_tendencia:
            return "compra", f"Reversión alcista a {col_ema_reversion}"

        cruce_bajista = df['close'].iloc[-2] > df[col_ema_reversion].iloc[-2] and ultima_vela['close'] < ultima_vela[col_ema_reversion]
        if cruce_bajista and precio_bajo_ema_tendencia:
            return "venta", f"Reversión bajista a {col_ema_reversion}"
        
        return None, "No hubo cruce o el filtro de tendencia no se cumplió"

    return None, "Estrategia no reconocida"