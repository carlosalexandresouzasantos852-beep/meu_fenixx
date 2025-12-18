from meu_bot_farm.web import keep_alive
from meu_bot_farm.bot import bot
from meu_bot_farm.config import TOKEN

keep_alive()

print("Iniciando bot com TOKEN:", TOKEN[:5] + "..." if TOKEN else "TOKEN não definido")
bot.run(TOKEN)