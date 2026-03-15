from typing import Dict, Any, List
from utils.storage import ensure_guild_dir, guild_warnings_file, load_json, save_json
from utils.timeutils import now_ts


class WarningManager:
    def __init__(self):
        self.cache: Dict[int, Dict[str, Any]] = {}

    def _get_guild_data(self, guild_id: int) -> Dict[str, Any]:
        if guild_id not in self.cache:
            ensure_guild_dir(guild_id)
            self.cache[guild_id] = load_json(guild_warnings_file(guild_id), {})
        return self.cache[guild_id]

    def add(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        data = self._get_guild_data(guild_id)
        key = str(user_id)
        warnings = data.get(key, [])
        warnings.append({
            "ts": now_ts(),
            "mod": moderator_id,
            "reason": reason
        })
        data[key] = warnings
        save_json(guild_warnings_file(guild_id), data)

    def get(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        data = self._get_guild_data(guild_id)
        return data.get(str(user_id), [])

    def clear(self, guild_id: int, user_id: int):
        data = self._get_guild_data(guild_id)
        if str(user_id) in data:
            del data[str(user_id)]
            save_json(guild_warnings_file(guild_id), data)