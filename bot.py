import discord
from discord.ext import commands
import os

# config.py dosyasından intent'leri ve ayarları içe aktar
from config import intents

# Komut öneki olarak '/' kullanılıyor. Bu, slash komutları için standarttır.
bot = commands.Bot(command_prefix="/", intents=intents)

async def setup_extensions():
    for filename in os.listdir("commands"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"commands.{filename[:-3]}")
            except Exception as e:
                print(f'Hata: commands/{filename} yüklenirken sorun oluştu: {e}')

    for filename in os.listdir("events"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"events.{filename[:-3]}")
            except Exception as e:
                print(f'Hata: events/{filename} yüklenirken sorun oluştu: {e}')

# setup_hook, bot client'ı giriş yapmadan önce çalışır ve Cog'ları yüklemek için idealdir.
bot.setup_hook = setup_extensions

@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")
    try:
        # Tüm eğik çizgi komutlarını Discord API'ına senkronize eder
        synced = await bot.tree.sync()
        print(f"{len(synced)} komut senkronize edildi.")
    except Exception as e:
        print(f"Hata: Komut senkronizasyonu başarısız oldu: {e}")

# Ortam değişkenlerinden TOKEN'i al
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    print("Bot başlatılıyor...")
    bot.run(TOKEN)
else:
    print("HATA: DISCORD_TOKEN ortam değişkeni bulunamadı. Bot başlatılamıyor.")
