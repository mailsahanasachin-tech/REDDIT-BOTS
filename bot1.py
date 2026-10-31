import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# 1. Keep-alive web server so Render's free tier stays happy
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Setup your Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# 3. Run everything together
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN_BOT1")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN_BOT1 is missing!")
    else:
        bot.run(TOKEN)
