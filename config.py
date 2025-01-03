import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

SETTINGS_FILE = "settings.json"

def validate_settings(settings):
    required_fields = ["server_port", "log_prompts", "prompt_folder", "files_folder"]
    return all(field in settings for field in required_fields)

def load_settings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            # Override with environment variables if they exist
            settings["server_port"] = os.getenv("SERVER_PORT", settings.get("server_port", "1234"))
            return settings
    except FileNotFoundError:
        return {
            "server_port": os.getenv("SERVER_PORT", "1234"),
            "log_prompts": True,
            "prompt_folder": "",
            "files_folder": "",
            "selected_prompt": ""
        }

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4) 