import discord
from discord.ext import commands
import os
from config import intents

bot = commands.Bot(command_prefix="/", intents=intents)

# Komutları yükleme
for folder in os.listdir("commands"):
    if folder.endswith(".py"):
        bot.load_extension(f"commands.{folder[:-3]}")

# Eventleri yükleme
for folder in os.listdir("events"):
    if folder.endswith(".py"):
        bot.load_extension(f"events.{folder[:-3]}")

@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} komut senkronize edildi.")
    except Exception as e:
        print(f"Hata: {e}")

# Bot token buraya
# Ortam değişkeninden tokeni çekin
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    print("Bot başlatılıyor...")
    bot.run(TOKEN)
else:
    print("HATA: DISCORD_TOKEN ortam değişkeni bulunamadı. Bot başlatılamıyor.")

