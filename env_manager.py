import os
from console_ui import ConsoleUI


class EnvManager:
    def __init__(self, env_path):
        self.env_path = env_path

    def get_var(self, variable_name):
        if not os.path.exists(self.env_path):
            return None
        try:
            with open(self.env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith(f"{variable_name}="):
                        return line.strip().split("=", 1)[1].replace('"', '').replace("'", "")
        except Exception:
            pass
        return None

    def set_var(self, variable_name, value):
        try:
            lines = []
            if os.path.exists(self.env_path):
                with open(self.env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            clean_value = str(value).replace('"', '').replace("'", "").strip()
            filtered_lines = [l for l in lines if not l.strip().startswith(f"{variable_name}=")]

            if filtered_lines and not filtered_lines[-1].endswith("\n"):
                filtered_lines[-1] += "\n"

            filtered_lines.append(f"{variable_name}={clean_value}\n")

            with open(self.env_path, "w", encoding="utf-8") as f:
                f.writelines(filtered_lines)
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Error al escribir en .env ({variable_name}): {e}")
            return False

    def delete_var(self, variable_name):
        if not os.path.exists(self.env_path):
            return
        try:
            with open(self.env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            filtered_lines = [l for l in lines if not l.strip().startswith(f"{variable_name}=")]

            with open(self.env_path, "w", encoding="utf-8") as f:
                f.writelines(filtered_lines)
        except Exception as e:
            ConsoleUI.log_error(f"No se pudo limpiar la variable {variable_name} del archivo .env: {e}")
