import os
import subprocess
import msvcrt
from console_ui import ConsoleUI
from orchestrator import HermesOrchestrator
from config import Config
from pathlib import Path

def hermes_folder_exists() -> bool:
    hermes_dir = Path(os.environ["LOCALAPPDATA"]) / "hermes"
    return hermes_dir.is_dir()

def check_hermes():
    try:
        # Ejecuta 'hermes -version' de forma silenciosa
        resultado = subprocess.run(
            ["hermes", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Si el código de salida es 0, es que respondió correctamente
        return resultado.returncode == 0

    except FileNotFoundError:
        # Si Windows dice que el comando no existe en el PATH, devuelve False
        return False

def uninstall_hermes():
    """Ejecuta los comandos de desinstalación solicitados en orden"""
    ConsoleUI.log_step("Desinstalando Hermes...")    
    orchestrator = HermesOrchestrator()
    ConsoleUI.log_step("Ejecutando hermes uninstall...")
    subprocess.run(["hermes", "uninstall"], shell=True)    
    
    ConsoleUI.log_success("Desinstalación de Hermes completada... Vuelva a ejecutar .\htg1 para re-instalar Hermes.")
    if ConsoleUI.prompt_yn("¿Desea borrar la carpeta de instalación de Hermes?"):
        if hermes_folder_exists():
            ConsoleUI.log_step("Borrando carpeta de instalación de Hermes...")
            subprocess.run(["rmdir", "/s", "/q", os.path.expandvars("%LOCALAPPDATA%\\hermes")], shell=True)
        else:
            ConsoleUI.log_warning("No se encontró la ningunacarpeta de instalación de Hermes para borrar.")


def run_fresh_install_flow():
    """Ejecuta el flujo de instalación seguido de configuración"""
    orchestrator = HermesOrchestrator()
    if ConsoleUI.prompt_yn("¿Desea instalar Hermes?"):
        ConsoleUI.log_step("Iniciando proceso de instalación limpia...")
        if not orchestrator.run_installation_steps():
            ConsoleUI.log_error("Falló el flujo de instalación separada")
            return True
    
    ConsoleUI.log_success("Instalación completa!... Vuelva a ejecutar .\htg1 para levantar los servicios de Hermes.")    
    return False

def main():
    ConsoleUI.print_logo()
    try:
        if not check_hermes():
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
                
                if ConsoleUI.prompt_yn("¿Desea reconfigurar Hermes?"):
                    ConsoleUI.log_step("Ejecutando reconfiguración en terminal separada...")
                    subprocess.run(f'start /wait hermes setup', shell=True)
                    ConsoleUI.log_step("Reconfiguración terminada con éxito!")
                else:                    
                    ConsoleUI.log_step("Continuando Orquestación...")

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