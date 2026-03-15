import os
from datetime import timedelta

import discord
from discord.ext import commands

from core.antispam import SpamHit
from utils.timeutils import now_ts, human_ts


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        for guild in self.bot.guilds:
            self.bot.get_cfg(guild.id)
            self.bot.warning_manager._get_guild_data(guild.id)
            self.bot.antispam.load_state(guild.id)

    @commands.Cog.listener()
    async def on_ready(self):
        status = os.getenv("BOT_STATUS", "Protegendo servidores com RA Sentinel")
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=status)
        )

        print(f"✅ Logado como {self.bot.user}")
        print(f"✅ Em {len(self.bot.guilds)} servidores")
        await self.bot.sync_commands()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.get_cfg(guild.id)
        self.bot.warning_manager._get_guild_data(guild.id)
        self.bot.antispam.load_state(guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = self.bot.get_cfg(member.guild.id)
        channel_id = cfg.get("welcome_channel_id")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(f"👋 Bem-vindo(a), {member.mention}, ao servidor **{member.guild.name}**!")
                except Exception:
                    pass

        await self.bot.send_log(
            member.guild,
            "📥 Membro entrou",
            f"**Membro:** {member} (`{member.id}`)\n**Quando:** {human_ts(now_ts())}",
            color=0x3498DB
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.send_log(
            member.guild,
            "📤 Membro saiu",
            f"**Membro:** {member} (`{member.id}`)\n**Quando:** {human_ts(now_ts())}",
            color=0x95A5A6
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if isinstance(message.author, discord.Member) and message.author.bot:
            return

        cfg = self.bot.get_cfg(message.guild.id)
        hit = self.bot.antispam.check_message(cfg, message)

        if hit:
            await self.handle_spam_hit(message, hit)

        self.bot.antispam.persist_state(message.guild.id)

    async def handle_spam_hit(self, message: discord.Message, hit: SpamHit):
        guild = message.guild
        member = message.author

        if not guild or not isinstance(member, discord.Member):
            return

        cfg = self.bot.get_cfg(guild.id)
        asp = cfg["antispam"]

        try:
            await message.delete()
        except Exception:
            pass

        strikes = self.bot.antispam.add_strike(guild.id, member.id)

        mod_id = self.bot.user.id if self.bot.user else 0
        self.bot.warning_manager.add(guild.id, member.id, mod_id, f"[AntiSpam] {hit.reason} — {hit.detail}")

        await self.bot.send_log(
            guild,
            "🚨 Anti-Spam Detectado",
            f"**Autor:** {member} (`{member.id}`)\n"
            f"**Canal:** {message.channel.mention}\n"
            f"**Motivo:** `{hit.reason}`\n"
            f"**Detalhe:** {hit.detail}\n"
            f"**Strikes:** `{strikes}`\n"
            f"**Quando:** {human_ts(now_ts())}",
            color=0xE74C3C,
            fields=[
                (
                    "Conteúdo (amostra)",
                    (message.content[:900] + "…") if message.content and len(message.content) > 900 else (message.content or "*sem texto*"),
                    False
                )
            ]
        )

        try:
            if strikes >= 2 and int(asp.get("action_timeout_seconds", 0)) > 0:
                seconds = int(asp["action_timeout_seconds"])
                until = discord.utils.utcnow() + timedelta(seconds=seconds)
                await member.timeout(until, reason=f"AntiSpam: {hit.reason}")

            if strikes >= 3 and asp.get("action_kick", False):
                await member.kick(reason=f"AntiSpam: {hit.reason}")

            if strikes >= 4 and asp.get("action_ban", False):
                await member.ban(reason=f"AntiSpam: {hit.reason}", delete_message_days=0)

        except discord.Forbidden:
            pass
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(EventsCog(bot))