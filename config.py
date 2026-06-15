import os


class Config:
    GATEWAY_API_PORT = 8642  # Puerto del API Server nativo de Hermes
    DASHBOARD_PORT = 9119
    WEBUI_PORT = 8787
    MESSAGING_PORT = 3000

    USER_PROFILE = os.environ.get("USERPROFILE", r"C:\Users\user")

    WEBUI_BOOTSTRAP = os.path.join(
        USER_PROFILE, r"AppData\Local\hermes\hermes-webui\bootstrap.py"
    )

    HERMES_ENV_PATH = os.path.join(USER_PROFILE, r"AppData\Local\hermes\.env")
    HERMES_GLOBAL_CONFIG_PATH = os.path.join(USER_PROFILE, r"AppData\Local\hermes\config.yaml")

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_YALM_DIR = os.path.join(SCRIPT_DIR, "config-yalm")
    OLLAMA_LOCAL_YAML = os.path.join(CONFIG_YALM_DIR, "ollama.local.config.yalm")
    RESTORE_BKP_YAML = os.path.join(CONFIG_YALM_DIR, "restore.bkp.config.yalm")
