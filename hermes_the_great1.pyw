import subprocess
import sys
import os
import time
import secrets
import base64
import msvcrt  # Librería nativa de Windows para capturar caracteres en tiempo real

# =====================================================================
# CONFIGURACIÓN DE PARÁMETROS NATIVOS Y RUTAS DINÁMICAS
# =====================================================================
GATEWAY_API_PORT = 8642  # Puerto del API Server nativo de Hermes
DASHBOARD_PORT = 9119
WEBUI_PORT = 8787

# Obtener dinámicamente la ruta base del perfil del usuario
USER_PROFILE = os.environ.get("USERPROFILE", r"C:\Users\user")

WEBUI_BOOTSTRAP = os.path.join(
    USER_PROFILE, r"AppData\Local\hermes\hermes-webui\bootstrap.py"
)

# Rutas globales dinámicas de Hermes
HERMES_ENV_PATH = os.path.join(USER_PROFILE, r"AppData\Local\hermes\.env")
HERMES_GLOBAL_CONFIG_PATH = os.path.join(USER_PROFILE, r"AppData\Local\hermes\config.yaml")

# Configuración de rutas para el módulo de Ollama
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_YALM_DIR = os.path.join(SCRIPT_DIR, "config-yalm")
OLLAMA_LOCAL_YAML = os.path.join(CONFIG_YALM_DIR, "ollama.local.config.yalm")
FACTORY_BKP_YAML = os.path.join(CONFIG_YALM_DIR, "factory.bkp.config.yalm")

# Códigos de escape ANSI para colores en consola
AMARILLO = "\033[93m"
VERDE = "\033[92m"
ROJO = "\033[91m"
CIAN = "\033[96m"
# Color ámbar/dorado (naranja-amarillento) usando 256 colores (código 214)
AMBAR_DORADO = "\033[38;5;214m"
RESET = "\033[0m"

# ASCII Art para el Encabezado con color Ámbar/Dorado
HERMES_ASCII = f"""{AMBAR_DORADO}
██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗
██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝
███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗
██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║
██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝

████████╗██╗  ██╗███████╗     ██████╗ ██████╗ ███████╗ █████╗ ████████╗     ██╗
╚══██╔══╝██║  ██║██╔════╝    ██╔════╝ ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝    ███║
   ██║   ███████║█████╗      ██║  ███╗██████╔╝█████╗  ███████║   ██║       ╚██║
   ██║   ██╔══██║██╔══╝      ██║   ██║██╔══██╗██╔══╝  ██╔══██║   ██║        ██║
   ██║   ██║  ██║███████╗    ╚██████╔╝██║  ██║███████╗██║  ██║   ██║        ██║
   ╚═╝   ╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝        ╚═╝
v 1.0.1
===============================================================================
            Orquestador de Servicios de Hermes Agent - by @mjunez
===============================================================================
{RESET}"""

# =====================================================================
# FUNCIONES AUXILIARES NATIVAS
# =====================================================================
def log_etapa(titulo):
    print(f"\n{CIAN}=== {titulo.upper()} ==={RESET}\n")

def log_paso(mensaje):
    print(f"{AMARILLO}[PASO]{RESET} {mensaje}")

def log_exito(mensaje):
    print(f"{VERDE}[OK]{RESET} {mensaje}")

def log_error(mensaje):
    print(f"{ROJO}[ERROR]{RESET} {mensaje}")

def ejecutar_totalmente_oculto(comando_string):
    """Lanza un comando de forma 100% invisible en Windows usando un script VBS temporal."""
    try:
        vbs_path = os.path.join(os.environ.get("TEMP", "."), "hermes_runner.vbs")
        comando_escapado = comando_string.replace('"', '""')
        vbs_content = f'CreateObject("Wscript.Shell").Run "cmd.exe /c {comando_escapado}", 0, False'
        
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        
        subprocess.Popen(f'wscript.exe "{vbs_path}"', shell=True)
        time.sleep(0.2) 
        return True
    except Exception as e:
        log_error(f"Excepción al lanzar proceso oculto: {e}")
        return False

