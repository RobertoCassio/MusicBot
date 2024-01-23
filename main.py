import asyncio
import discord
from discord.ext import commands

with open("key", "r") as file:
    key = file.read().strip()

from music_cog import music_cog


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

async def main():
    async with bot:
        await bot.add_cog(music_cog(bot))
        await bot.start(key)


asyncio.run(main())
