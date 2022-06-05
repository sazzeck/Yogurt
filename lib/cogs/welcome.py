import discord
from discord.ext.commands import Cog
import datetime

from ..db import db


class Welcome(Cog):

    def __init__(self, Bot):
        self.Bot = Bot

    @Cog.listener()
    async def on_ready(self):
        if not self.Bot.ready:
            self.Bot.cogs_ready.ready_up("welcome")

    @Cog.listener()
    async def on_member_join(self, member):
        db.execute("INSERT INTO main (UserId) VALUES (?)", member.id)
        role = discord.utils.get(member.guild.roles, name='username')
        guild = self.Bot.get_guild(795114731920687135)
        channel = guild.get_channel(830110891747311676)

        embed = discord.Embed(color=0x8c46e2,
                              description=f'**Welcome to our family {member.mention}!**\n You are the **{len(list(member.guild.members))}** member on this server.')
        embed.set_thumbnail(url=f'{member.avatar_url}')
        embed.set_author(name=f'{member.name}', icon_url=f'{member.avatar_url}')
        embed.set_footer(text=f'{member.guild}', icon_url=f'{member.guild.icon_url}')
        embed.timestamp = datetime.datetime.utcnow()

        await member.add_roles(role)
        await channel.send(embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        db.execute("DELETE FROM main WHERE UserId = ?", member.id)
        guild = self.Bot.get_guild(795114731920687135)
        channel = guild.get_channel(830110891747311676)

        embed = discord.Embed(color=0x8c46e2, description=f'{member.mention} **left the server** :face_vomiting:')
        embed.set_thumbnail(url=f'{member.avatar_url}')
        embed.set_author(name=f'{member.name}', icon_url=f'{member.avatar_url}')
        embed.set_footer(text=f'{member.guild}', icon_url=f'{member.guild.icon_url}')
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)


def setup(Bot):
    Bot.add_cog(Welcome(Bot))