def matar_proceso_por_puerto(puerto):
    """
    Busca el PID escuchando en el puerto, detiene el gateway de forma nativa 
    en segundo plano primero, y luego elimina el proceso de forma forzada.
    """
    # Detener el gateway nativamente pero en segundo plano antes de la purga
    ejecutar_totalmente_oculto("hermes gateway stop")

    try:
        cmd = f'netstat -ano | findstr /R /C:":{puerto} *[^ ]* *LISTENING"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.stdout:
            lines = res.stdout.strip().split("\n")
            pids = set(line.strip().split()[-1] for line in lines if line.strip())
            for pid in pids:
                if pid != "0":
                    subprocess.run(f"taskkill /PID {pid} /F /T", shell=True, capture_output=True)
            return True
    except Exception:
        pass
    return False

def generar_api_key_base64():
    """Genera un token criptográfico seguro en Base64."""
    bytes_seguros = secrets.token_bytes(48)
    return base64.b64encode(bytes_seguros).decode('utf-8')

def obtener_variable_de_env(ruta_env, variable_nombre):
    """Busca el valor de una variable directamente en el archivo .env."""
    if not os.path.exists(ruta_env):
        return None
    try:
        with open(ruta_env, "r", encoding="utf-8") as f:
            for linea in f:
                if linea.strip().startswith(f"{variable_nombre}="):
                    return linea.strip().split("=", 1)[1].replace('"', '').replace("'", "")
    except Exception:
        pass
    return None

def establecer_variable_en_env(ruta_env, variable_nombre, valor):
    """Establece variables con formato estricto de producción en el .env."""
    try:
        lineas = []
        if os.path.exists(ruta_env):
            with open(ruta_env, "r", encoding="utf-8") as f:
                lineas = f.readlines()
        
        valor_limpio = str(valor).replace('"', '').replace("'", "").strip()
        lineas_filtradas = [l for l in lineas if not l.strip().startswith(f"{variable_nombre}=")]
        
        if lineas_filtradas and not lineas_filtradas[-1].endswith("\n"):
            lineas_filtradas[-1] += "\n"
            
        lineas_filtradas.append(f"{variable_nombre}={valor_limpio}\n")
        
        with open(ruta_env, "w", encoding="utf-8") as f:
            f.writelines(lineas_filtradas)
        return True
    except Exception as e:
        log_error(f"Error al escribir en .env ({variable_nombre}): {e}")
        return False

