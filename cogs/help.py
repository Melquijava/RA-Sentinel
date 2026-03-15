import discord
from discord.ext import commands
from discord import app_commands


class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot

    @discord.ui.button(label="Moderação", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def moderation(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ Ajuda — Moderação",
            description=(
                "• `/ban`\n"
                "• `/unban`\n"
                "• `/kick`\n"
                "• `/timeout`\n"
                "• `/purge`\n"
                "• `/lock`\n"
                "• `/unlock`\n"
                "• `/slowmode`\n"
                "• `/warn`\n"
                "• `/warnings`\n"
                "• `/clearwarnings`\n"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Configuração", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def config(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ Ajuda — Configuração",
            description=(
                "• `/setup`\n"
                "• `/config show`\n"
                "• `/config logs`\n"
                "• `/config antispam_toggle`\n"
                "• `/config antispam_limits`\n"
                "• `/config antispam_actions`\n"
                "• `/config whitelist_add`\n"
                "• `/config whitelist_remove`\n"
                "• `/config ignore_channel_add`\n"
                "• `/config ignore_channel_remove`\n"
                "• `/config ignore_role_add`\n"
                "• `/config ignore_role_remove`\n"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Sobre", style=discord.ButtonStyle.success, emoji="ℹ️")
    async def about(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="ℹ️ RA Sentinel",
            description=(
                "**Bot multi-servidor de moderação e segurança**\n\n"
                f"• Latência: `{round(self.bot.latency * 1000)}ms`\n"
                f"• Servidores: `{len(self.bot.guilds)}`"
            ),
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Mostra o painel de ajuda do RA Sentinel.")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 RA Sentinel — Painel de Ajuda",
            description="Use os botões abaixo para navegar.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=HelpView(self.bot), ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))