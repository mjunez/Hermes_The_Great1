import sys
import os
import msvcrt


class ConsoleUI:
    AMARILLO = "\033[93m"
    VERDE = "\033[92m"
    ROJO = "\033[91m"
    CIAN = "\033[96m"
    AMBAR_DORADO = "\033[38;5;214m"
    RESET = "\033[0m"

    HERMES_ASCII = f"""{AMBAR_DORADO}
██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗
██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝
███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗
██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║
██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝
v 1.0.1
===============================================================================
            Orquestador de Servicios de Hermes Agent - by @mjunez
===============================================================================
{RESET}"""

    @classmethod
    def enable_ansi_colors(cls):
        if sys.platform == "win32":
            os.system('color')

    @classmethod
    def print_logo(cls):
        cls.enable_ansi_colors()
        print(cls.HERMES_ASCII)

    @classmethod
    def log_stage(cls, titulo):
        print(f"\n{cls.CIAN}=== {titulo.upper()} ==={cls.RESET}\n")

    @classmethod
    def log_step(cls, mensaje):
        print(f"{cls.AMARILLO}[PASO]{cls.RESET} {mensaje}")

    @classmethod
    def log_success(cls, mensaje):
        print(f"{cls.VERDE}[OK]{cls.RESET} {mensaje}")

    @classmethod
    def log_error(cls, mensaje):
        print(f"{cls.ROJO}[ERROR]{cls.RESET} {mensaje}")

    @classmethod
    def prompt_yn(cls, question_text):
        resp = input(f"{cls.AMARILLO}[PREGUNTA]{cls.RESET} {question_text} [Y/N]: ").strip().lower()
        return resp == 'y'

    @classmethod
    def prompt_input(cls, prompt_text):
        return input(f"{cls.AMARILLO}[INPUT]{cls.RESET} {prompt_text}: ").strip()

    @classmethod
    def input_password(cls, prompt_text):
        print(prompt_text, end="", flush=True)
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
                    character = ch.decode('utf-8')
                    password += character
                    sys.stdout.write('*')
                    sys.stdout.flush()
                except UnicodeDecodeError:
                    pass
        return password
