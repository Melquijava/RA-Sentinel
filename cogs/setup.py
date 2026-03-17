import discord
from discord.ext import commands
from discord import app_commands

from core.checks import require_staff


class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, config_key: str, title: str, channel_types):
        super().__init__(
            placeholder=f"Selecione: {title}",
            min_values=1,
            max_values=1,
            channel_types=channel_types
        )
        self.bot = bot
        self.config_key = config_key
        self.title = title

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        channel = self.values[0]
        cfg = self.bot.get_cfg(interaction.guild.id)
        cfg[self.config_key] = channel.id
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(
            f"✅ {self.title} definido como {channel.mention}",
            ephemeral=True
        )


class ChannelSelectView(discord.ui.View):
    def __init__(self, bot, config_key: str, title: str, channel_types):
        super().__init__(timeout=120)
        self.add_item(ChannelSelect(bot, config_key, title, channel_types))


class IgnoredChannelsSelect(discord.ui.ChannelSelect):
    def __init__(self, bot):
        super().__init__(
            placeholder="Selecione os canais ignorados",
            min_values=0,
            max_values=25,
            channel_types=[discord.ChannelType.text]
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        cfg = self.bot.get_cfg(interaction.guild.id)
        cfg["antispam"]["ignored_channels"] = [c.id for c in self.values]
        self.bot.save_cfg(interaction.guild.id)

        canais = ", ".join(c.mention for c in self.values) if self.values else "nenhum"
        await interaction.response.send_message(f"✅ Canais ignorados atualizados: {canais}", ephemeral=True)


class IgnoredChannelsView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(IgnoredChannelsSelect(bot))


class IgnoredRolesSelect(discord.ui.RoleSelect):
    def __init__(self, bot):
        super().__init__(
            placeholder="Selecione os cargos ignorados",
            min_values=0,
            max_values=25
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso em um servidor.", ephemeral=True)

        cfg = self.bot.get_cfg(interaction.guild.id)
        cfg["antispam"]["ignored_roles"] = [r.id for r in self.values]
        self.bot.save_cfg(interaction.guild.id)

        cargos = ", ".join(r.mention for r in self.values) if self.values else "nenhum"
        await interaction.response.send_message(f"✅ Cargos ignorados atualizados: {cargos}", ephemeral=True)


class IgnoredRolesView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.add_item(IgnoredRolesSelect(bot))


class SetupMainView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
    @discord.ui.button(label="Canal de Saída", style=discord.ButtonStyle.primary, emoji="📤", custom_id="setup_leave")
    async def setup_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione o canal de saída:",
            view=ChannelSelectView(self.bot, "leave_channel_id", "Canal de Saída", [discord.ChannelType.text]),
            ephemeral=True
    )
        
    @discord.ui.button(label="Log de Voz", style=discord.ButtonStyle.secondary, emoji="🎙️", custom_id="setup_voice_log")
    async def setup_voice_log(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione o canal de logs de voz:",
            view=ChannelSelectView(self.bot, "voice_log_channel_id", "Log de Voz", [discord.ChannelType.text]),
            ephemeral=True
    )

    @discord.ui.button(label="Canal de Logs", style=discord.ButtonStyle.primary, emoji="📝", custom_id="setup_logs")
    async def setup_logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione o canal de logs:",
            view=ChannelSelectView(self.bot, "log_channel_id", "Canal de Logs", [discord.ChannelType.text]),
            ephemeral=True
        )

    @discord.ui.button(label="Canal de Boas-vindas", style=discord.ButtonStyle.primary, emoji="👋", custom_id="setup_welcome")
    async def setup_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione o canal de boas-vindas:",
            view=ChannelSelectView(self.bot, "welcome_channel_id", "Canal de Boas-vindas", [discord.ChannelType.text]),
            ephemeral=True
        )

    @discord.ui.button(label="Categoria Staff", style=discord.ButtonStyle.secondary, emoji="🛡️", custom_id="setup_staff_category")
    async def setup_staff_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione a categoria de staff:",
            view=ChannelSelectView(self.bot, "staff_category_id", "Categoria Staff", [discord.ChannelType.category]),
            ephemeral=True
        )

    @discord.ui.button(label="Canais Ignorados", style=discord.ButtonStyle.secondary, emoji="📵", custom_id="setup_ignored_channels")
    async def setup_ignored_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione os canais ignorados no anti-spam:",
            view=IgnoredChannelsView(self.bot),
            ephemeral=True
        )

    @discord.ui.button(label="Cargos Ignorados", style=discord.ButtonStyle.secondary, emoji="🎭", custom_id="setup_ignored_roles")
    async def setup_ignored_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Selecione os cargos ignorados no anti-spam:",
            view=IgnoredRolesView(self.bot),
            ephemeral=True
        )

    @discord.ui.button(label="Anti-Spam ON/OFF", style=discord.ButtonStyle.success, emoji="🚫", custom_id="setup_antispam_toggle")
    async def toggle_antispam(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild:
            return await interaction.response.send_message("Use isso dentro de um servidor.", ephemeral=True)

        cfg = self.bot.get_cfg(interaction.guild.id)
        cfg["antispam"]["enabled"] = not cfg["antispam"].get("enabled", True)
        self.bot.save_cfg(interaction.guild.id)

        await interaction.response.send_message(
            f"✅ Anti-spam agora está `{ 'ON' if cfg['antispam']['enabled'] else 'OFF' }`",
            ephemeral=True
        )


class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(SetupMainView(bot))

    @app_commands.command(name="setup", description="Abre o painel de setup do bot.")
    @require_staff()
    async def setup_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ RA Sentinel — Setup",
            description=(
                "Configure este servidor pelos botões abaixo.\n\n"
                "• Canal de logs\n"
                "• Canal de boas-vindas\n"
                "• Canal de saída\n"
                "• Canal de logs de voz\n"
                "• Categoria staff\n"
                "• Canais ignorados\n"
                "• Cargos ignorados\n"
                "• Ligar/desligar anti-spam"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=SetupMainView(self.bot), ephemeral=True)


async def setup(bot):
    await bot.add_cog(SetupCog(bot))