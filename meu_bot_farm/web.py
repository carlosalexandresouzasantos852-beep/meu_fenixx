from flask import Flask
import threading

app = Flask("")

@app.route("/")
def home():
    return "Bot rodando!"

def run():
    app.run(host="0.0.0.0", port=3000)  # Troque 3000 pela porta do Render

# Rodar em uma thread separada para não travar o bot
threading.Thread(target=run).start()