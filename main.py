import os
import msvcrt

from console_ui import ConsoleUI
from orchestrator import HermesOrchestrator


def main():
    ConsoleUI.print_logo()
    try:
        orchestrator = HermesOrchestrator()
        hubo_error = orchestrator.execute()
        print()
        if hubo_error:
            ConsoleUI.log_error("Pipeline finalizado con advertencias estructurales.")
        else:
            ConsoleUI.log_success("¡Pipeline ejecutado con éxito total usando el flujo mágico!")
    except Exception as e:
        ConsoleUI.log_error(f"\nSe interrumpió el flujo debido a una excepción crítica: {e}")
    finally:
        print("\n" + "-" * 53)
        print("Ya puedes cerrar la ventana! o presiona [Enter] 2 veces para salir...", end="", flush=True)
        msvcrt.getch()
        os._exit(0)


if __name__ == "__main__":
    main()
