from discord import Intents

from datetime import datetime
from glob import glob
from asyncio import sleep

from discord import Embed
from discord.errors import Forbidden
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import when_mentioned_or
from discord.ext.commands import (CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown)


from ..db import db

OWNER = [516682493152329729]
COGS = [path.split("/")[-1][:-3] for path in glob("./lib/cogs/*.py")]
#When booting to Heroku: [path.split("\\")[-1][:-3]
#              replace by [path.split("/")[-1][:-3]
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)


def get_prefix(Bot, message):
    prefix = db.field("SELECT Prefix FROM guilds WHERE GuildID = ?", message.guild.id)
    return when_mentioned_or(prefix)(Bot, message)


class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f" {cog} cog ready!")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


class Bot(BotBase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)

        super().__init__(
            owner_id=OWNER,
            intents=Intents.all(),
            command_prefix=get_prefix,
        )

    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f" {cog} cog loaded.")

        print("Setup complete.")

    def update_db(self):
        db.multiexec("INSERT OR IGNORE INTO guilds (GuildID) VALUES (?)",
                     ((guild.id,) for guild in self.guilds))

        db.multiexec("INSERT OR IGNORE INTO main (UserId) VALUES (?)",
                     ((member.id,) for member in self.guild.members if not member.bot))

        to_remove = []
        stored_members = db.column("SELECT UserId FROM main")
        for id_ in stored_members:
            if not self.guild.get_member(id_):
                to_remove.append(id_)

        db.multiexec("DELETE FROM main WHERE UserId = ?",
                     ((id_,) for id_ in to_remove))

        db.commit()

    def run(self, created):
        self.CREATED = created

        print("Running setup...")
        self.setup()

        with open("./lib/bot/token", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()

        print("\nRunning bot...")
        super().run(self.TOKEN, reconnect=True)

    async def on_connect(self):
        print("\nBot connected.\n")

    async def on_disconnect(self):
        print("\nBot disconnected.")

    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("**Something went wrong.**",  delete_after=10)

        await self.chatbot.send("**An error occured.**",  delete_after=10)
        raise

    async def on_command_error(self, ctx, exc):
        if any([isinstance(exc, error) for error in IGNORE_EXCEPTIONS]):
            pass

        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.",  delete_after=10)

        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(
                f"That command is on {str(exc.cooldown.type).split('.')[-1]} cooldown. Try again in {exc.retry_after:,.2f} secs.",  delete_after=10)

        elif hasattr(exc, "original"):
            if isinstance(exc.original, Forbidden):
                await ctx.send("I do not have permission to do that.",  delete_after=10)

            else:
                raise exc.original

        else:
            raise exc

    async def on_ready(self):
        if not self.ready:
            self.chatbot = self.get_channel(795121999068135449)
            self.guild = self.get_guild(795114731920687135)
            self.scheduler.start()
            self.update_db()

            embed = Embed(color=0x8c46e2, title='Hi!', description='**Bot is now online.**',
                          timestamp=datetime.utcnow()
                          )
            embed.set_author(name='yogurt', icon_url=self.guild.icon_url)

            await self.chatbot.send(embed=embed)

            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            self.ready = True
            print("\nBot ready.\n")

            meta = self.get_cog("Meta")
            await meta.set()

        else:
            print("\nBot reconnected.\n")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)


Bot = Bot()
