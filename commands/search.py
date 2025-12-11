import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="google", description="Google'da arama yapar")
    async def google(self, interaction: discord.Interaction, arama: str):
        query = arama.replace(" ", "+")
        url = f"https://www.google.com/search?q={query}"

        embed = discord.Embed(
            title="🔍 Google Araması",
            description=f"**Aranan:** {arama}\n[Google'da Aç]({url})",
            color=0x4285F4,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="youtube", description="YouTube'da video arar")
    async def youtube(self, interaction: discord.Interaction, arama: str):
        embed = discord.Embed(
            title="▶️ YouTube Araması",
            description=f"**Aranan:** {arama}\n\nEn iyi sonuçlar:\nhttps://www.youtube.com/results?search_query={arama.replace(' ', '+')}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="imdb", description="IMDB'de film/dizi arar")
    async def imdb(self, interaction: discord.Interaction, arama: str):
        query = arama.replace(" ", "%20")
        url = f"https://www.imdb.com/find/?q={query}"

        embed = discord.Embed(
            title="🎬 IMDB Araması",
            description=f"**Aranan:** {arama}\n[IMDB'de Aç]({url})",
            color=0xF5C518,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="anime", description="Anime araması yapar")
    async def anime(self, interaction: discord.Interaction, arama: str):
        url = f"https://myanimelist.net/search/all?q={arama.replace(' ', '%20')}"
        embed = discord.Embed(
            title="🧧 Anime Araması",
            description=f"**Aranan:** {arama}\n[MyAnimeList'te Aç]({url})",
            color=0x2E51A2,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="manga", description="Manga araması yapar")
    async def manga(self, interaction: discord.Interaction, arama: str):
        url = f"https://myanimelist.net/manga.php?q={arama.replace(' ', '%20')}"
        embed = discord.Embed(
            title="📚 Manga Araması",
            description=f"**Aranan:** {arama}\n[MyAnimeList'te Aç]({url})",
            color=0x8E44AD,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Search(bot))
