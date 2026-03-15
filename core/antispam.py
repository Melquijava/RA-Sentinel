import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import discord

from utils.storage import ensure_guild_dir, guild_antispam_file, load_json, save_json


@dataclass
class SpamHit:
    reason: str
    detail: str


class AntiSpamManager:
    def __init__(self, bot):
        self.bot = bot
        self.msg_times: Dict[int, Dict[int, List[int]]] = {}
        self.strikes: Dict[int, Dict[int, int]] = {}
        self.last_persist: Dict[int, float] = {}

    def _ensure_maps(self, guild_id: int):
        self.msg_times.setdefault(guild_id, {})
        self.strikes.setdefault(guild_id, {})
        self.last_persist.setdefault(guild_id, 0.0)

    def load_state(self, guild_id: int):
        self._ensure_maps(guild_id)
        ensure_guild_dir(guild_id)
        data = load_json(guild_antispam_file(guild_id), {"strikes": {}})
        self.strikes[guild_id] = {
            int(k): int(v) for k, v in data.get("strikes", {}).items()
        }

    def persist_state(self, guild_id: int, force: bool = False):
        self._ensure_maps(guild_id)
        now = time.time()
        if not force and (now - self.last_persist[guild_id]) < 30:
            return

        self.last_persist[guild_id] = now
        save_json(
            guild_antispam_file(guild_id),
            {"strikes": {str(k): v for k, v in self.strikes[guild_id].items()}}
        )

    def add_strike(self, guild_id: int, user_id: int) -> int:
        self._ensure_maps(guild_id)
        self.strikes[guild_id][user_id] = self.strikes[guild_id].get(user_id, 0) + 1
        return self.strikes[guild_id][user_id]

    def is_ignored(self, guild_cfg: dict, channel_id: int, member: discord.Member) -> bool:
        asp = guild_cfg["antispam"]
        if channel_id in asp.get("ignored_channels", []):
            return True
        for role in member.roles:
            if role.id in asp.get("ignored_roles", []):
                return True
        return False

    def check_message(self, guild_cfg: dict, message: discord.Message) -> Optional[SpamHit]:
        asp = guild_cfg["antispam"]

        if not asp.get("enabled", True):
            return None
        if not message.guild:
            return None
        if not isinstance(message.author, discord.Member):
            return None
        if message.author.bot:
            return None
        if self.is_ignored(guild_cfg, message.channel.id, message.author):
            return None

        content = message.content or ""
        lowered = content.lower()

        if asp.get("block_everyone_here", True):
            if "@everyone" in content or "@here" in content:
                return SpamHit("Menção proibida", "Uso de @everyone/@here")

        max_mentions = int(asp.get("max_mentions", 6))
        mention_count = len(message.mentions) + len(message.role_mentions)
        if mention_count >= max_mentions:
            return SpamHit("Menções em massa", f"{mention_count} menções (limite {max_mentions - 1})")

        if asp.get("block_suspicious_links", True):
            if "http://" in lowered or "https://" in lowered or "www." in lowered:
                whitelist = set(d.lower() for d in asp.get("whitelist_domains", []))
                tokens = lowered.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ").split()
                domains = []

                for token in tokens:
                    t = token.strip(".,;:!\"'<>")
                    if "http://" in t or "https://" in t:
                        rest = t.split("://", 1)[1]
                        dom = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip(".,;:!\"'<>")
                        if dom:
                            domains.append(dom)
                    elif t.startswith("www."):
                        dom = t.split("/", 1)[0].strip(".,;:!\"'<>")
                        if dom:
                            domains.append(dom)

                for dom in domains:
                    allowed = any(dom == w or dom.endswith("." + w) for w in whitelist)
                    if not allowed:
                        return SpamHit("Link suspeito", f"Domínio não permitido: `{dom}`")

        if asp.get("caps_enabled", True):
            min_len = int(asp.get("caps_min_len", 20))
            ratio = float(asp.get("caps_ratio", 0.75))
            letters = [c for c in content if c.isalpha()]
            if len(letters) >= min_len:
                upper = sum(1 for c in letters if c.isupper())
                if letters and (upper / len(letters)) >= ratio:
                    return SpamHit("Caps excessivo", f"{upper}/{len(letters)} letras em maiúsculo")

        guild_id = message.guild.id
        self._ensure_maps(guild_id)

        uid = message.author.id
        tnow = int(time.time())
        window = int(asp.get("flood_window_sec", 6))
        max_msgs = int(asp.get("flood_max_msgs", 6))

        lst = self.msg_times[guild_id].get(uid, [])
        lst.append(tnow)
        lst = [t for t in lst if (tnow - t) <= window]
        self.msg_times[guild_id][uid] = lst

        if len(lst) >= max_msgs:
            return SpamHit("Flood", f"{len(lst)} msgs em {window}s (limite {max_msgs - 1})")

        return None