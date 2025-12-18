from meu_bot_farm.bot import bot
from meu_bot_farm.config import TOKEN
from web import keep_alive

print("Iniciando bot com TOKEN:", TOKEN[:5] + "..." if TOKEN else "TOKEN não definido")

keep_alive()  # 🚀 abre a porta pro Render
bot.run(TOKEN)