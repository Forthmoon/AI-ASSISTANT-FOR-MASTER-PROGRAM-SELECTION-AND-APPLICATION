# app_final/config.py

import os
import yaml


current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))



config_file_path = os.path.join(project_root, "config.yaml")


def load_config():
    with open(config_file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config_data = load_config()


openai_api_key = config_data["config"]["api_keys"]["openai"]
llm_config = config_data["config"]["llm"]

