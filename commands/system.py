import discord
from discord.ext import commands
from discord import app_commands
from config import OWNER_ID
import asyncio


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def owner_check(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Bu komutu sadece bot sahibi kullanabilir!", ephemeral=True)
            return False
        return True

    @app_commands.command(name="setstatus", description="Botun durumunu ayarlar (online, idle, dnd, offline)")
    async def setstatus(self, interaction: discord.Interaction, status: str):
        if not await self.owner_check(interaction):
            return

        status = status.lower()
        durumlar = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "offline": discord.Status.offline
        }

        if status not in durumlar:
            return await interaction.response.send_message("❌ Durum: online, idle, dnd, offline olabilir.", ephemeral=True)

        await self.bot.change_presence(status=durumlar[status])
        await interaction.response.send_message(f"✅ Durum değiştirildi: **{status}**")

    @app_commands.command(name="setactivity", description="Botun aktivitesini ayarlar")
    async def setactivity(self, interaction: discord.Interaction, activity: str, type: str):
        if not await self.owner_check(interaction):
            return

        types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing
        }

        if type not in types:
            return await interaction.response.send_message("❌ Aktivite türleri: playing, watching, listening, competing", ephemeral=True)

        await self.bot.change_presence(
            activity=discord.Activity(type=types[type], name=activity)
        )

        await interaction.response.send_message(f"🎮 Aktivite değiştirildi: **{type} {activity}**")

    @app_commands.command(name="shutdown", description="Botu güvenli şekilde kapatır")
    async def shutdown(self, interaction: discord.Interaction):
        if not await self.owner_check(interaction):
            return

        await interaction.response.send_message("🛑 Bot kapatılıyor...")
        await asyncio.sleep(1)
        await self.bot.close()

    @app_commands.command(name="reload", description="Komut dosyasını yeniden yükler")
    async def reload(self, interaction: discord.Interaction, dosya: str):
        if not await self.owner_check(interaction):
            return

        try:
            await self.bot.reload_extension(f"commands.{dosya}")
            await interaction.response.send_message(f"♻️ `{dosya}` başarıyla yeniden yüklendi.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: `{e}`")

    @app_commands.command(name="sync", description="Slash komutlarını senkronize eder")
    async def sync(self, interaction: discord.Interaction):
        if not await self.owner_check(interaction):
            return

        synced = await self.bot.tree.sync()
        await interaction.response.send_message(f"🔧 {len(synced)} komut senkronize edildi.")


async def setup(bot):
    await bot.add_cog(System(bot))
