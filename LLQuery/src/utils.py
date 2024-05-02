from box import Box  # Python dictionaries with advanced dot notation access.
import yaml


def load_config():
    with open(r"./config/config.yml", "r", encoding="utf8") as ymlfile:
        cfg = Box(yaml.safe_load(ymlfile))
        return cfg