def eliminar_variable_del_env(ruta_env, variable_nombre):
    """Lee el archivo .env y elimina la línea de la variable indicada por completo."""
    if not os.path.exists(ruta_env):
        return
    try:
        with open(ruta_env, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        
        lineas_filtradas = [l for l in lineas if not l.strip().startswith(f"{variable_nombre}=")]
        
        with open(ruta_env, "w", encoding="utf-8") as f:
            f.writelines(lineas_filtradas)
    except Exception as e:
        log_error(f"No se pudo limpiar la variable {variable_nombre} del archivo .env: {e}")

def input_con_asteriscos(prompt):
    """Muestra un prompt y captura la entrada del usuario enmascarándola con asteriscos."""
    print(prompt, end="", flush=True)
    password = ""
    while True:
        ch = msvcrt.getch()
        if ch in (b'\r', b'\n'):
            print() 
            break
        elif ch == b'\x08':
            if len(password) > 0:
                password = password[:-1]
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        else:
            try:
                caracter = ch.decode('utf-8')
                password += caracter
                sys.stdout.write('*')
                sys.stdout.flush()
            except UnicodeDecodeError:
                pass 
    return password

def extraer_datos_config_yaml(ruta_yaml):
    """
    Función Unificada Pura por Bloques: Identifica y extrae de forma independiente 
    las variables variantes tanto de model: como de custom_providers: al estar al mismo nivel.
    """
    datos = {"provider": "No definido", "base_url": "No definido", "default": "No definido", "tiene_custom_providers": False}
    if not os.path.exists(ruta_yaml):
        return datos
    try:
        with open(ruta_yaml, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        
        bloque_actual = None  # Puede ser "model" o "custom_providers"
        
        for linea in lineas:
            linea_strip = linea.strip()
            if not linea_strip or linea_strip.startswith("#"):
                continue
            
            indent_actual = len(linea) - len(linea.lstrip())
            
            # Detectar cambios de bloque principales (Raíz / Indentación 0)
            if indent_actual == 0:
                if linea_strip.startswith("model:"):
                    bloque_actual = "model"
                    continue
                elif linea_strip.startswith("custom_providers:"):
                    bloque_actual = "custom_providers"
                    datos["tiene_custom_providers"] = True
                    continue
                elif ":" in linea_strip:
                    bloque_actual = None  # Otro bloque raíz, salimos del contexto anterior
            
            # Extraer del bloque model principal
            if bloque_actual == "model":
                if linea_strip.startswith("provider:"):
                    datos["provider"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                elif linea_strip.startswith("base_url:") and datos["base_url"] == "No definido":
                    datos["base_url"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                elif linea_strip.startswith("default:") and datos["default"] == "No definido":
                    datos["default"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                    
            # Si el bloque model no tenía la URL o el default pero está en custom_providers como comodín de respaldo
            elif bloque_actual == "custom_providers":
                if linea_strip.startswith("base_url:") and datos["base_url"] == "No definido":
                    datos["base_url"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                elif linea_strip.startswith("model:") and not linea_strip.startswith("models:") and datos["default"] == "No definido":
                    datos["default"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
    except Exception:
        pass
    return datos

def validar_campos_difieren(ruta1, ruta2):
    """Compara valores estructurales y campos variantes de ambos archivos en paralelo."""
    campos1 = extraer_datos_config_yaml(ruta1)
    campos2 = extraer_datos_config_yaml(ruta2)
    
    valores_difieren = (campos1["provider"] != campos2["provider"]) or (campos1["base_url"] != campos2["base_url"]) or (campos1["default"] != campos2["default"])
    estructura_difiere = (campos1["tiene_custom_providers"] != campos2["tiene_custom_providers"])
    
    return valores_difieren or estructura_difiere

def actualizar_yaml_local_ollama(base_url, modelo):
    """Inyecta de forma paralela y simétrica las decisiones del usuario en model y custom_providers."""
    if not os.path.exists(OLLAMA_LOCAL_YAML):
        log_error(f"No se encontró la plantilla local en: {OLLAMA_LOCAL_YAML}")
        return False
    try:
        with open(OLLAMA_LOCAL_YAML, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        
        nuevas_lineas = []
        bloque_actual = None

        for linea in lineas:
            linea_strip = linea.strip()
            indent_actual = len(linea) - len(linea.lstrip())

            if indent_actual == 0:
                if linea_strip.startswith("model:"):
                    bloque_actual = "model"
                    nuevas_lineas.append(linea)
                    continue
                elif linea_strip.startswith("custom_providers:"):
                    bloque_actual = "custom_providers"
                    nuevas_lineas.append(linea)
                    continue
                elif ":" in linea_strip:
                    bloque_actual = None

            if bloque_actual == "model":
                if linea_strip.startswith("base_url:"):
                    nuevas_lineas.append(f"{' ' * indent_actual}base_url: {base_url}\n")
                elif linea_strip.startswith("default:"):
                    nuevas_lineas.append(f"{' ' * indent_actual}default: {modelo}\n")
                elif linea_strip.startswith("provider:"):
                    nuevas_lineas.append(f"{' ' * indent_actual}provider: ollama\n")
                else:
                    nuevas_lineas.append(linea)

            elif bloque_actual == "custom_providers":
                if linea_strip.startswith("base_url:"):
                    nuevas_lineas.append(f"{' ' * indent_actual}base_url: {base_url}\n")
                elif linea_strip.startswith("model:") and not linea_strip.startswith("models:"):
                    nuevas_lineas.append(f"{' ' * indent_actual}model: {modelo}\n")
                elif (linea_strip.startswith("- name:") or ":" in linea_strip) and "context_length:" in linea_strip:
                    partes = linea_strip.split("context_length:")
                    valor_contexto = partes[1].strip() if len(partes) > 1 else ""
                    if linea_strip.startswith("-"):
                        nuevas_lineas.append(f"{' ' * indent_actual}- name: {modelo}\n{' ' * (indent_actual + 2)}context_length: {valor_contexto}\n")
                    else:
                        nuevas_lineas.append(f"{' ' * indent_actual}{modelo}:\n{' ' * (indent_actual + 2)}context_length: {valor_contexto}\n")
                else:
                    if linea_strip.endswith(":") and not (linea_strip.startswith("models:") or linea_strip.startswith("base_url:") or linea_strip.startswith("model:")):
                        nuevas_lineas.append(f"{' ' * indent_actual}{modelo}:\n")
                    else:
                        nuevas_lineas.append(linea)
            else:
                nuevas_lineas.append(linea)
                
        with open(OLLAMA_LOCAL_YAML, "w", encoding="utf-8") as f:
            f.writelines(nuevas_lineas)
        return True
    except Exception as e:
        log_error(f"Error al escribir en ollama.local.config.yalm: {e}")
        return False

def leer_y_escribir_archivo(origen, destino, msg_log):
    """Clona flujos de archivos para transmutaciones globales reflejando la acción en logs."""
    try:
        with open(origen, "r", encoding="utf-8") as f:
            contenido = f.read()
        with open(destino, "w", encoding="utf-8") as f:
            f.write(contenido)
        log_exito(msg_log)
        return True
    except Exception as e:
        log_error(f"Error en transferencia de archivos ({origen} -> {destino}): {e}")
        return False

# =====================================================================
# CORE PIPELINE ESTRUCTURAL EN TRES ETAPAS
# =====================================================================
def gestionar_hermes():
    error_detectado = False
    
    if not os.path.exists(CONFIG_YALM_DIR):
        os.makedirs(CONFIG_YALM_DIR)

    # -----------------------------------------------------------------
    # ETAPA 1: RECOLECCIÓN DE INPUTS POR SECCIÓN
    # -----------------------------------------------------------------
    log_etapa("Etapa 1: Recolección de Inputs")
    
    # Inputs Sección 1: Perfil Ollama
    resp_ollama = input(f"{AMARILLO}[PREGUNTA]{RESET} ¿Usar Modelos de Ollama Locales? [Y/N]: ").strip().lower()
    ollama_final_base_url = None
    ollama_final_modelo = None
    procesar_ollama_profile = False

    if resp_ollama == 'y':
        valores_actuales = extraer_datos_config_yaml(OLLAMA_LOCAL_YAML)
        
        print(f"{VERDE}[INFO]{RESET} Valores predefinidos leídos de OLLAMA_LOCAL_YAML: Base_URL: {valores_actuales['base_url']}, Model: {valores_actuales['default']}")
        resp_cambiar = input(f"{AMARILLO}[PREGUNTA]{RESET} ¿Desea cambiar los valores? [Y/N]: ").strip().lower()
        
        if resp_cambiar == 'y':
            ollama_final_base_url = input(f"{AMARILLO}[INPUT]{RESET} Base URL (ej.: http://127.0.0.1:11434/v1): ").strip()
            ollama_final_modelo = input(f"{AMARILLO}[INPUT]{RESET} Modelo por defecto (ej.: deepseek-r1:14b): ").strip()
            
            if not ollama_final_base_url or not ollama_final_modelo:
                log_error("Entradas inválidas o vacías detectadas. Se abortará la inyección para proteger la integridad estructural.")
                error_detectado = True
            else:
                procesar_ollama_profile = True
        else:
            if valores_actuales['base_url'] == "No definido" or valores_actuales['default'] == "No definido":
                log_error("No se pudieron aislar variantes válidas en OLLAMA_LOCAL_YAML. Configuración manual mandatoria.")
                error_detectado = True
            else:
                ollama_final_base_url = valores_actuales['base_url']
                ollama_final_modelo = valores_actuales['default']
                procesar_ollama_profile = True

    # Inputs Sección 2: API Server
    resp_api = input(f"{AMARILLO}[PREGUNTA]{RESET} ¿Activar API Server? [Y/N]: ").strip().lower()
    llave_api_final = None
    
    if resp_api == 'y':
        llave_actual = obtener_variable_de_env(HERMES_ENV_PATH, "API_SERVER_KEY")
        if llave_actual:
            print(f"{VERDE}[INFO]{RESET} Se detectó una API-Key guardada actualmente.")
            resp_update = input(f"{AMARILLO}[PREGUNTA]{RESET} ¿Desea actualizar la API-Key actual? [Y/N]: ").strip().lower()
            llave_api_final = generar_api_key_base64() if resp_update == 'y' else llave_actual
        else:
            llave_api_final = generar_api_key_base64()

    # Inputs Sección 3: WebUI Password
    resp_pass = input(f"{AMARILLO}[PREGUNTA]{RESET} ¿Proteger WebUI Chat por contraseña? [Y/N]: ").strip().lower()
    webui_pass_final = None
    
    if resp_pass == 'y':
        pass_actual = obtener_variable_de_env(HERMES_ENV_PATH, "HERMES_WEBUI_PASSWORD")
        if pass_actual:
            print(f"{VERDE}[INFO]{RESET} Se detectó una contraseña de WebUI guardada actualmente.")
            resp_mantener = input(f"{AMARILLO}[PREGUNTA]{RESET} ¿Desea mantener la misma contraseña? [Y/N]: ").strip().lower()
            if resp_mantener == 'y':
                webui_pass_final = pass_actual
        
        if webui_pass_final is None:
            prompt_str = f"{AMARILLO}[INPUT]{RESET} Introduce la nueva contraseña para la WebUI: "
            user_password = input_con_asteriscos(prompt_str).strip()
            if user_password:
                webui_pass_final = user_password
            else:
                log_error("Contraseña vacía recibida. Se mantendrá el respaldo anterior de existir.")
                webui_pass_final = pass_actual

    # -----------------------------------------------------------------
    # ETAPA 2: MODIFICACIÓN DE ARCHIVOS SEGÚN CORRESPONDA
    # -----------------------------------------------------------------
    log_etapa("Etapa 2: Persistencia y Modificación de Archivos")
    
    if error_detectado:
        log_error("Flujo de persistencia comprometido por inputs inválidos en Etapa 1. Cambios cancelados.")
        return True

    # 1. Escritura y sincronización simétrica de Perfiles YAML
    if resp_ollama == 'y' and procesar_ollama_profile:
        log_paso(f"Modificando simétricamente model: y custom_providers: en la plantilla: {OLLAMA_LOCAL_YAML}...")
        if actualizar_yaml_local_ollama(ollama_final_base_url, ollama_final_modelo):
            log_exito("Valores variantes sincronizados en ambos bloques espejo con éxito.")
            
            if validar_campos_difieren(OLLAMA_LOCAL_YAML, HERMES_GLOBAL_CONFIG_PATH):
                global_datos = extraer_datos_config_yaml(HERMES_GLOBAL_CONFIG_PATH)
                if not global_datos["tiene_custom_providers"] and os.path.exists(HERMES_GLOBAL_CONFIG_PATH):
                    leer_y_escribir_archivo(HERMES_GLOBAL_CONFIG_PATH, FACTORY_BKP_YAML, f"Respaldo dinámico de fábrica guardado en: {FACTORY_BKP_YAML}")
                
                leer_y_escribir_archivo(OLLAMA_LOCAL_YAML, HERMES_GLOBAL_CONFIG_PATH, f"Mutación global simétrica aplicada en: {HERMES_GLOBAL_CONFIG_PATH}")
            else:
                log_exito("La estructura global ya se encuentra en perfecta sincronía simétrica con Ollama.")
    else:
        log_paso("Validando balance estructural con configuración de Fábrica...")
        if os.path.exists(FACTORY_BKP_YAML):
            if validar_campos_difieren(FACTORY_BKP_YAML, HERMES_GLOBAL_CONFIG_PATH):
                leer_y_escribir_archivo(FACTORY_BKP_YAML, HERMES_GLOBAL_CONFIG_PATH, "Estructura asimétrica/Ollama detectada. Configuración original de fábrica restablecida.")
            else:
                log_exito("El ecosistema global ya se encuentra limpio de Ollama y alineado con Fábrica. No requiere escritura.")
        else:
            log_error("No se localizó el archivo factory.bkp.config.yalm para la restauración.")

    # 2. Modificación de variables API_SERVER en .env
    if resp_api == 'y' and llave_api_final:
        establecer_variable_en_env(HERMES_ENV_PATH, "API_SERVER_ENABLED", "true")
        establecer_variable_en_env(HERMES_ENV_PATH, "API_SERVER_KEY", llave_api_final)
        establecer_variable_en_env(HERMES_ENV_PATH, "API_SERVER_HOST", "0.0.0.0")
        establecer_variable_en_env(HERMES_ENV_PATH, "API_SERVER_PORT", str(GATEWAY_API_PORT))
        print(f"{VERDE}[API_KEY GUARDADA]:{RESET} {llave_api_final}")
        log_exito("Parámetros de API inyectados con éxito en .env.")
    else:
        for var in ["API_SERVER_ENABLED", "API_SERVER_KEY", "API_SERVER_HOST", "API_SERVER_PORT"]:
            eliminar_variable_del_env(HERMES_ENV_PATH, var)
        log_exito("Variables de API desactivadas y purgadas del archivo .env.")

    # 3. Modificación de WEBUI_PASSWORD en .env
    if resp_pass == 'y' and webui_pass_final:
        establecer_variable_en_env(HERMES_ENV_PATH, "HERMES_WEBUI_PASSWORD", webui_pass_final)
        password_enmascarada = "*" * len(webui_pass_final)
        print(f"{VERDE}[WEBUI_PASSWORD GUARDADA]:{RESET} {password_enmascarada}")
        log_exito("Contraseña asentada en el entorno global de la WebUI.")
    else:
        eliminar_variable_del_env(HERMES_ENV_PATH, "HERMES_WEBUI_PASSWORD")
        log_exito("Filtro de contraseña deshabilitado por completo del .env.")

    # -----------------------------------------------------------------
    # ETAPA 3: REINICIO DE HERMES EN SEGUNDO PLANO (FLUJO MÁGICO)
    # -----------------------------------------------------------------
    log_etapa("Etapa 3: Orquestación e Inicio Oculto de Servicios")
    
    log_paso("Ejecutando purga forzada de sockets liberando puertos activos...")
    matar_proceso_por_puerto(GATEWAY_API_PORT) 
    matar_proceso_por_puerto(DASHBOARD_PORT)   
    matar_proceso_por_puerto(WEBUI_PORT)       
    
    # Cereza del pastel: Limpieza absoluta por imagen de proceso
    log_paso("Aplicando golpe maestro: Purgando hilos huérfanos de hermes.exe...")
    subprocess.run("taskkill /F /IM hermes.exe", shell=True, capture_output=True)
    time.sleep(1.0)

    # Lanzamiento del daemon a secas sin argumentos (Carga transparente de Variables de Entorno)
    log_paso(f"Lanzando Core Daemon Invisible ('hermes gateway run' a secas)...")
    if ejecutar_totalmente_oculto("hermes gateway restart"):
        ejecutar_totalmente_oculto("hermes gateway run")
        log_exito("Gateway inicializado exitosamente en segundo plano.")
    else:
        error_detectado = True

    log_paso(f"Lanzando Servicio de Telemetría Invisible ('hermes dashboard' en puerto {DASHBOARD_PORT})...")
    cmd_dashboard = f"hermes dashboard --host 0.0.0.0 --port {DASHBOARD_PORT} --insecure --no-open --skip-build"
    if ejecutar_totalmente_oculto(cmd_dashboard):
        log_exito("Dashboard montado correctamente.")
    else:
        error_detectado = True

    log_paso(f"Lanzando Interfaz Gráfica Invisible ('Hermes WebUI' en puerto {WEBUI_PORT})...")
    cmd_webui = f'python "{WEBUI_BOOTSTRAP}" --host 0.0.0.0 {WEBUI_PORT} --no-browser'
    if ejecutar_totalmente_oculto(cmd_webui):
        log_exito("WebUI levantada correctamente.")
    else:
        error_detectado = True

    return error_detectado

# =====================================================================
# ENTRADA DEL PROGRAMA Y CONTROL DE SALIDA ESTRICTO
# =====================================================================
if __name__ == "__main__":
    if sys.platform == "win32":
        os.system('color')

    # Imprimir el ASCII Art antes del encabezado de texto
    print(HERMES_ASCII)

    try:
        hubo_error = gestionar_hermes()
        print() 
        if hubo_error:
            log_error("Pipeline finalizado con advertencias estructurales.")
        else:
            log_exito("¡Pipeline ejecutado con éxito total usando el flujo mágico!")
            
    except Exception as e:
        log_error(f"\nSe interrumpió el flujo debido a una excepción crítica: {e}")
    
    print("\n" + "-"*53)
    print("Ya puedes cerrar la ventana! o presiona [Enter] 2 veces para salir...", end="", flush=True)
    msvcrt.getch()
    os._exit(0)