import os
import subprocess
import time
from console_ui import ConsoleUI


class ProcessManager:
    @staticmethod
    def run_hidden(command_string):
        try:
            temp_dir = os.environ.get("TEMP", ".")
            vbs_path = os.path.join(temp_dir, "hermes_runner.vbs")
            escaped_command = command_string.replace('"', '""')
            vbs_content = f'CreateObject("Wscript.Shell").Run "cmd.exe /c {escaped_command}", 0, False'

            with open(vbs_path, "w", encoding="utf-8") as f:
                f.write(vbs_content)

            subprocess.Popen(f'wscript.exe "{vbs_path}"', shell=True)
            time.sleep(0.2)
            return True
        except Exception as e:
            ConsoleUI.log_error(f"Excepción al lanzar proceso oculto: {e}")
            return False

    @classmethod
    def kill_by_port(cls, port):
        cls.run_hidden("hermes gateway stop")

        try:
            cmd = f'netstat -ano | findstr /R /C:":{port} *[^ ]* *LISTENING"'
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

    @staticmethod
    def kill_by_name(process_name):
        try:
            subprocess.run(f"taskkill /F /IM {process_name}", shell=True, capture_output=True)
            return True
        except Exception:
            return False
