import os
import subprocess
import msvcrt
from console_ui import ConsoleUI
from orchestrator import HermesOrchestrator

def check_hermes_version():
    """Verifica si Hermes está instalado ejecutando 'hermes --version'"""
    try:
        result = subprocess.run(
            ["hermes", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def uninstall_hermes():
    """Ejecuta los comandos de desinstalación solicitados en orden"""
    ConsoleUI.log_step("Desinstalando Hermes...")
    
    ConsoleUI.log_step("Ejecutando hermes uninstall...")
    subprocess.run(["hermes", "uninstall"], shell=True)
    
    ConsoleUI.log_step("Deteniendo procesos de Python...")
    subprocess.Popen([
        "powershell", "-Command",
        "Stop-Process -Name \"python\" -Force -ErrorAction SilentlyContinue"
    ], shell=True)
    
    ConsoleUI.log_step("Eliminando directorio de Hermes...")
    subprocess.Popen([
        "powershell", "-Command",
        "Remove-Item -Path \"$env:LOCALAPPDATA\\hermes\" -Recurse -Force"
    ], shell=True)
    
    ConsoleUI.log_success("Desinstalación de Hermes completada... Vuelva a ejecutar .\htg1 para re-instalar Hermes.")

def run_fresh_install_flow():
    """Ejecuta el flujo de instalación seguido de configuración"""
    orchestrator = HermesOrchestrator()
    if ConsoleUI.prompt_yn("¿Desea instalar Hermes?"):
        ConsoleUI.log_step("Iniciando proceso de instalación limpia...")
        if not orchestrator.run_installation_steps():
            ConsoleUI.log_error("Falló el flujo de instalación separada")
            return True
    
    ConsoleUI.log_success("Proceso de instalación terminado!... Vuelva a ejecutar .\htg1 para levantar los servicios de Hermes.")    
    return False

def main():
    ConsoleUI.print_logo()
    try:
        if not check_hermes_version():
            ConsoleUI.log_step("No se detectó instalación previa de Hermes")
            hubo_error = run_fresh_install_flow()
        else:
            ConsoleUI.log_step("Se detectó instalación previa de Hermes")
            if ConsoleUI.prompt_yn("¿Desea desinstalar Hermes?"):
                uninstall_hermes()
                hubo_error = False
            else:
                if ConsoleUI.prompt_yn("¿Desea actualizar Hermes?"):
                    orchestrator = HermesOrchestrator()
                    ConsoleUI.log_step("Ejecutando actualización en terminal separada...")
                    if not orchestrator.run_update_terminal():
                        ConsoleUI.log_error("Falló la actualización de Hermes")
                        hubo_error = True
                    else:
                        ConsoleUI.log_step("Actualización terminada con éxito...")
                        hubo_error = orchestrator.execute()
                else:
                    ConsoleUI.log_step("Omitiendo actualización, continuando con flujo normal...")
                    orchestrator = HermesOrchestrator()
                    hubo_error = orchestrator.execute()

        print()
        if hubo_error:
            ConsoleUI.log_error("Pipeline finalizado con advertencias estructurales.")
        else:
            ConsoleUI.log_success("¡Pipeline ejecutado con éxito!")

    except Exception as e:
        ConsoleUI.log_error(f"\nSe interrumpió el flujo debido a una excepción crítica: {e}")
    finally:
        print("\n" + "-" * 53)
        print("Ya puedes cerrar la ventana! o presiona [Enter] 2 veces para salir...", end="", flush=True)
        msvcrt.getch()
        os._exit(0)

if __name__ == "__main__":
    main()