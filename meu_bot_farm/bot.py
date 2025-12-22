import os
import discord
from discord.ext import commands
from config import BOT_PREFIX, TOKEN
from utils.logger import setup_logger

def start_bot():
    setup_logger()

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

    # Carregar extensões
    EXTENSIONS = [
        "cogs.tickets",
        "cogs.farm",
        "cogs.cargos"
    ]

    for ext in EXTENSIONS:
        bot.load_extension(ext)

    @bot.event
    async def on_ready():
        print(f"Bot online como {bot.user} (ID: {bot.user.id})")

    bot.run(TOKEN)