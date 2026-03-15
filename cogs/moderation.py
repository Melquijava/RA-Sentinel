from datetime import timedelta

import discord
from discord.ext import commands
from discord import app_commands

from core.checks import require_staff
from utils.timeutils import now_ts, human_ts


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bane um membro do servidor.")
    @require_staff()
    @app_commands.describe(membro="Membro a ser banido", motivo="Motivo", apagar_mensagens="Apagar msgs dos últimos 0-7 dias")
    async def ban_cmd(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str | None = None,
        apagar_mensagens: app_commands.Range[int, 0, 7] = 0
    ):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        if membro == interaction.user:
            return await interaction.response.send_message("Você não pode banir você mesmo.", ephemeral=True)

        if membro.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Você não pode banir alguém com cargo igual/maior que o seu.", ephemeral=True)

        reason = motivo or "Sem motivo informado"

        try:
            await membro.ban(reason=reason, delete_message_days=apagar_mensagens)
            await interaction.response.send_message(f"✅ {membro.mention} foi banido.", ephemeral=True)
            await self.bot.send_log(
                interaction.guild,
                "🔨 Ban",
                f"**Alvo:** {membro} (`{membro.id}`)\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Motivo:** `{reason}`\n**Quando:** {human_ts(now_ts())}",
                color=0xE74C3C
            )
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para banir este membro.", ephemeral=True)

    @app_commands.command(name="unban", description="Remove banimento por ID.")
    @require_staff()
    @app_commands.describe(user_id="ID do usuário banido", motivo="Motivo")
    async def unban_cmd(self, interaction: discord.Interaction, user_id: str, motivo: str | None = None):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        try:
            uid = int(user_id)
        except ValueError:
            return await interaction.response.send_message("ID inválido.", ephemeral=True)

        reason = motivo or "Sem motivo informado"

        try:
            bans = [entry async for entry in guild.bans(limit=2000)]
            target = next((b.user for b in bans if b.user.id == uid), None)

            if not target:
                return await interaction.response.send_message("Usuário não encontrado na lista de banidos.", ephemeral=True)

            await guild.unban(target, reason=reason)
            await interaction.response.send_message(f"✅ Usuário `{target}` foi desbanido.", ephemeral=True)

            await self.bot.send_log(
                guild,
                "✅ Unban",
                f"**Alvo:** {target} (`{uid}`)\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Motivo:** `{reason}`\n**Quando:** {human_ts(now_ts())}",
                color=0x2ECC71
            )
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para desbanir.", ephemeral=True)

    @app_commands.command(name="kick", description="Expulsa um membro do servidor.")
    @require_staff()
    @app_commands.describe(membro="Membro a ser expulso", motivo="Motivo")
    async def kick_cmd(self, interaction: discord.Interaction, membro: discord.Member, motivo: str | None = None):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        if membro == interaction.user:
            return await interaction.response.send_message("Você não pode expulsar você mesmo.", ephemeral=True)

        if membro.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Você não pode expulsar alguém com cargo igual/maior que o seu.", ephemeral=True)

        reason = motivo or "Sem motivo informado"

        try:
            await membro.kick(reason=reason)
            await interaction.response.send_message(f"✅ {membro.mention} foi expulso.", ephemeral=True)
            await self.bot.send_log(
                interaction.guild,
                "👢 Kick",
                f"**Alvo:** {membro} (`{membro.id}`)\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Motivo:** `{reason}`\n**Quando:** {human_ts(now_ts())}",
                color=0xF39C12
            )
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para expulsar este membro.", ephemeral=True)

    @app_commands.command(name="timeout", description="Aplica timeout em um membro.")
    @require_staff()
    @app_commands.describe(membro="Membro alvo", minutos="Duração em minutos", motivo="Motivo")
    async def timeout_cmd(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        minutos: app_commands.Range[int, 1, 10080],
        motivo: str | None = None
    ):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        if membro == interaction.user:
            return await interaction.response.send_message("Você não pode aplicar timeout em você mesmo.", ephemeral=True)

        if membro.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Você não pode aplicar timeout em alguém com cargo igual/maior que o seu.", ephemeral=True)

        reason = motivo or "Sem motivo informado"
        until = discord.utils.utcnow() + timedelta(minutes=int(minutos))

        try:
            await membro.timeout(until, reason=reason)
            await interaction.response.send_message(f"✅ {membro.mention} recebeu timeout por `{minutos}` min.", ephemeral=True)
            await self.bot.send_log(
                interaction.guild,
                "⏳ Timeout",
                f"**Alvo:** {membro} (`{membro.id}`)\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Duração:** `{minutos} min`\n**Motivo:** `{reason}`\n**Quando:** {human_ts(now_ts())}",
                color=0x9B59B6
            )
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para aplicar timeout.", ephemeral=True)

    @app_commands.command(name="purge", description="Apaga mensagens do canal.")
    @require_staff()
    @app_commands.describe(quantidade="Quantidade (1-200)", usuario="Filtrar por usuário")
    async def purge_cmd(
        self,
        interaction: discord.Interaction,
        quantidade: app_commands.Range[int, 1, 200],
        usuario: discord.Member | None = None
    ):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Esse comando só funciona em canais de texto.", ephemeral=True)

        await interaction.response.defer(ephemeral=True, thinking=True)

        def check(m: discord.Message):
            return True if usuario is None else m.author.id == usuario.id

        deleted = await channel.purge(limit=int(quantidade), check=check, bulk=True)
        await interaction.followup.send(f"🧹 Apaguei **{len(deleted)}** mensagens.", ephemeral=True)

        extra = f"\n**Filtro:** {usuario} (`{usuario.id}`)" if usuario else ""
        await self.bot.send_log(
            interaction.guild,
            "🧹 Purge",
            f"**Canal:** {channel.mention}\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Solicitado:** `{quantidade}`\n**Deletadas:** `{len(deleted)}`{extra}\n**Quando:** {human_ts(now_ts())}",
            color=0x3498DB
        )

    @app_commands.command(name="lock", description="Trava o canal atual.")
    @require_staff()
    async def lock_cmd(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Esse comando só funciona em canais de texto.", ephemeral=True)

        overwrites = channel.overwrites_for(interaction.guild.default_role)
        overwrites.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)

        await interaction.response.send_message(f"🔒 Canal {channel.mention} travado.", ephemeral=True)
        await self.bot.send_log(
            interaction.guild,
            "🔒 Lock",
            f"**Canal:** {channel.mention}\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Quando:** {human_ts(now_ts())}",
            color=0x95A5A6
        )

    @app_commands.command(name="unlock", description="Destrava o canal atual.")
    @require_staff()
    async def unlock_cmd(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Esse comando só funciona em canais de texto.", ephemeral=True)

        overwrites = channel.overwrites_for(interaction.guild.default_role)
        overwrites.send_messages = None
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)

        await interaction.response.send_message(f"🔓 Canal {channel.mention} destravado.", ephemeral=True)
        await self.bot.send_log(
            interaction.guild,
            "🔓 Unlock",
            f"**Canal:** {channel.mention}\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Quando:** {human_ts(now_ts())}",
            color=0x2ECC71
        )

    @app_commands.command(name="slowmode", description="Define o slowmode do canal atual.")
    @require_staff()
    @app_commands.describe(segundos="0 desativa, máximo 21600")
    async def slowmode_cmd(self, interaction: discord.Interaction, segundos: app_commands.Range[int, 0, 21600]):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Esse comando só funciona em canais de texto.", ephemeral=True)

        await channel.edit(slowmode_delay=int(segundos))
        await interaction.response.send_message(f"⏱️ Slowmode definido para `{segundos}s`.", ephemeral=True)
        await self.bot.send_log(
            interaction.guild,
            "⏱️ Slowmode",
            f"**Canal:** {channel.mention}\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Delay:** `{segundos}s`\n**Quando:** {human_ts(now_ts())}",
            color=0x1ABC9C
        )

    @app_commands.command(name="warn", description="Aplica warn em um membro.")
    @require_staff()
    @app_commands.describe(membro="Membro alvo", motivo="Motivo do warn")
    async def warn_cmd(self, interaction: discord.Interaction, membro: discord.Member, motivo: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        self.bot.warning_manager.add(interaction.guild.id, membro.id, interaction.user.id, motivo)
        total = len(self.bot.warning_manager.get(interaction.guild.id, membro.id))

        await interaction.response.send_message(f"⚠️ {membro.mention} recebeu WARN. Total: `{total}`", ephemeral=True)
        await self.bot.send_log(
            interaction.guild,
            "⚠️ Warn",
            f"**Alvo:** {membro} (`{membro.id}`)\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Motivo:** `{motivo}`\n**Total:** `{total}`\n**Quando:** {human_ts(now_ts())}",
            color=0xF1C40F
        )

    @app_commands.command(name="warnings", description="Mostra os warns de um membro.")
    @require_staff()
    @app_commands.describe(membro="Membro alvo")
    async def warnings_cmd(self, interaction: discord.Interaction, membro: discord.Member):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        warns = self.bot.warning_manager.get(interaction.guild.id, membro.id)
        if not warns:
            return await interaction.response.send_message(f"✅ {membro.mention} não possui warns.", ephemeral=True)

        lines = []
        start_idx = max(1, len(warns) - 9)
        for i, w in enumerate(warns[-10:], start=start_idx):
            lines.append(
                f"**#{i}** — {human_ts(int(w['ts']))}\n"
                f"• Mod: <@{w['mod']}>\n"
                f"• Motivo: `{w['reason']}`"
            )

        embed = discord.Embed(
            title=f"📋 Warns — {membro}",
            description="\n\n".join(lines),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Total: {len(warns)} (mostrando últimos 10)")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearwarnings", description="Limpa todos os warns de um membro.")
    @require_staff()
    @app_commands.describe(membro="Membro alvo")
    async def clearwarnings_cmd(self, interaction: discord.Interaction, membro: discord.Member):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        total = len(self.bot.warning_manager.get(interaction.guild.id, membro.id))
        self.bot.warning_manager.clear(interaction.guild.id, membro.id)

        await interaction.response.send_message(
            f"🧽 Warns de {membro.mention} foram limpos. Removidos: `{total}`",
            ephemeral=True
        )
        await self.bot.send_log(
            interaction.guild,
            "🧽 Clear Warnings",
            f"**Alvo:** {membro} (`{membro.id}`)\n**Por:** {interaction.user} (`{interaction.user.id}`)\n**Removidos:** `{total}`\n**Quando:** {human_ts(now_ts())}",
            color=0x95A5A6
        )


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))