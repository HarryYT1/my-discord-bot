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
    @app_commands.command(name="say", description="Bot yazdığınız mesajı tekrar eder")
    @app_commands.describe(mesaj="Tekrar edilecek mesaj")
    async def say(self, interaction: discord.Interaction, mesaj: str):
        embed = discord.Embed(
            description=mesaj,
            color=0x5865F2
        )
        embed.set_footer(text=f"Gönderen: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed)

    # ========== JOKE ==========
    @app_commands.command(name="joke", description="Rastgele bir şaka gönderir")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Bilgisayar neden üşümez? Çünkü içinde fan vardır 😂",
            "Neden deniz dalgalıdır? Çünkü karaya çıkamaz 😅",
            "Adamın biri güneşte yanmış, ayda da donmuş 😁",
            "Programcılar neden bahçe işlerini sevmez? Çünkü bug'ları kovmaktan bıkmışlardır 🐛",
            "Bilgisayarcılar neden açık havayı sevmez? Çünkü dışarısı 'cloud' dolu ☁️"
        ]
        
        embed = discord.Embed(
            title="😂 𝐑𝐚𝐧𝐝𝐨𝐦 𝐒𝐚𝐤𝐚",
            description=f"```{random.choice(jokes)}```",
            color=0xFFD700
        )
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed)

    # ========== 8BALL ==========
    @app_commands.command(name="sor", description="Bot sorunuza rastgele yanıt verir")
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
            title="🎱 𝟖𝐁𝐚𝐥𝐥",
            color=0x8B00FF
        )
        embed.add_field(name="❓ 𝐒𝐨𝐫𝐮", value=f"```{soru}```", inline=False)
        embed.add_field(name="💭 𝐂𝐞𝐯𝐚𝐩", value=f"```{random.choice(cevaplar)}```", inline=False)
        embed.set_footer(text=f"Soran: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== HUG ==========
    @app_commands.command(name="hug", description="Birini sarılırsınız")
    @app_commands.describe(kullanici="Sarılmak istediğiniz kişi")
    async def hug(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ **𝐊𝐞𝐧𝐝𝐢𝐧𝐢𝐳𝐞 𝐬𝐚𝐫𝐢𝐥𝐚𝐦𝐚𝐳𝐬𝐢𝐧𝐢𝐳!** 🤗",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="🤗 𝐒𝐚𝐫𝐢𝐥𝐦𝐚",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n```Sıcacık bir sarılma!```",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(self.hug_gifs))
        embed.set_footer(text=f"💕 Sevgiyle sarıldı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== KISS ==========
    @app_commands.command(name="kiss", description="Birine öpücük gönderirsin")
    @app_commands.describe(kullanici="Öpmek istediğiniz kişi")
    async def kiss(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ **𝐊𝐞𝐧𝐝𝐢𝐧𝐢𝐳𝐢 𝐨𝐩𝐞𝐦𝐞𝐳𝐬𝐢𝐧𝐢𝐳!** 😘",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="💋 𝐎𝐩𝐮𝐜𝐮𝐤",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n```Romantik bir öpücük!```",
            color=0xFF1493
        )
        embed.set_image(url=random.choice(self.kiss_gifs))
        embed.set_footer(text=f"💖 Aşkla öptü", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== SLAP ==========
    @app_commands.command(name="slap", description="Birine tokat atarsın")
    @app_commands.describe(kullanici="Tokat atacağınız kişi")
    async def slap(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ **𝐊𝐞𝐧𝐝𝐢𝐧𝐢𝐳𝐞 𝐭𝐨𝐤𝐚𝐭 𝐚𝐭𝐚𝐦𝐚𝐳𝐬𝐢𝐧𝐢𝐳!** 😳",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        embed = discord.Embed(
            title="👋 𝐓𝐨𝐤𝐚𝐭",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n```Güçlü bir tokat!```",
            color=0xFF4500
        )
        embed.set_image(url=random.choice(self.slap_gifs))
        embed.set_footer(text=f"💥 Sertçe vurdu", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== PAT ==========
    @app_commands.command(name="pat", description="Birinin başını okşarsın")
    @app_commands.describe(kullanici="Başını okşayacağınız kişi")
    async def pat(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            embed = discord.Embed(
                description="❌ **𝐊𝐞𝐧𝐝𝐢 𝐛𝐚𝐬𝐢𝐧𝐢𝐳𝐢 𝐨𝐤𝐬𝐚𝐲𝐚𝐦𝐚𝐳𝐬𝐢𝐧𝐢𝐳!** 😊",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        pat_gifs = [
            "https://media1.tenor.com/m/FmJHdN7Vt04AAAAC/anime-head-pat.gif",
            "https://media1.tenor.com/m/Ip0IPlgmLSwAAAAC/anime-pat.gif",
            "https://media1.tenor.com/m/AlLLoFk_UAYAAAAC/headpat-anime.gif"
        ]
        
        embed = discord.Embed(
            title="✋ 𝐎𝐤𝐬𝐚𝐦𝐚",
            description=f"{interaction.user.mention} **➜** {kullanici.mention}\n```Sevgiyle okşadı!```",
            color=0xFFC0CB
        )
        embed.set_image(url=random.choice(pat_gifs))
        embed.set_footer(text=f"💝 Nazikçe okşadı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
