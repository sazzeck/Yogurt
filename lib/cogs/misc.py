from discord.ext.commands import Cog
from discord.ext.commands import command, has_any_role
import discord

from ..db import db


class Misc(Cog):
    def __init__(self, Bot):
        self.Bot = Bot

    @Cog.listener()
    async def on_ready(self):
        if not self.Bot.ready:
            self.Bot.cogs_ready.ready_up("misc")

    @command(name="prefix", brief="prefix:")
    @has_any_role('admin', 'moderator')
    async def change_prefix(self, ctx, new: str):
        await ctx.message.delete()

        """Allows you to change the prefix."""

        if len(new) > 2:
            embed = discord.Embed(color=0x8c46e2, description=f"**Prefix can't be more** `5` **characters in lenght**.")
            await ctx.send(embed=embed, delete_after=5)
        else:
            db.execute("UPDATE guilds SET Prefix = ? WHERE GuildID = ?", new, ctx.guild.id)
            embed = discord.Embed(color=0x8c46e2, description=f"**Prefix set to:** `{new}`")
            await ctx.send(embed=embed, delete_after=5)


def setup(Bot):
    Bot.add_cog(Misc(Bot))