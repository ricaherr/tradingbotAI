#!/usr/bin/env python3
"""
Ejecuta optimización con monitoreo en tiempo real.
"""

import subprocess
import threading
import time
import os
import sys

def run_optimization():
    """Ejecuta la optimización en un proceso separado."""
    cmd = [sys.executable, "run_optimization_enhanced.py", "--population", "50", "--generations", "20"]
    
    print("[INICIANDO] Optimización genética...")
    print(f"[COMANDO] {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Leer salida en tiempo real
    for line in process.stdout:
        print(f"[OPT] {line.rstrip()}")
    
    process.wait()
    print(f"\n[TERMINADO] Código de salida: {process.returncode}")

def monitor_progress():
    """Monitorea el progreso de la optimización."""
    start_time = time.time()
    
    while True:
        try:
            # Verificar procesos activos
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True, text=True, shell=True
            )
            
            active_count = result.stdout.count('python.exe')
            elapsed = time.time() - start_time
            
            # Verificar archivos de resultados
            files_status = []
            for file in ['convergence_plot.png', 'optimization_results.json']:
                if os.path.exists(file):
                    mtime = os.path.getmtime(file)
                    age = time.time() - mtime
                    files_status.append(f"{file}({age/60:.1f}m)")
            
            status = f"[{elapsed/60:.1f}m] Procesos: {active_count}"
            if files_status:
                status += f" | Archivos: {', '.join(files_status)}"
            
            print(f"\r{status}", end="", flush=True)
            
            time.sleep(15)  # Actualizar cada 15 segundos
            
        except KeyboardInterrupt:
            break
        except:
            time.sleep(15)

def main():
    print("=== OPTIMIZACIÓN CON MONITOREO ===\n")
    
    # Iniciar optimización en hilo separado
    opt_thread = threading.Thread(target=run_optimization, daemon=True)
    opt_thread.start()
    
    # Esperar un poco antes de iniciar monitoreo
    time.sleep(3)
    
    try:
        # Iniciar monitoreo
        monitor_progress()
    except KeyboardInterrupt:
        print("\n\n[INFO] Monitoreo detenido por el usuario")
    
    # Esperar a que termine la optimización
    opt_thread.join()
    print("\n[COMPLETADO] Proceso finalizado")

if __name__ == "__main__":
    main()