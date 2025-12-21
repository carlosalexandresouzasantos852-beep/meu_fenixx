from meu_bot_farm.web import keep_alive
import asyncio
import discord
from discord.ext import commands

# ================== KEEP ALIVE ==================
keep_alive()  # Mantém o bot vivo no Render

# ================== INTENTS ==================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== COGS ==================
COGS = [
    "meu_bot_farm.kortefarm"  # Substitua pelo caminho do seu cog
]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[INFO] Cog carregado: {cog}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {cog}: {e}")

# ================== EVENTOS ==================
@bot.event
async def on_ready():
    print(f"\n[INFO] Bot conectado como {bot.user} (ID: {bot.user.id})")
    print("[INFO] Todas as funções carregadas e pronto para uso!")

# ================== EXECUÇÃO ==================
async def main():
    await load_cogs()
    await bot.start("SEU_TOKEN_AQUI")  # Substitua pelo seu token real

asyncio.run(main())