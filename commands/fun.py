import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # GIF koleksiyonları
        self.hug_gifs = [
            "https://media1.tenor.com/m/92XhYr9bb2oAAAAC/anime-hug.gif",
            "https://media1.tenor.com/m/hMNJ7j9wNR0AAAAC/anime-hug.gif",
            "https://media1.tenor.com/m/m-HeV9J3qx0AAAAC/hug-anime.gif",
            "https://media1.tenor.com/m/uEn4FfKSYPgAAAAC/anime-anime-hug.gif",
            "https://media1.tenor.com/m/bzSurKXx0woAAAAC/kanna-anime-hug.gif"
        ]
        
        self.kiss_gifs = [
            "https://media1.tenor.com/m/TXEjvB5c1iYAAAAC/anime-kiss.gif",
            "https://media1.tenor.com/m/ZqAanQyj_GAAAAAC/anime-kiss.gif",
            "https://media1.tenor.com/m/v-dqGMgbwdYAAAAC/kiss-anime.gif",
            "https://media1.tenor.com/m/45t8vQxW4GAAAAAC/anime-kiss.gif",
            "https://media1.tenor.com/m/N5j6N2g4lM0AAAAC/anime-kiss.gif"
        ]
        
    # ========== HUG ==========\r\n
    @app_commands.command(name="hug", description="Birine sarılırsın")
    @app_commands.describe(kullanici="Sarılacağınız kişi")
    async def hug(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            # GÖRÜNÜM DÜZENLEMESİ BAŞLANGIÇ
            embed = discord.Embed(
                description="❌ **Kendine sarılamazsın!** 😊",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            # GÖRÜNÜM DÜZENLEMESİ SON
        
        # GÖRÜNÜM DÜZENLEMESİ BAŞLANGIÇ
        embed = discord.Embed(
            title="🫂 Sarılma Zamanı",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n_Sımsıkı sarıldılar!_",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(self.hug_gifs))
        embed.set_footer(text=f"İstek: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
        # GÖRÜNÜM DÜZENLEMESİ SON

    # ========== KISS ==========\r\n
    @app_commands.command(name="kiss", description="Birini öpersin")
    @app_commands.describe(kullanici="Öpeceğiniz kişi")
    async def kiss(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            # GÖRÜNÜM DÜZENLEMESİ BAŞLANGIÇ
            embed = discord.Embed(
                description="❌ **Kendi kendini öpemezsin!** 😉",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            # GÖRÜNÜM DÜZENLEMESİ SON
        
        # GÖRÜNÜM DÜZENLEMESİ BAŞLANGIÇ
        embed = discord.Embed(
            title="💋 Öpücük",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n_Dudaklarından öptü!_",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(self.kiss_gifs))
        embed.set_footer(text=f"İstek: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
        # GÖRÜNÜM DÜZENLEMESİ SON

    # ========== PAT ==========\r\n
    @app_commands.command(name="pat", description="Birinin başını okşarsın")
    @app_commands.describe(kullanici="Başını okşayacağınız kişi")
    async def pat(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            # GÖRÜNÜM DÜZENLEMESİ BAŞLANGIÇ
            embed = discord.Embed(
                description="❌ **Kendi başınızı okşayamazsınız!** 😊",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            # GÖRÜNÜM DÜZENLEMESİ SON
        
        pat_gifs = [
            "https://media1.tenor.com/m/FmJHdN7Vt04AAAAC/anime-head-pat.gif",
            "https://media1.tenor.com/m/Ip0IPlgmLSwAAAAC/anime-pat.gif",
            "https://media1.tenor.com/m/AlLLoFk_UAYAAAAC/headpat-anime.gif"
        ]
        
        # GÖRÜNÜM DÜZENLEMESİ BAŞLANGIÇ
        embed = discord.Embed(
            title="✋ Baş Okşama",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n_Sevgiyle okşadı!_",
            color=0x5865F2
        )
        embed.set_image(url=random.choice(pat_gifs))
        embed.set_footer(text=f"İstek: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
        # GÖRÜNÜM DÜZENLEMESİ SON


async def setup(bot):
    await bot.add_cog(Fun(bot))
