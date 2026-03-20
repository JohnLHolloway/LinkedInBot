import asyncio
import logging

import discord
from discord.ext import commands

from config import DISCORD_BOT_TOKEN, ALLOWED_GUILD_IDS, setup_logging

setup_logging()
log = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "commands.generation",
]


@bot.event
async def on_ready() -> None:
    await bot.tree.sync()
    log.info("Logged in as %s (guilds: %d)", bot.user, len(bot.guilds))


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    if ALLOWED_GUILD_IDS and guild.id not in ALLOWED_GUILD_IDS:
        log.info("Leaving non-allowed guild %s (%s)", guild.name, guild.id)
        await guild.leave()


async def main() -> None:
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            log.info("Loaded cog: %s", cog)
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
