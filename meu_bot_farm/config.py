import os

BOT_PREFIX = "!"
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("O token do bot não foi definido! Adicione DISCORD_TOKEN nas variáveis de ambiente.")

DB_PATH = "data/ticket_farm.db"