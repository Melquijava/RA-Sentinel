import discord
from discord.ext import commands
from discord import app_commands

from core.checks import require_staff


class ConfigGroup(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="config", description="Configurações do RA Sentinel")
        self.bot = bot

    @app_commands.command(name="show", description="Mostra a configuração atual.")
    @require_staff()
    async def show(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        cfg = self.bot.get_cfg(interaction.guild.id)
        asp = cfg["antispam"]

        embed = discord.Embed(
            title="⚙️ Configuração Atual",
            color=discord.Color.blurple()
        )

        logs_text = f"<#{cfg['log_channel_id']}>" if cfg.get("log_channel_id") else "`não definido`"
        welcome_text = f"<#{cfg['welcome_channel_id']}>" if cfg.get("welcome_channel_id") else "`não definido`"
        staff_text = f"<#{cfg['staff_category_id']}>" if cfg.get("staff_category_id") else "`não definida`"

        embed.add_field(
            name="Principais",
            value=(
                f"**Logs:** {logs_text}\n"
                f"**Boas-vindas:** {welcome_text}\n"
                f"**Categoria Staff:** {staff_text}"
            ),
            inline=False
        )

        embed.add_field(name="Anti-Spam", value="ON" if asp.get("enabled", True) else "OFF", inline=True)
        embed.add_field(name="Flood", value=f"{asp.get('flood_max_msgs')}/{asp.get('flood_window_sec')}s", inline=True)
        embed.add_field(name="Menções", value=str(asp.get("max_mentions")), inline=True)
        embed.add_field(name="Links", value="ON" if asp.get("block_suspicious_links", True) else "OFF", inline=True)
        embed.add_field(name="Caps", value="ON" if asp.get("caps_enabled", True) else "OFF", inline=True)
        embed.add_field(name="Timeout Auto", value=f"{asp.get('action_timeout_seconds')}s", inline=True)

        ignored_channels = asp.get("ignored_channels", [])
        ignored_roles = asp.get("ignored_roles", [])

        embed.add_field(
            name="Canais ignorados",
            value=", ".join(f"<#{cid}>" for cid in ignored_channels[:15]) if ignored_channels else "`nenhum`",
            inline=False
        )
        embed.add_field(
            name="Cargos ignorados",
            value=", ".join(f"<@&{rid}>" for rid in ignored_roles[:15]) if ignored_roles else "`nenhum`",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="logs", description="Define o canal de logs.")
    @require_staff()
    @app_commands.describe(canal="Canal de logs")
    async def logs(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        cfg = self.bot.get_cfg(interaction.guild.id)
        cfg["log_channel_id"] = canal.id
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Canal de logs definido para {canal.mention}", ephemeral=True)

    @app_commands.command(name="antispam_toggle", description="Liga ou desliga o anti-spam.")
    @require_staff()
    @app_commands.describe(estado="on ou off")
    async def antispam_toggle(self, interaction: discord.Interaction, estado: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        estado = estado.lower().strip()
        if estado not in ("on", "off"):
            return await interaction.response.send_message("Use `on` ou `off`.", ephemeral=True)

        cfg = self.bot.get_cfg(interaction.guild.id)
        cfg["antispam"]["enabled"] = (estado == "on")
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Anti-spam agora está `{estado.upper()}`", ephemeral=True)

    @app_commands.command(name="antispam_limits", description="Ajusta os limites do anti-spam.")
    @require_staff()
    @app_commands.describe(
        flood_max_msgs="Máx de msgs (3-20)",
        flood_window_sec="Janela em segundos (3-30)",
        max_mentions="Máx de menções (3-20)"
    )
    async def antispam_limits(
        self,
        interaction: discord.Interaction,
        flood_max_msgs: app_commands.Range[int, 3, 20],
        flood_window_sec: app_commands.Range[int, 3, 30],
        max_mentions: app_commands.Range[int, 3, 20]
    ):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        asp["flood_max_msgs"] = int(flood_max_msgs)
        asp["flood_window_sec"] = int(flood_window_sec)
        asp["max_mentions"] = int(max_mentions)
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message("✅ Limites do anti-spam atualizados.", ephemeral=True)

    @app_commands.command(name="antispam_actions", description="Configura ações automáticas do anti-spam.")
    @require_staff()
    @app_commands.describe(
        timeout_seconds="Timeout em segundos (0 desativa)",
        kick="Kick automático",
        ban="Ban automático"
    )
    async def antispam_actions(
        self,
        interaction: discord.Interaction,
        timeout_seconds: app_commands.Range[int, 0, 86400],
        kick: bool,
        ban: bool
    ):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        asp["action_timeout_seconds"] = int(timeout_seconds)
        asp["action_kick"] = bool(kick)
        asp["action_ban"] = bool(ban)
        asp["action_warn"] = True
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message("✅ Ações automáticas atualizadas.", ephemeral=True)

    @app_commands.command(name="whitelist_add", description="Adiciona domínio à whitelist.")
    @require_staff()
    @app_commands.describe(dominio="Ex: example.com")
    async def whitelist_add(self, interaction: discord.Interaction, dominio: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        dominio = dominio.lower().strip()
        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        wl = asp.get("whitelist_domains", [])

        if dominio in wl:
            return await interaction.response.send_message("Esse domínio já está na whitelist.", ephemeral=True)

        wl.append(dominio)
        asp["whitelist_domains"] = wl
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Domínio `{dominio}` adicionado.", ephemeral=True)

    @app_commands.command(name="whitelist_remove", description="Remove domínio da whitelist.")
    @require_staff()
    @app_commands.describe(dominio="Ex: example.com")
    async def whitelist_remove(self, interaction: discord.Interaction, dominio: str):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        dominio = dominio.lower().strip()
        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        wl = asp.get("whitelist_domains", [])

        if dominio not in wl:
            return await interaction.response.send_message("Esse domínio não está na whitelist.", ephemeral=True)

        wl.remove(dominio)
        asp["whitelist_domains"] = wl
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Domínio `{dominio}` removido.", ephemeral=True)

    @app_commands.command(name="ignore_channel_add", description="Ignora um canal no anti-spam.")
    @require_staff()
    @app_commands.describe(canal="Canal a ignorar")
    async def ignore_channel_add(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        lst = asp.get("ignored_channels", [])
        if canal.id not in lst:
            lst.append(canal.id)
        asp["ignored_channels"] = lst
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Canal {canal.mention} ignorado no anti-spam.", ephemeral=True)

    @app_commands.command(name="ignore_channel_remove", description="Remove um canal da lista de ignorados.")
    @require_staff()
    @app_commands.describe(canal="Canal a remover")
    async def ignore_channel_remove(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        lst = asp.get("ignored_channels", [])
        if canal.id in lst:
            lst.remove(canal.id)
        asp["ignored_channels"] = lst
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Canal {canal.mention} removido dos ignorados.", ephemeral=True)

    @app_commands.command(name="ignore_role_add", description="Ignora um cargo no anti-spam.")
    @require_staff()
    @app_commands.describe(cargo="Cargo a ignorar")
    async def ignore_role_add(self, interaction: discord.Interaction, cargo: discord.Role):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        lst = asp.get("ignored_roles", [])
        if cargo.id not in lst:
            lst.append(cargo.id)
        asp["ignored_roles"] = lst
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Cargo {cargo.mention} ignorado no anti-spam.", ephemeral=True)

    @app_commands.command(name="ignore_role_remove", description="Remove um cargo da lista de ignorados.")
    @require_staff()
    @app_commands.describe(cargo="Cargo a remover")
    async def ignore_role_remove(self, interaction: discord.Interaction, cargo: discord.Role):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        asp = self.bot.get_cfg(interaction.guild.id)["antispam"]
        lst = asp.get("ignored_roles", [])
        if cargo.id in lst:
            lst.remove(cargo.id)
        asp["ignored_roles"] = lst
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(f"✅ Cargo {cargo.mention} removido dos ignorados.", ephemeral=True)


class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_group = ConfigGroup(bot)


async def setup(bot):
    cog = ConfigCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(cog.config_group)