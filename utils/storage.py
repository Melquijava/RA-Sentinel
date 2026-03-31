import shutil
import os
import json
from typing import Any

DATA_DIR = os.getenv("DATA_DIR", "./data")
GUILDS_DIR = os.path.join(DATA_DIR, "guilds")

def save_json(path: str, data: Any):
    if os.path.exists(path):
        backup_path = path + ".bak"
        try:
            shutil.copy2(path, backup_path)
        except Exception:
            pass

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def ensure_base_dirs():
    os.makedirs(GUILDS_DIR, exist_ok=True)


def ensure_guild_dir(guild_id: int):
    os.makedirs(os.path.join(GUILDS_DIR, str(guild_id)), exist_ok=True)


def guild_dir(guild_id: int) -> str:
    return os.path.join(GUILDS_DIR, str(guild_id))


def guild_config_file(guild_id: int) -> str:
    return os.path.join(guild_dir(guild_id), "config.json")


def guild_warnings_file(guild_id: int) -> str:
    return os.path.join(guild_dir(guild_id), "warnings.json")


def guild_antispam_file(guild_id: int) -> str:
    return os.path.join(guild_dir(guild_id), "antispam_state.json")


def load_json(path: str, default: Any):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        try:
            os.rename(path, path + ".broken")
        except Exception:
            pass
        return default


def save_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out