import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Bot yazdığınız mesajı tekrar eder")
    async def say(self, interaction: discord.Interaction, mesaj: str):
        await interaction.response.send_message(mesaj)

    @app_commands.command(name="joke", description="Rastgele bir şaka gönderir")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Bilgisayar neden üşümez? Çünkü içinde fan vardır 😂",
            "Neden deniz dalgalıdır? Çünkü karaya çıkamaz 😅",
            "Adamın biri güneşte yanmış, ay da da donmuş 😁",
        ]
        await interaction.response.send_message(random.choice(jokes))

    @app_commands.command(name="sor", description="Bot sorunuza rastgele yanıt verir")
    async def sor(self, interaction: discord.Interaction, soru: str):
        cevaplar = [
            "Kesinlikle evet!",
            "Bence olabilir.",
            "İmkansız gibi duruyor.",
            "Bunu söylemek için çok erken.",
            "Hayır.",
            "Kesinlikle hayır!",
        ]
        embed = discord.Embed(
            title="🎱 8ball",
            description=f"**Soru:** {soru}\n**Cevap:** {random.choice(cevaplar)}",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hug", description="Birini sarılırsınız")
    async def hug(self, interaction: discord.Interaction, kullanici: discord.Member):
        gifs = [
            "https://media1.tenor.com/m/92XhYr9bb2oAAAAC/anime-hug.gif",
            "https://media1.tenor.com/m/JN2mKategorie8AAAAC/hug.gif",
        ]
        embed = discord.Embed(
            description=f"{interaction.user.mention} {kullanici.mention} kişisine sarılıyor 🤗",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(gifs))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kiss", description="Birine öpücük gönderirsin")
    async def kiss(self, interaction: discord.Interaction, kullanici: discord.Member):
        gifs = [
            "https://media1.tenor.com/m/BuskisokjrYAAAAC/kiss.gif",
            "https://media1.tenor.com/m/TXEjvB5c1iYAAAAC/anime-kiss.gif",
        ]
        embed = discord.Embed(
            description=f"{interaction.user.mention} {kullanici.mention} kişisini öpüyor 😘",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(gifs))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slap", description="Birine tokat atarsın")
    async def slap(self, interaction: discord.Interaction, kullanici: discord.Member):
        gifs = [
            "https://media1.tenor.com/m/Oyq5hZrVXkEAAAAC/anime-slap.gif",
            "https://media1.tenor.com/m/ZC2EpPHTHueAAAAC/slap-hit.gif",
        ]
        embed = discord.Embed(
            description=f"{interaction.user.mention} {kullanici.mention} kişisine tokat attı 😳",
            color=0xFF0000
        )
        embed.set_image(url=random.choice(gifs))
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
