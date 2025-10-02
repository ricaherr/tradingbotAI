# strategies.py

def determinar_senales(df, estrategia):
    """
    Identifica señales de compra/venta.
    VERSIÓN CORREGIDA - Funciona sin dependencias de columnas faltantes.
    """
    if len(df) < 2:
        return None, "Datos insuficientes (menos de 2 velas)"

    ultima_vela = df.iloc[-1]
    penultima_vela = df.iloc[-2]
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

    # Estrategia simplificada para "Rompimiento de la EMA 20"
    if nombre_estrategia == "Rompimiento de la EMA 20":
        # Usar EMA_20 si existe, sino calcular sobre la marcha
        if 'EMA_20' in df.columns:
            ema_20_actual = ultima_vela['EMA_20']
            ema_20_anterior = penultima_vela['EMA_20']
        else:
            # Calcular EMA simple si no existe
            ema_20_actual = df['close'].tail(20).mean()
            ema_20_anterior = df['close'].tail(21).iloc[:-1].mean()
        
        precio_actual = ultima_vela['close']
        precio_anterior = penultima_vela['close']
        
        # Rompimiento alcista: precio cruza por encima de EMA
        if precio_anterior <= ema_20_anterior and precio_actual > ema_20_actual:
            return "compra", "Rompimiento alcista de EMA_20"
        
        # Rompimiento bajista: precio cruza por debajo de EMA  
        if precio_anterior >= ema_20_anterior and precio_actual < ema_20_actual:
            return "venta", "Rompimiento bajista de EMA_20"
        
        return None, "No hay rompimiento de EMA_20"
    
    # Estrategia corregida para "Reversión a la Media"
    elif nombre_estrategia == "Reversión a la Media":
        ema_reversion_periodo = estrategia.get("ema_reversion", 20)
        col_ema_reversion = f'EMA_{ema_reversion_periodo}'
        
        # Verificar si existe la columna, sino usar EMA_20 por defecto
        if col_ema_reversion not in df.columns:
            if 'EMA_20' in df.columns:
                col_ema_reversion = 'EMA_20'
            else:
                # Calcular EMA simple
                ema_actual = df['close'].tail(ema_reversion_periodo).mean()
                ema_anterior = df['close'].tail(ema_reversion_periodo + 1).iloc[:-1].mean()
                precio_actual = ultima_vela['close']
                precio_anterior = penultima_vela['close']
                
                # Cruce alcista
                if precio_anterior < ema_anterior and precio_actual > ema_actual:
                    return "compra", f"Reversión alcista a EMA_{ema_reversion_periodo}"
                
                # Cruce bajista  
                if precio_anterior > ema_anterior and precio_actual < ema_actual:
                    return "venta", f"Reversión bajista a EMA_{ema_reversion_periodo}"
                
                return None, "No hay cruce de EMA"
        
        # Usar columna existente
        ema_actual = ultima_vela[col_ema_reversion]
        ema_anterior = penultima_vela[col_ema_reversion]
        precio_actual = ultima_vela['close']
        precio_anterior = penultima_vela['close']
        
        # Filtro de tendencia opcional (simplificado)
        usar_filtro = estrategia.get("usar_filtro_tendencia", False)
        if usar_filtro:
            ema_tendencia_periodo = estrategia.get("ema_tendencia", 200)
            col_ema_tendencia = f'EMA_{ema_tendencia_periodo}'
            
            if col_ema_tendencia in df.columns:
                ema_tendencia = ultima_vela[col_ema_tendencia]
                
                # Solo operar en dirección de la tendencia
                if precio_actual > ema_tendencia:  # Tendencia alcista
                    if precio_anterior < ema_anterior and precio_actual > ema_actual:
                        return "compra", f"Reversión alcista a {col_ema_reversion} (tendencia alcista)"
                elif precio_actual < ema_tendencia:  # Tendencia bajista
                    if precio_anterior > ema_anterior and precio_actual < ema_actual:
                        return "venta", f"Reversión bajista a {col_ema_reversion} (tendencia bajista)"
                
                return None, "Cruce contra tendencia - señal filtrada"
        
        # Sin filtro de tendencia
        if precio_anterior < ema_anterior and precio_actual > ema_actual:
            return "compra", f"Reversión alcista a {col_ema_reversion}"
        
        if precio_anterior > ema_anterior and precio_actual < ema_actual:
            return "venta", f"Reversión bajista a {col_ema_reversion}"
        
        return None, "No hay cruce de EMA"

    return None, "Estrategia no reconocida"