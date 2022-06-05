from asyncio import sleep
from datetime import datetime, timedelta
from re import search
from typing import Optional

from discord import Embed, Member, NotFound, Object
from discord.utils import find
from discord.ext.commands import Cog, Greedy, Converter
from discord.ext.commands import CheckFailure, BadArgument
from discord.ext.commands import command, bot_has_permissions, has_any_role

from ..db import db


class Mod(Cog):
    def __init__(self, Bot):
        self.Bot = Bot

    @command(name="clear", aliases=["purge"], brief="clear:")
    @bot_has_permissions(administrator=True)
    @has_any_role('admin', 'moderator')
    async def clear_messages(self, ctx, targets: Greedy[Member], limit: Optional[int] = 1):
        def _check(message):
            return not len(targets) or message.author in targets

        if 0 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit, after=datetime.utcnow() - timedelta(days=14),
                                                  check=_check)
                embed = Embed(title="Сhat cleared successfully.",
                              colour=0x8c46e2,
                              description=f"``Deleted messages:{len(deleted):,}``",
                              timestamp=datetime.utcnow())
                await ctx.send(embed=embed, delete_after=5)

        else:
            await ctx.message.delete()
            await ctx.send("The limit provided is not within acceptable bounds.", delete_after=5)

    @command(name="mute", brief="mute:")
    @bot_has_permissions(administrator=True)
    @has_any_role('admin', 'moderator')
    async def mute_command(self, ctx, targets: Greedy[Member], times: Optional[int], *,
                           reason: Optional[str] = "No reason provided."):
        await ctx.message.delete()
        if not len(targets):
            await ctx.send("One or more required arguments are missing.")

        else:
            unmutes = await self.mute_members(ctx.message, targets, times, reason)
            await ctx.send("Action complete.", delete_after=5)

            if len(unmutes):
                await sleep(times)
                await self.unmute_members(ctx.guild, targets)

    async def mute_members(self, message, targets, times, reason):
        unmutes = []

        for target in targets:
            if not self.mute_role in target.roles:
                if message.guild.me.top_role.position > target.top_role.position:
                    role_ids = ",".join([str(r.id) for r in target.roles])
                    end_time = datetime.utcnow() - timedelta(seconds=times) if times else None

                    db.execute("INSERT INTO mutes VALUES (?, ?, ?)",
                               target.id, role_ids, getattr(end_time, "isoformat", lambda: None)())

                    await target.edit(roles=[self.mute_role])

                    embed = Embed(title="Member muted",
                                  colour=0x8c46e2,
                                  timestamp=datetime.utcnow())

                    embed.set_thumbnail(url=target.avatar_url)

                    fields = [("Member", target.display_name, False),
                              ("Actioned by", message.author.display_name, False),
                              ("Duration", f"{times:,} second(s)" if times else "Indefinite", False),
                              ("Reason", reason, False)]

                    for name, value, inline in fields:
                        embed.add_field(name=name, value=value, inline=inline)

                    await self.log_channel.send(embed=embed)

                    if times:
                        unmutes.append(target)

        return unmutes

    @mute_command.error
    async def mute_command_error(self, ctx, exc):
        if isinstance(exc, CheckFailure):
            await ctx.send("Insufficient permissions to perform that task.", delete_after=10)

    async def unmute_members(self, guild, targets, *, reason="Mute time expired."):
        for target in targets:
            if self.mute_role in target.roles:
                role_ids = db.field("SELECT RoleIds FROM mutes WHERE UserId = ?", target.id)
                roles = [guild.get_role(int(id_)) for id_ in role_ids.split(",") if len(id_)]

                db.execute("DELETE FROM mutes WHERE UserId = ?", target.id)

                await target.edit(roles=roles)

                embed = Embed(title="Member unmuted",
                              colour=0x8c46e2,
                              timestamp=datetime.utcnow())

                embed.set_thumbnail(url=target.avatar_url)

                fields = [("Member", target.display_name, False),
                          ("Reason", reason, False)]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                await self.log_channel.send(embed=embed)

    @command(name="unmute", brief="unmute:")
    @bot_has_permissions(administrator=True)
    @has_any_role('admin', 'moderator')
    async def unmute_command(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
        await ctx.message.delete()
        if not len(targets):
            await ctx.send("One or more required arguments is missing.", delete_after=10)

        else:
            await self.unmute_members(ctx.guild, targets, reason=reason)

    @Cog.listener()
    async def on_ready(self):
        if not self.Bot.ready:
            self.log_channel = self.Bot.get_channel(795121999068135449)
            self.mute_role = self.Bot.guild.get_role(840383889846566924)

            self.Bot.cogs_ready.ready_up("moderation")


def setup(Bot):
    Bot.add_cog(Mod(Bot))