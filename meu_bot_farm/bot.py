import discord
from discord.ext import commands
from meu_bot_farm.config import BOT_PREFIX
from meu_bot_farm.utils.logger import setup_logger

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

logger = setup_logger()

EXTENSIONS = [
    "meu_bot_farm.cogs.tickets",
    "meu_bot_farm.cogs.farm",
    "meu_bot_farm.cogs.cargos",
]

@bot.event
async def setup_hook():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            logger.info(f"Cog carregado: {ext}")
        except Exception as e:
            logger.error(f"Erro ao carregar {ext}: {e}")

@bot.event
async def on_ready():
    logger.info(f"Bot ON como {bot.user} (ID: {bot.user.id})")