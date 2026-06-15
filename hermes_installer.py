import subprocess
import os
import shutil
from console_ui import ConsoleUI

class HermesInstaller:
    def __init__(self, user_profile):
        self.user_profile = user_profile

    def install_agent_only(self):
        """Instala solo el agente de Hermes (sin setup ni clonación de webui)"""
        ConsoleUI.log_step("Instalando solo el agente de Hermes...")
        cmd_install = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command "'
            'Write-Host \\"Iniciando descarga e instalacion de Hermes-Agent\\" -ForegroundColor Cyan; '
            'iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1); '
            'Write-Host \\"Actualizando variables de entorno de la sesion\\" -ForegroundColor Cyan; '
            '$env:Path = [Environment]::GetEnvironmentVariable(\\"Path\\", \\"User\\\") + \\";\\\" + [Environment]::GetEnvironmentVariable(\\"Path\\", \\"Machine\\\"); '
            'Write-Host \\"Instalacion de Hermes-Agent completada\\" -ForegroundColor Green;'
            '"'
        )
        try:
            subprocess.run(f'start /wait {cmd_install}', shell=True, cwd=self.user_profile)
            ConsoleUI.log_success("Instalación de Hermes-Agent completada.")
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error al instalar Hermes-Agent: {e}")
            return False

    def setup_dashboard(self, port):
        """Configura hermes dashboard en un proceso separado (sin --skip-build)"""
        ConsoleUI.log_step(f"Configurando dashboard en puerto {port}...")
        try:
            subprocess.Popen(f'hermes dashboard --host 0.0.0.0 --port {port} --insecure --no-open', shell=True, cwd=self.user_profile)
            ConsoleUI.log_success("Configurando Dashboard.")
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error ejecutando dashboard setup: {e}")
            return False

    def clone_webui(self):
        """Clona hermes-webui (mantenido para compatibilidad)"""
        hermes_dir = os.path.join(self.user_profile, r"AppData\Local\hermes")
        if not os.path.exists(hermes_dir):
            ConsoleUI.log_error(f"El directorio de instalación de Hermes no existe en: {hermes_dir}")
            raise FileNotFoundError(f"Directorio de instalación obligatorio no encontrado: {hermes_dir}")

        webui_dir = os.path.join(hermes_dir, "hermes-webui")
        if os.path.exists(webui_dir):
            ConsoleUI.log_step("Detectada instalación previa de hermes-webui. Limpiando para instalación limpia...")
            try:
                shutil.rmtree(webui_dir)
                ConsoleUI.log_success("Instalación previa de hermes-webui removida con éxito.")
            except Exception as e:
                ConsoleUI.log_error(f"No se pudo eliminar la carpeta hermes-webui: {e}. Se intentará clonar de todos modos.")

        ConsoleUI.log_step("Clonando hermes-webui en una nueva ventana de terminal...")
        cmd_clone = (
            'powershell -NoProfile -ExecutionPolicy Bypass -Command "'
            'Write-Host \\"Iniciando clonado de hermes-webui\\" -ForegroundColor Cyan; '
            '$env:Path = [Environment]::GetEnvironmentVariable(\\"Path\\", \\"User\\\") + \\";\\\" + [Environment]::GetEnvironmentVariable(\\"Path\\", \\"Machine\\\"); '
            'git clone https://github.com/nesquena/hermes-webui.git hermes-webui; '
            'Write-Host \\"Clonado finalizado. Esta ventana se cerrara en 3 segundos...\\" -ForegroundColor Green; '
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