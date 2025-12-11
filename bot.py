
import discord
from discord.ext import commands
import os
from config import intents

bot = commands.Bot(command_prefix="/", intents=intents)

async def setup_extensions():
    for filename in os.listdir("commands"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"commands.{filename[:-3]}")
                print(f"✅ Yüklendi: commands/{filename}")
            except Exception as e:
                print(f'❌ Hata: commands/{filename} yüklenirken sorun oluştu: {e}')

    for filename in os.listdir("events"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"events.{filename[:-3]}")
                print(f"✅ Yüklendi: events/{filename}")
            except Exception as e:
                print(f'❌ Hata: events/{filename} yüklenirken sorun oluştu: {e}')

bot.setup_hook = setup_extensions

@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} komut senkronize edildi.")
    except Exception as e:
        print(f"Hata: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    print("Bot başlatılıyor...")
    bot.run(TOKEN)
else:
    print("HATA: DISCORD_TOKEN ortam değişkeni bulunamadı. Bot başlatılamıyor.")
