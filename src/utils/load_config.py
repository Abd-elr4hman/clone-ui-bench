import json

from src.judge import DEFAULT_JUDGES


def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        models = config.get("models")
        urls = config.get("urls")
        # `judges` is the panel; `judge` is accepted as a single-model shorthand.
        judges = config.get("judges")
        if not judges:
            single = config.get("judge")
            judges = [single] if single else list(DEFAULT_JUDGES)
        if isinstance(judges, str):
            judges = [judges]

        if not models:
            raise ValueError("No models specified in config file")
        if not urls:
            raise ValueError("No URLs specified in config file")

        return models, urls, judges

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file '{config_file}' not found")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
