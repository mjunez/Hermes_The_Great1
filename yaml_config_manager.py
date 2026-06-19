import os
from console_ui import ConsoleUI


class YamlConfigManager:
    @staticmethod
    def extract_config(yaml_path):
        datos = {"provider": "No definido", "base_url": "No definido", "default": "No definido", "tiene_custom_providers": False}
        if not os.path.exists(yaml_path):
            return datos
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                lineas = f.readlines()

            bloque_actual = None
            for linea in lineas:
                linea_strip = linea.strip()
                if not linea_strip or linea_strip.startswith("#"):
                    continue

                indent_actual = len(linea) - len(linea.lstrip())
                if indent_actual == 0:
                    if linea_strip.startswith("model:"):
                        bloque_actual = "model"
                        continue
                    elif linea_strip.startswith("custom_providers:"):
                        bloque_actual = "custom_providers"
                        datos["tiene_custom_providers"] = True
                        continue
                    elif ":" in linea_strip:
                        bloque_actual = None

                if bloque_actual == "model":
                    if linea_strip.startswith("provider:"):
                        datos["provider"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                    elif linea_strip.startswith("base_url:") and datos["base_url"] == "No definido":
                        datos["base_url"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                    elif linea_strip.startswith("default:") and datos["default"] == "No definido":
                        datos["default"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")

                elif bloque_actual == "custom_providers":
                    if linea_strip.startswith("base_url:") and datos["base_url"] == "No definido":
                        datos["base_url"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
                    elif linea_strip.startswith("model:") and not linea_strip.startswith("models:") and datos["default"] == "No definido":
                        datos["default"] = linea_strip.split(":", 1)[1].strip().replace('"', '').replace("'", "")
        except Exception:
            pass
        return datos

    @classmethod
    def validates_differ(cls, path1, path2):
        campos1 = cls.extract_config(path1)
        campos2 = cls.extract_config(path2)

        valores_difieren = (campos1["provider"] != campos2["provider"]) or \
                           (campos1["base_url"] != campos2["base_url"]) or \
                           (campos1["default"] != campos2["default"])
        estructura_difiere = (campos1["tiene_custom_providers"] != campos2["tiene_custom_providers"])

        return valores_difieren or estructura_difiere

    @staticmethod
    def build_ollama_local_config(source_yaml_path, base_url, model):
        if not os.path.exists(source_yaml_path):
            ConsoleUI.log_error(f"No se encontró el archivo de origen {source_yaml_path}.")
            return None

        try:
            with open(source_yaml_path, "r", encoding="utf-8") as f:
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
                    elif linea_strip.startswith("-"):
                        # Items de lista bajo custom_providers mantienen el bloque activo
                        if bloque_actual != "custom_providers":
                            bloque_actual = None
                    elif ":" in linea_strip:
                        bloque_actual = None

                if bloque_actual == "model":
                    if linea_strip.startswith("base_url:"):
                        nuevas_lineas.append(f"{' ' * indent_actual}base_url: {base_url}\n")
                    elif linea_strip.startswith("default:"):
                        nuevas_lineas.append(f"{' ' * indent_actual}default: {model}\n")
                    elif linea_strip.startswith("provider:"):
                        nuevas_lineas.append(f"{' ' * indent_actual}provider: ollama\n")
                    else:
                        nuevas_lineas.append(linea)

                elif bloque_actual == "custom_providers":
                    if linea_strip.startswith("base_url:"):
                        nuevas_lineas.append(f"{' ' * indent_actual}base_url: {base_url}\n")
                    elif linea_strip.startswith("model:") and not linea_strip.startswith("models:"):
                        nuevas_lineas.append(f"{' ' * indent_actual}model: {model}\n")
                    elif linea_strip.endswith(":") and not (linea_strip.startswith("models:") or linea_strip.startswith("base_url:") or linea_strip.startswith("model:")):
                        nuevas_lineas.append(f"{' ' * indent_actual}{model}:\n")
                    else:
                        nuevas_lineas.append(linea)
                else:
                    nuevas_lineas.append(linea)

            return "".join(nuevas_lineas)
        except Exception as e:
            ConsoleUI.log_error(f"Error al construir configuración de Ollama desde {source_yaml_path}: {e}")
            return None

    @staticmethod
    def write_string_to_file(destination, content, log_msg):
        try:
            with open(destination, "w", encoding="utf-8") as f:
                f.write(content)
            ConsoleUI.log_success(log_msg)
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error al escribir en {destination}: {e}")
            return False

    @staticmethod
    def update_ollama_local(source_yaml_path, yaml_path, base_url, model):
        content = YamlConfigManager.build_ollama_local_config(source_yaml_path, base_url, model)
        if content is None:
            return False
        return YamlConfigManager.write_string_to_file(
            yaml_path,
            content,
            f"Configuración de Ollama generada en memoria y guardada en: {yaml_path}"
        )

    @staticmethod
    def read_and_write(source, destination, log_msg):
        try:
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()
            with open(destination, "w", encoding="utf-8") as f:
                f.write(content)
            ConsoleUI.log_success(log_msg)
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error en transferencia de archivos ({source} -> {destination}): {e}")
            return False
