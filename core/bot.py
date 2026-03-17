import discord
from discord.ext import commands

from utils.storage import ensure_base_dirs
from utils.config_manager import ConfigManager
from utils.warning_manager import WarningManager
from core.antispam import AntiSpamManager


class RASentinel(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True
        intents.voice_states = True

        super().__init__(command_prefix="!", intents=intents)

        ensure_base_dirs()

        self.config_manager = ConfigManager()
        self.warning_manager = WarningManager()
        self.antispam = AntiSpamManager(self)

    async def setup_hook(self):
        extensions = (
            "cogs.help",
            "cogs.setup",
            "cogs.config",
            "cogs.moderation",
            "cogs.events",
        )
        for ext in extensions:
            await self.load_extension(ext)

    async def sync_commands(self):
        synced = await self.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados")

    def get_cfg(self, guild_id: int):
        return self.config_manager.get(guild_id)

    def save_cfg(self, guild_id: int):
        self.config_manager.save(guild_id)

    async def send_log(self, guild: discord.Guild, title: str, description: str, color: int | None = None, fields=None):
        cfg = self.get_cfg(guild.id)
        channel_id = cfg.get("log_channel_id")
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception:
                return

        embed = discord.Embed(
            title=title,
            description=description,
            color=color or discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        try:
            await channel.send(embed=embed)
        except Exception:
            pass