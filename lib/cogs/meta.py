from datetime import datetime, timedelta
from platform import python_version
from time import time

from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType, Embed
from discord import __version__ as discord_version
from discord.ext.commands import Cog
from discord.ext.commands import command, has_any_role, is_owner
from psutil import Process, virtual_memory

from ..db import db


class Meta(Cog):
    def __init__(self, Bot):
        self.Bot = Bot
        self._message = "watching {prefix}help | {users:,} users in server."
        Bot.scheduler.add_job(self.set, CronTrigger(second=0))

    @property
    def message(self):
        prefix = db.field("SELECT Prefix FROM guilds")
        return self._message.format(users=len(self.Bot.users), prefix=prefix)

    @message.setter
    def message(self, value):
        if value.split(" ")[0] not in ("playing", "watching", "listening", "streaming"):
            raise ValueError("Invalid activity type.")

        self._message = value

    async def set(self):
        _type, _name = self.message.split(" ", maxsplit=1)

        await self.Bot.change_presence(activity=Activity(
            name=_name, type=getattr(ActivityType, _type, ActivityType.playing)
        ))

    @command(name="setactivity",
             brief="setactivity:",
             aliases=["sa", "activity"])
    @has_any_role('admin', 'moderator')
    async def set_activity_message(self, ctx, *, text: str):
        await ctx.message.delete()
        self.message = text
        await self.set()

    @command(name="ping", brief="ping:")
    async def ping(self, ctx):
        await ctx.message.delete()
        start = time()
        message = await ctx.send(f"Pong!\n DWSP latency: {self.Bot.latency * 1000:,.0f} ms.")
        end = time()

        await message.edit(
            content=f"Pong!\nDWSP latency: {self.Bot.latency * 1000:,.0f} ms.\nResponse time: {(end - start) * 1000:,.0f} ms.")

    @command(name="stats", brief="stats:")
    @has_any_role('admin', 'moderator')
    async def show_bot_stats(self, ctx):
        await ctx.message.delete()
        embed = Embed(title="Bot stats",
                      colour=ctx.author.colour,
                      thumbnail=self.Bot.user.avatar_url,
                      timestamp=datetime.utcnow())

        proc = Process()
        with proc.oneshot():
            uptime = timedelta(seconds=time() - proc.create_time())
            cpu_time = timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user)
            mem_total = virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100)

        fields = [
            ("Bot created:", self.Bot.CREATED, True),
            ("Python version:", python_version(), True),
            ("discord.py version:", discord_version, True),
            ("Uptime:", uptime, True),
            ("CPU time:", cpu_time, True),
            ("Memory usage:", f"{mem_usage:,.3f} / {mem_total:,.0f} MiB ({mem_of_total:.0f}%)", True),
            ("Users:", f"{self.Bot.guild.member_count:,}", True)
        ]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)

    @Cog.listener()
    async def on_ready(self):
        if not self.Bot.ready:
            self.Bot.cogs_ready.ready_up("meta")


def setup(Bot):
    Bot.add_cog(Meta(Bot))