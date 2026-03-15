import discord
from discord import app_commands


def is_staff(interaction: discord.Interaction) -> bool:
    if not interaction.user or not isinstance(interaction.user, discord.Member):
        return False

    perms = interaction.user.guild_permissions
    return (
        perms.administrator
        or perms.ban_members
        or perms.kick_members
        or perms.manage_messages
        or perms.moderate_members
        or perms.manage_guild
    )


def require_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        return is_staff(interaction)
    return app_commands.check(predicate)