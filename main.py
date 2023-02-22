import asyncio

import discord
from discord.ext import commands

from music_cog import music_cog

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)


async def main():
    async with bot:
        await bot.add_cog(music_cog(bot))
        await bot.start("MTA3NzM4NjI0OTQ5MDQxOTcxMg.G6v44t.p1AGjQthCgu_FxYwENYvFItuN8U_QwSoc8FWuU")


asyncio.run(main())