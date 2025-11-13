import os
import json

SETTINGS_FILE = "settings.json"

def load_settings():
    """Loads the database settings from a JSON file, including SSL settings."""
    default_config = {
        "host": "localhost",
        "database": "",
        "ssl": {
            "enabled": False,
            "cert_path": ""
        }
    }

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as file:
                loaded_config = json.load(file)

                # Update top-level fields
                default_config["host"] = loaded_config.get("host", "localhost")
                default_config["database"] = loaded_config.get("database", "")
                

                # Update nested SSL config
                ssl_config = loaded_config.get("ssl", {})
                default_config["ssl"]["enabled"] = ssl_config.get("enabled", False)
                default_config["ssl"]["cert_path"] = ssl_config.get("cert_path", "")

        except Exception as e:
            print(f"⚠️ Failed to load settings: {e}")

    return default_config
