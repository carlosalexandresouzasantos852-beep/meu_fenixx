from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot online!"

def run():
    app.run(host='0.0.0.0', port=3000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()