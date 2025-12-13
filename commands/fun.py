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
            "https://media1.tenor.com/m/RTgr0eYP-UMAAAAC/kiss-anime-kiss.gif",
            "https://media1.tenor.com/m/u8kq2vE6xOAAAAAC/anime-love.gif"
        ]
        
        self.slap_gifs = [
            "https://media1.tenor.com/m/Oyq5hZrVXkEAAAAC/anime-slap.gif",
            "https://media1.tenor.com/m/ZC2EpPHTHueAAAAC/slap-hit.gif",
            "https://media1.tenor.com/m/zC4lYeWqh7MAAAAC/anime-slap.gif",
            "https://media1.tenor.com/m/W23TWGxTnMoAAAAC/anime-mad.gif",
            "https://media1.tenor.com/m/D9jJZb6s1dEAAAAC/slap.gif"
        ]

    # ========== SAY ==========
    @app_commands.command(name="say", description="💬 Bot yazdığınız mesajı tekrar eder")
    @app_commands.describe(mesaj="Tekrar edilecek mesaj")
    async def say(self, interaction: discord.Interaction, mesaj: str):
        embed = discord.Embed(
            description=mesaj,
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed)

    # ========== JOKE ==========
    @app_commands.command(name="joke", description="😂 Rastgele bir şaka gönderir")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Bilgisayar neden üşümez? Çünkü içinde fan vardır 😂",
            "Neden deniz dalgalıdır? Çünkü karaya çıkamaz 😅",
            "Adamın biri güneşte yanmış, ayda da donmuş 😆",
            "Programcılar neden bahçe işlerini sevmez? Çünkü bug'ları kovmaktan bıkmışlardır 🐛",
            "Bilgisayarcılar neden açık havayı sevmez? Çünkü dışarısı 'cloud' dolu ☁️"
        ]
        
        embed = discord.Embed(
            title="😂 Rastgele Şaka",
            description=random.choice(jokes),
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed)

    # ========== 8BALL ==========
    @app_commands.command(name="sor", description="🎱 Bot sorunuza rastgele yanıt verir")
    @app_commands.describe(soru="Sormak istediğiniz soru")
    async def sor(self, interaction: discord.Interaction, soru: str):
        cevaplar = [
            "Kesinlikle evet! ✅",
            "Bence olabilir. 🤔",
            "İmkansız gibi duruyor. ❌",
            "Bunu söylemek için çok erken. ⏰",
            "Hayır. ❎",
            "Kesinlikle hayır! 🚫",
            "Şüphesiz! 💯",
            "Belki... 🎲",
            "Yeniden sor. 🔄"
        ]
        
        embed = discord.Embed(
            title="🎱 8Ball",
            color=0x8B00FF
        )
        embed.add_field(name="❓ Soru", value=soru, inline=False)
        embed.add_field(name="💭 Cevap", value=random.choice(cevaplar), inline=False)
        
        await interaction.response.send_message(embed=embed)

    # ========== HUG ==========
    @app_commands.command(name="hug", description="🤗 Birini sarılırsınız")
    @app_commands.describe(kullanici="Sarılmak istediğiniz kişi")
    async def hug(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ Kendinize sarılamazsınız!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="🤗 Sarılma",
            description=f"{interaction.user.mention} ➜ {kullanici.mention}\nSıcacık bir sarılma!",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(self.hug_gifs))
        
        await interaction.response.send_message(embed=embed)

    # ========== KISS ==========
    @app_commands.command(name="kiss", description="💋 Birine öpücük gönderirsin")
    @app_commands.describe(kullanici="Öpmek istediğiniz kişi")
    async def kiss(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ Kendinizi öpemezsiniz!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="💋 Öpücük",
            description=f"{interaction.user.mention} ➜ {kullanici.mention}\nRomantik bir öpücük!",
            color=0xFF1493
        )
        embed.set_image(url=random.choice(self.kiss_gifs))
        
        await interaction.response.send_message(embed=embed)

    # ========== SLAP ==========
    @app_commands.command(name="slap", description="👋 Birine tokat atarsın")
    @app_commands.describe(kullanici="Tokat atacağınız kişi")
    async def slap(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ Kendinize tokat atamazsınız!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="👋 Tokat",
            description=f"{interaction.user.mention} ➜ {kullanici.mention}\nGüçlü bir tokat!",
            color=0xFF4500
        )
        embed.set_image(url=random.choice(self.slap_gifs))
        
        await interaction.response.send_message(embed=embed)

    # ========== PAT ==========
    @app_commands.command(name="pat", description="✋ Birinin başını okşarsın")
    @app_commands.describe(kullanici="Başını okşayacağınız kişi")
    async def pat(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ Kendi başınızı okşayamazsınız!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        pat_gifs = [
            "https://media1.tenor.com/m/FmJHdN7Vt04AAAAC/anime-head-pat.gif",
            "https://media1.tenor.com/m/Ip0IPlgmLSwAAAAC/anime-pat.gif",
            "https://media1.tenor.com/m/AlLLoFk_UAYAAAAC/headpat-anime.gif"
        ]
        
        embed = discord.Embed(
            title="✋ Okşama",
            description=f"{interaction.user.mention} ➜ {kullanici.mention}\nSevgiyle okşadı!",
            color=0xFFC0CB
        )
        embed.set_image(url=random.choice(pat_gifs))
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
