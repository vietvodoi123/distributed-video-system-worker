# utils/yaml_loader.py
import os
import yaml

def load_yaml_settings():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BASE_DIR, "config", "settings.yaml"), "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    # Chuẩn hóa credentials_path -> absolute path
    if "credentials_path" in settings:
        if not os.path.isabs(settings["credentials_path"]):
            settings["credentials_path"] = os.path.join(BASE_DIR, settings["credentials_path"])

    return settings
