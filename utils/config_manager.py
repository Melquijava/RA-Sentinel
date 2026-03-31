from typing import Dict, Any
from utils.storage import ensure_guild_dir, guild_config_file, load_json, save_json, deep_merge

DEFAULT_GUILD_CONFIG = {
    "log_channel_id": None,
    "welcome_channel_id": None,
    "leave_channel_id": None,
    "voice_log_channel_id": None,
    "staff_category_id": None,
    "welcome_image_url": None,
    "moderation": {
        "require_reason": False
    },
    "antispam": {
        "enabled": True,
        "flood_max_msgs": 6,
        "flood_window_sec": 6,
        "block_suspicious_links": True,
        "whitelist_domains": ["discord.com", "discord.gg", "github.com"],
        "max_mentions": 6,
        "block_everyone_here": True,
        "caps_enabled": True,
        "caps_min_len": 20,
        "caps_ratio": 0.75,
        "action_warn": True,
        "action_timeout_seconds": 600,
        "action_kick": False,
        "action_ban": False,
        "ignored_channels": [],
        "ignored_roles": []
    }
}


class ConfigManager:
    def __init__(self):
        self.cache: Dict[int, Dict[str, Any]] = {}

    def get(self, guild_id: int) -> Dict[str, Any]:
        if guild_id not in self.cache:
            ensure_guild_dir(guild_id)
            path = guild_config_file(guild_id)

            existing = load_json(path, None)

            if existing is None:
                merged = DEFAULT_GUILD_CONFIG.copy()
                save_json(path, merged)
            else:
                merged = deep_merge(DEFAULT_GUILD_CONFIG, existing)

                # Só salva se realmente precisou adicionar campos novos
                if merged != existing:
                    save_json(path, merged)

            self.cache[guild_id] = merged

        return self.cache[guild_id]

    def save(self, guild_id: int):
        cfg = self.get(guild_id)
        save_json(guild_config_file(guild_id), cfg)