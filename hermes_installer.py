import subprocess
import os
from console_ui import ConsoleUI


class HermesInstaller:
    def __init__(self, user_profile):
        self.user_profile = user_profile

    def run_clean_install(self):
        ConsoleUI.log_step("Iniciando la instalación limpia de Hermes-Agent...")

        cmd_install = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command "'
            'Write-Host \"Iniciando descarga e instalacion de Hermes-Agent...\" -ForegroundColor Cyan; '
            'iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1); '
            'Write-Host \"Actualizando variables de entorno de la sesion...\" -ForegroundColor Cyan; '
            '$env:Path = [Environment]::GetEnvironmentVariable(\"Path\", \"User\") + \";\" + [Environment]::GetEnvironmentVariable(\"Path\", \"Machine\"); '
            'Write-Host \"Ejecutando hermes setup...\" -ForegroundColor Cyan; '
            'hermes setup; '
            'Write-Host \"Proceso de instalacion finalizado. Esta ventana se cerrara en 3 segundos...\" -ForegroundColor Green; '
            'Start-Sleep -Seconds 3'
            '"'
        )
        try:
            subprocess.run(f'start /wait {cmd_install}', shell=True, cwd=self.user_profile)
            ConsoleUI.log_success("Instalación de Hermes-Agent y hermes setup completados.")
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error al ejecutar la instalación de Hermes-Agent: {e}")
            return False

    def clone_webui(self):
        hermes_dir = os.path.join(self.user_profile, r"AppData\Local\hermes")
        if not os.path.exists(hermes_dir):
            ConsoleUI.log_error(f"El directorio de instalación de Hermes no existe en: {hermes_dir}")
            raise FileNotFoundError(f"Directorio de instalación obligatorio no encontrado: {hermes_dir}")

        webui_dir = os.path.join(hermes_dir, "hermes-webui")
        if os.path.exists(webui_dir):
            ConsoleUI.log_step("Detectada instalación previa de hermes-webui. Limpiando para instalación limpia...")
            import shutil
            try:
                shutil.rmtree(webui_dir)
                ConsoleUI.log_success("Instalación previa de hermes-webui removida con éxito.")
            except Exception as e:
                ConsoleUI.log_error(f"No se pudo eliminar la carpeta hermes-webui: {e}. Se intentará clonar de todos modos.")

        ConsoleUI.log_step("Clonando hermes-webui en una nueva ventana de terminal...")
        cmd_clone = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command "'
            'Write-Host \"Iniciando clonado de hermes-webui...\" -ForegroundColor Cyan; '
            '$env:Path = [Environment]::GetEnvironmentVariable(\"Path\", \"User\") + \";\" + [Environment]::GetEnvironmentVariable(\"Path\", \"Machine\"); '
            'git clone https://github.com/nesquena/hermes-webui.git hermes-webui; '
            'Write-Host \"Clonado finalizado. Esta ventana se cerrara en 3 segundos...\" -ForegroundColor Green; '
            'Start-Sleep -Seconds 3'
            '"'
        )
        try:
            subprocess.run(f'start /wait {cmd_clone}', shell=True, cwd=hermes_dir)
            ConsoleUI.log_success("Clonado de hermes-webui completado.")
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error al clonar hermes-webui: {e}")
            return False
