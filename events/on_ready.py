import discord
from discord.ext import commands


class Ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"\n🔹 BOT GİRİŞ YAPTI: {self.bot.user}")
        print("🔹 Komutlar senkronize ediliyor...")

        try:
            synced = await self.bot.tree.sync()
            print(f"🔹 {len(synced)} komut başarıyla senkronize edildi.")
        except Exception as e:
            print(f"❌ Sync Hatası: {e}")

        print("✅ Bot başarıyla aktif!")


async def setup(bot):
    await bot.add_cog(Ready(bot))
