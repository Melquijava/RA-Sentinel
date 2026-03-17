import os
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from core.antispam import SpamHit
from utils.timeutils import now_ts, human_ts


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}  # guild_id -> user_id -> datetime entrada UTC

    async def cog_load(self):
        for guild in self.bot.guilds:
            self.bot.get_cfg(guild.id)
            self.bot.warning_manager._get_guild_data(guild.id)
            self.bot.antispam.load_state(guild.id)
            self.voice_states.setdefault(guild.id, {})

    @commands.Cog.listener()
    async def on_ready(self):
        status = os.getenv("BOT_STATUS", "Protegendo servidores com RA Sentinel")
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=status)
        )

        print(f"✅ Logado como {self.bot.user}")
        print(f"✅ Em {len(self.bot.guilds)} servidores")
        await self.bot.sync_commands()

        for guild in self.bot.guilds:
            self.voice_states.setdefault(guild.id, {})

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.get_cfg(guild.id)
        self.bot.warning_manager._get_guild_data(guild.id)
        self.bot.antispam.load_state(guild.id)
        self.voice_states.setdefault(guild.id, {})

    # =========================================================
    # MEMBER JOIN
    # =========================================================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = self.bot.get_cfg(member.guild.id)

        welcome_channel_id = cfg.get("welcome_channel_id")
        if welcome_channel_id:
            channel = member.guild.get_channel(welcome_channel_id)
            if isinstance(channel, discord.TextChannel):
                embed = discord.Embed(
                    title=f"👋 Bem-vindo(a), {member.name}!",
                    description=(
                        "Sinta-se em casa no servidor **RA Corporation**! 🚀\n\n"
                        "Apresente-se e mostre quem você é!"
                    ),
                    color=discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )

                embed.set_thumbnail(
                    url=member.display_avatar.url if member.display_avatar else member.default_avatar.url
                )

                # Troque essa URL pela arte/banner oficial da RA Corporation
                embed.set_image(url="https://i.imgur.com/kJEVaa8.png")

                embed.set_footer(text="Seu crescimento começa agora • RA Corporation")

                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass

        await self.bot.send_log(
        member.guild,
        "📥 Membro entrou",
        f"**Membro:** {member} (`{member.id}`)\n**Quando:** {human_ts(now_ts())}",
        color=0x3498DB
    )

    # =========================================================
    # MEMBER REMOVE
    # =========================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        cfg = self.bot.get_cfg(member.guild.id)

        leave_channel_id = cfg.get("leave_channel_id")
        if leave_channel_id:
            channel = member.guild.get_channel(leave_channel_id)

            data_entrada = member.joined_at
            data_saida = datetime.now(timezone.utc)

            if data_entrada:
                tempo_total = data_saida - data_entrada
                dias_totais = tempo_total.days
                meses = dias_totais // 30
                dias = dias_totais % 30
                permanencia = f"{meses} mês(es) e {dias} dia(s)"
            else:
                permanencia = "Não disponível"

            nome_username = member.global_name if member.global_name else member.name

            embed = discord.Embed(
                title="⚠️ Membro saiu do servidor",
                color=discord.Color.red(),
                timestamp=data_saida
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Nome de exibição", value=member.display_name, inline=True)
            embed.add_field(name="🔒 Nome username", value=nome_username, inline=True)
            embed.add_field(name="🆔 ID do usuário", value=f"`{member.id}`", inline=False)
            embed.add_field(name="⏱️ Tempo no servidor", value=permanencia, inline=False)
            embed.set_footer(text="Monitoramento automático • RA Corporation")

            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass

        await self.bot.send_log(
            member.guild,
            "📤 Membro saiu",
            f"**Membro:** {member} (`{member.id}`)\n**Quando:** {human_ts(now_ts())}",
            color=0x95A5A6
        )

    # =========================================================
    # VOICE STATE UPDATE
    # =========================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        guild = member.guild
        cfg = self.bot.get_cfg(guild.id)
        voice_log_channel_id = cfg.get("voice_log_channel_id")

        if not voice_log_channel_id:
            return

        log_channel = guild.get_channel(voice_log_channel_id)
        if not isinstance(log_channel, discord.TextChannel):
            return

        guild_voice_states = self.voice_states.setdefault(guild.id, {})

        # Entrou em call
        if before.channel is None and after.channel is not None:
            guild_voice_states[member.id] = datetime.now(timezone.utc)

            embed_entrada = discord.Embed(
                title="🟢 Registro de Entrada em Voz",
                description=(
                    f"✅ **{member.display_name}** entrou no canal de voz **{after.channel.name}**."
                ),
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed_entrada.set_thumbnail(url=member.display_avatar.url)
            embed_entrada.set_footer(text=f"RA Corporation • ID do Usuário: {member.id}")

            try:
                await log_channel.send(embed=embed_entrada)
            except Exception:
                pass
            return

        # Saiu da call
        if before.channel is not None and after.channel is None:
            if member.id in guild_voice_states:
                entrada_dt = guild_voice_states.pop(member.id)
                saida_dt = datetime.now(timezone.utc)
                duracao = saida_dt - entrada_dt

                fuso_horario_br = timezone(timedelta(hours=-3))
                horario_entrada_str = entrada_dt.astimezone(fuso_horario_br).strftime('%H:%M:%S')
                horario_saida_str = saida_dt.astimezone(fuso_horario_br).strftime('%H:%M:%S')

                total_seconds = int(duracao.total_seconds())
                horas, remainder = divmod(total_seconds, 3600)
                minutos, segundos = divmod(remainder, 60)

                descricao_saida = (
                    f"| 🧑 **Nome**: {member.display_name}\n"
                    f"| 🎧 **Canal**: {before.channel.name}\n"
                    f"| 🕒 **Entrada**: {horario_entrada_str}\n"
                    f"| 🕒 **Saída**: {horario_saida_str}\n"
                    f"| ⌛ **Tempo total**: {horas}h {minutos}min {segundos}s"
                )

                embed_saida = discord.Embed(
                    title="🔴 Registro de Saída de Voz",
                    description=descricao_saida,
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed_saida.set_thumbnail(url=member.display_avatar.url)
                embed_saida.set_footer(text=f"RA Corporation • ID do Usuário: {member.id}")

                try:
                    await log_channel.send(embed=embed_saida)
                except Exception:
                    pass
            else:
                embed_simples = discord.Embed(
                    description=f"❌ **{member.display_name}** saiu do canal **{before.channel.name}** (tempo não rastreado).",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                embed_simples.set_footer(text=f"RA Corporation • ID do Usuário: {member.id}")

                try:
                    await log_channel.send(embed=embed_simples)
                except Exception:
                    pass
            return

        # Mudou de canal
        if before.channel is not None and after.channel is not None and before.channel != after.channel:
            if member.id not in guild_voice_states:
                guild_voice_states[member.id] = datetime.now(timezone.utc)

            embed_move = discord.Embed(
                title="🔄 Mudança de Canal de Voz",
                description=(
                    f"**{member.display_name}** mudou de **{before.channel.name}** para **{after.channel.name}**."
                ),
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed_move.set_thumbnail(url=member.display_avatar.url)
            embed_move.set_footer(text=f"RA Corporation • ID do Usuário: {member.id}")

            try:
                await log_channel.send(embed=embed_move)
            except Exception:
                pass

    # =========================================================
    # ANTI-SPAM
    # =========================================================
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