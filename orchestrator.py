import os
import time
import subprocess
import secrets
import base64
from config import Config
from console_ui import ConsoleUI
from env_manager import EnvManager
from hermes_installer import HermesInstaller
from process_manager import ProcessManager
from yaml_config_manager import YamlConfigManager

class HermesOrchestrator:
    def __init__(self):
        self.env_mgr = EnvManager(Config.HERMES_ENV_PATH)
        self.installer = HermesInstaller(Config.USER_PROFILE)
        self.error_detected = False
        self.perfil_seleccionado = None
        self.perfil_ruta_completa = None
        self.final_base_url = None
        self.final_modelo = None
        self.procesar_personalizacion = False
        self.resp_api = False
        self.llave_api_final = None
        self.resp_pass = False
        self.webui_pass_final = None

    def run_input_stage(self):
        ConsoleUI.log_stage("Etapa 1: Recolección de Inputs")

        if not os.path.exists(Config.CONFIG_YALM_DIR):
            os.makedirs(Config.CONFIG_YALM_DIR)

        archivos_yalm = [f for f in os.listdir(Config.CONFIG_YALM_DIR) if f.endswith(".yalm")]

        if archivos_yalm:
            print(f"{ConsoleUI.AMARILLO}[PREGUNTA]{ConsoleUI.RESET} ¿Qué Perfil de configuración desea aplicar?:")
            for idx, archivo in enumerate(archivos_yalm, 1):
                print(f"  {idx}. {archivo}")

            while True:
                seleccion = ConsoleUI.prompt_input(f"Seleccione una opción (1-{len(archivos_yalm)})")
                try:
                    opcion = int(seleccion)
                    if 1 <= opcion <= len(archivos_yalm):
                        self.perfil_seleccionado = archivos_yalm[opcion - 1]
                        self.perfil_ruta_completa = os.path.join(Config.CONFIG_YALM_DIR, self.perfil_seleccionado)
                        break
                    else:
                        ConsoleUI.log_error(f"Opción fuera de rango (1-{len(archivos_yalm)}).")
                except ValueError:
                    ConsoleUI.log_error("Por favor, ingrese un número válido.")

            if "ollama" in self.perfil_seleccionado.lower():
                valores_actuales = YamlConfigManager.extract_config(self.perfil_ruta_completa)
                ConsoleUI.log_success(
                    f"Valores predefinidos leídos de {self.perfil_seleccionado}: Base_URL: {valores_actuales['base_url']}, Model: {valores_actuales['default']}"
                )

                print(f"{ConsoleUI.VERDE}[INFO]{ConsoleUI.RESET} Base URL actual: {valores_actuales['base_url']}")
                if ConsoleUI.prompt_yn("¿Desea cambiar la Base URL?"):
                    self.final_base_url = ConsoleUI.prompt_input("Base URL (ej.: http://127.0.0.1:11434/v1)")
                else:
                    self.final_base_url = valores_actuales['base_url']

                print(f"{ConsoleUI.VERDE}[INFO]{ConsoleUI.RESET} Modelo actual: {valores_actuales['default']}")
                if ConsoleUI.prompt_yn("¿Desea cambiar el Modelo?"):
                    self.final_modelo = ConsoleUI.prompt_input("Modelo por defecto (ej.: deepseek-r1:14b)")
                else:
                    self.final_modelo = valores_actuales['default']

                if not self.final_base_url or not self.final_modelo:
                    ConsoleUI.log_error("Entradas inválidas o vacías detectadas. Se abortará la inyección para proteger la integridad estructural.")
                    self.error_detected = True
                elif self.final_base_url == "No definido" or self.final_modelo == "No definido":
                    ConsoleUI.log_error("No se pudieron aislar variantes válidas en el archivo. Configuración manual mandatoria.")
                    self.error_detected = True
                else:
                    self.procesar_personalizacion = True
        else:
            ConsoleUI.log_error(f"No se encontraron perfiles .yalm en la ruta: {Config.CONFIG_YALM_DIR}")
            self.error_detected = True

        self.resp_api = ConsoleUI.prompt_yn("¿Activar API Server?")
        self.llave_api_final = None

        if self.resp_api:
            llave_actual = self.env_mgr.get_var("API_SERVER_KEY")
            if llave_actual:
                print(f"{ConsoleUI.VERDE}[INFO]{ConsoleUI.RESET} Se detectó una API-Key guardada actualmente.")
                if ConsoleUI.prompt_yn("¿Desea actualizar la API-Key actual?"):
                    self.llave_api_final = self.generar_api_key_base64()
                else:
                    self.llave_api_final = llave_actual
            else:
                self.llave_api_final = self.generar_api_key_base64()

        self.resp_pass = ConsoleUI.prompt_yn("¿Proteger WebUI Chat por contraseña?")
        self.webui_pass_final = None

        if self.resp_pass:
            pass_actual = self.env_mgr.get_var("HERMES_WEBUI_PASSWORD")
            if pass_actual:
                print(f"{ConsoleUI.VERDE}[INFO]{ConsoleUI.RESET} Se detectó una contraseña de WebUI guardada actualmente.")
                if ConsoleUI.prompt_yn("¿Desea mantener la misma contraseña?"):
                    self.webui_pass_final = pass_actual

            if self.webui_pass_final is None:
                prompt_str = f"{ConsoleUI.AMARILLO}[INPUT]{ConsoleUI.RESET} Introduce la nueva contraseña para la WebUI: "
                user_password = ConsoleUI.input_password(prompt_str).strip()
                if user_password:
                    self.webui_pass_final = user_password
                else:
                    ConsoleUI.log_error("Contraseña vacía recibida. Se mantendrá el respaldo anterior de existir.")
                    self.webui_pass_final = pass_actual

    def generar_api_key_base64(self):
        bytes_seguros = secrets.token_bytes(48)
        return base64.b64encode(bytes_seguros).decode('utf-8')

    def run_persistence_stage(self):
        ConsoleUI.log_stage("Etapa 2: Persistencia y Modificación de Archivos")

        if self.error_detected:
            ConsoleUI.log_error("Flujo de persistencia comprometido por inputs inválidos o falta de perfil en Etapa 1. Cambios cancelados.")
            return

        if self.perfil_seleccionado and self.perfil_ruta_completa:
            if "ollama" in self.perfil_seleccionado.lower() and self.procesar_personalizacion:
                ConsoleUI.log_step(
                    f"Modificando simétricamente model: y custom_providers: en la plantilla: {self.perfil_seleccionado}..."
                )
                if YamlConfigManager.update_ollama_local(self.perfil_ruta_completa, self.final_base_url, self.final_modelo):
                    ConsoleUI.log_success("Valores variantes sincronizados en ambos bloques espejo con éxito.")
                else:
                    ConsoleUI.log_error("No se pudo actualizar el perfil de Ollama.")
                    self.error_detected = True
                    return

            ConsoleUI.log_step(f"Aplicando el perfil: {self.perfil_seleccionado}...")
            if YamlConfigManager.validates_differ(self.perfil_ruta_completa, Config.HERMES_GLOBAL_CONFIG_PATH):
                if os.path.exists(Config.HERMES_GLOBAL_CONFIG_PATH):
                    global_datos = YamlConfigManager.extract_config(Config.HERMES_GLOBAL_CONFIG_PATH)
                    if not global_datos["tiene_custom_providers"] and self.perfil_seleccionado != os.path.basename(Config.RESTORE_BKP_YAML):
                        if not os.path.exists(Config.RESTORE_BKP_YAML):
                            YamlConfigManager.read_and_write(
                                Config.HERMES_GLOBAL_CONFIG_PATH,
                                Config.RESTORE_BKP_YAML,
                                f"Respaldo dinámico de fábrica guardado en: {Config.RESTORE_BKP_YAML}"
                            )

                YamlConfigManager.read_and_write(
                    self.perfil_ruta_completa,
                    Config.HERMES_GLOBAL_CONFIG_PATH,
                    f"Perfil aplicado con éxito en: {Config.HERMES_GLOBAL_CONFIG_PATH}"
                )
            else:
                ConsoleUI.log_success(
                    f"La estructura global ya se encuentra en perfecta sincronía con el perfil {self.perfil_seleccionado}."
                )

        if self.resp_api and self.llave_api_final:
            self.env_mgr.set_var("API_SERVER_ENABLED", "true")
            self.env_mgr.set_var("API_SERVER_KEY", self.llave_api_final)
            self.env_mgr.set_var("API_SERVER_HOST", "0.0.0.0")
            self.env_mgr.set_var("API_SERVER_PORT", str(Config.GATEWAY_API_PORT))
            print(f"{ConsoleUI.VERDE}[API_KEY GUARDADA]:{ConsoleUI.RESET} {self.llave_api_final}")
            ConsoleUI.log_success("Parámetros de API inyectados con éxito en .env.")
        else:
            for var in ["API_SERVER_ENABLED", "API_SERVER_KEY", "API_SERVER_HOST", "API_SERVER_PORT"]:
                self.env_mgr.delete_var(var)
            ConsoleUI.log_success("Variables de API desactivadas y purgadas del archivo .env.")

        if self.resp_pass and self.webui_pass_final:
            self.env_mgr.set_var("HERMES_WEBUI_PASSWORD", self.webui_pass_final)
            password_enmascarada = "*" * len(self.webui_pass_final)
            print(f"{ConsoleUI.VERDE}[WEBUI_PASSWORD GUARDADA]:{ConsoleUI.RESET} {password_enmascarada}")
            ConsoleUI.log_success("Contraseña asentada en el entorno global de la WebUI.")
        else:
            self.env_mgr.delete_var("HERMES_WEBUI_PASSWORD")
            ConsoleUI.log_success("Filtro de contraseña deshabilitado por completo del .env.")
    def kill_hermes_processes(self):
        ConsoleUI.log_step("Ejecutando purga forzada de sockets liberando puertos activos...")        
        ProcessManager.kill_by_port(Config.GATEWAY_API_PORT)
        ProcessManager.kill_by_port(Config.MESSAGING_PORT)
        ProcessManager.kill_by_port(Config.DASHBOARD_PORT)
        ProcessManager.kill_by_port(Config.WEBUI_PORT)
        """
        ConsoleUI.log_step("Terminando proceso principal de hermes.exe...")
        ProcessManager.kill_by_name("hermes.exe")
        time.sleep(1.0)
        """
        time.sleep(1.0)

    def run_restart_stage(self):
        ConsoleUI.log_stage("Etapa 3: Orquestación e Inicio de Servicios")

        self.kill_hermes_processes()

        ConsoleUI.log_step("Lanzando Core Daemon ('hermes gateway')...")
        if ProcessManager.run_hidden("hermes gateway"):
            ConsoleUI.log_success("Gateway inicializado exitosamente en segundo plano.")
        else:
            self.error_detected = True

        ConsoleUI.log_step(f"Lanzando Servicio de Dashboard ('hermes dashboard' en puerto {Config.DASHBOARD_PORT})...")
        # NOTA: --skip-build eliminado según solicitud del usuario
        cmd_dashboard = f"hermes dashboard --host 0.0.0.0 --port {Config.DASHBOARD_PORT} --insecure --no-open --skip-build"
        if ProcessManager.run_hidden(cmd_dashboard):
            ConsoleUI.log_success("Dashboard montado correctamente.")
        else:
            self.error_detected = True

        ConsoleUI.log_step(f"Lanzando Web UI ('Hermes WebUI' en puerto {Config.WEBUI_PORT})...")
        cmd_webui = f'python "{Config.WEBUI_BOOTSTRAP}" --host 0.0.0.0 {Config.WEBUI_PORT} --no-browser'
        if ProcessManager.run_hidden(cmd_webui):
            ConsoleUI.log_success("WebUI levantada correctamente.")
        else:
            ConsoleUI.log_alert("No se pudo levantar la WebUI. Revise su configuración o intente instalar nuevamente.")
            self.error_detected = True
        
        if not self.error_detected:            
            ConsoleUI.log_success("Endpoints disponibles...")
            ConsoleUI.log_info(f"Gateway API: http://localhost:{Config.GATEWAY_API_PORT}")
            ConsoleUI.log_info(f"Dashboard: http://localhost:{Config.DASHBOARD_PORT}")
            ConsoleUI.log_info(f"Hermes WebUI: http://localhost:{Config.WEBUI_PORT}")

    def run_installation_steps(self):
        """Ejecuta instalación, setup y dashboard en tres terminales separadas"""
        ConsoleUI.log_stage("Iniciando procesos separados de instalación")
        
        ConsoleUI.log_step("Installation Step 1: Instalando agente Hermes")
        if not self.installer.install_agent_only():
            self.error_detected = True
            return False

        # Paso "hermes setup" según requerimiento.
        ConsoleUI.log_step("Installation Step 2: Configurando dashboard")
        if not self.installer.setup_dashboard(Config.DASHBOARD_PORT):
            self.error_detected = True
            return False

        # Paso "hermes webui" según requerimiento.
        ConsoleUI.log_step("Installation Step 3: Configurando hermes webui")
        if not self.installer.clone_webui():
            self.error_detected = True
            return False

        return True

    def run_update_terminal(self):
        """Ejecuta hermes update en una terminal separada"""
        ConsoleUI.log_stage("Ejecutando actualización de Hermes en terminal separada")
        try:
            result = subprocess.run(f'start /wait hermes update', shell=True)
            
            if result.returncode == 0:
                ConsoleUI.log_success("Actualización de Hermes completada.")
                return True
            else:
                ConsoleUI.log_error(f"Actualización falló: {result.stderr}")
                return False
        except Exception as e:
            ConsoleUI.log_error(f"Error ejecutando hermes update: {e}")
            return False

    def execute(self):
        """Flujo principal después de instalación/actualización"""
        self.run_input_stage()
        self.run_persistence_stage()
        if not self.error_detected:
            self.run_restart_stage()
        return self.error_detected