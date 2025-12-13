import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import random
import aiohttp
import os

TENOR_API_KEY = os.getenv("TENOR_API_KEY")


async def get_tenor_gif(query: str):
    url = "https://tenor.googleapis.com/v2/search"
    params = {
        "q": query,
        "key": TENOR_API_KEY,
        "limit": 20,
        "media_filter": "gif"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    try:
        gif = random.choice(data["results"])
        return gif["media_formats"]["gif"]["url"]
    except:
        return None


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== SAY ==========
    @app_commands.command(name="say", description="🗣️ Bot mesajınızı tekrar eder")
    async def say(self, interaction: discord.Interaction, mesaj: str):
        embed = discord.Embed(
            title="🗨️ 𝗦𝗮𝘆",
            description=f"```{mesaj}```",
            color=0x5865F2
        )
        embed.set_footer(text=f"👤 Gönderen: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    # ========== JOKE ==========
    @app_commands.command(name="joke", description="😂 Rastgele şaka")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Bilgisayar neden üşümez? Çünkü fanı vardır 😂",
            "Programcılar neden gece çalışır? Çünkü karanlık mod 🌙",
            "WiFi neden mutsuz? Çünkü bağlantısı zayıf 😅",
            "Java mı Python mu? Kahve ☕",
            "Bug fixing = sihir 🧙"
        ]

        embed = discord.Embed(
            title="🤣 𝗦̧𝗮𝗸𝗮 𝗭𝗮𝗺𝗮𝗻𝗶!",
            description=f"```{random.choice(jokes)}```",
            color=0xFFD700
        )
        embed.set_footer(text=f"😄 İsteyen: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    # ========== 8BALL ==========
    @app_commands.command(name="sor", description="🎱 Sor, cevaplayalım")
    async def sor(self, interaction: discord.Interaction, soru: str):
        cevaplar = [
            "Kesinlikle evet! ✅",
            "Büyük ihtimalle 🤔",
            "Sanmam ❌",
            "Zaman gösterecek ⏳",
            "Kesinlikle hayır 🚫",
            "Şans senden yana 🍀",
            "Tekrar sor 🔄"
        ]

        embed = discord.Embed(title="🎱 8BALL", color=0x8E44AD)
        embed.add_field(name="❓ Soru", value=f"```{soru}```", inline=False)
        embed.add_field(name="💭 Cevap", value=f"```{random.choice(cevaplar)}```", inline=False)
        embed.set_footer(text=f"🧠 Soran: {interaction.user.name}")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== HUG ==========
    @app_commands.command(name="hug", description="🤗 Sarıl")
    async def hug(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 **Kendine sarılamazsın!** 🤗",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        gif = await get_tenor_gif("anime hug")

        embed = discord.Embed(
            title="🤗 𝗦𝗮𝗿𝗶𝗹𝗺𝗮",
            description=f"{interaction.user.mention} 💞 {kullanici.mention}\n```Sıcacık bir sarılma!```",
            color=0xFF69B4
        )
        if gif:
            embed.set_image(url=gif)

        embed.set_footer(text="💕 Sevgi dolu an")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== KISS ==========
    @app_commands.command(name="kiss", description="💋 Öpücük gönder")
    async def kiss(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 **Kendini öpemezsin!** 😘",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        gif = await get_tenor_gif("anime kiss")

        embed = discord.Embed(
            title="💋 𝗢̈𝗽𝘂̈𝗰𝘂̈𝗸",
            description=f"{interaction.user.mention} 💖 {kullanici.mention}\n```Romantik bir öpücük!```",
            color=0xFF1493
        )
        if gif:
            embed.set_image(url=gif)

        embed.set_footer(text="💞 Aşk dolu")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== SLAP ==========
    @app_commands.command(name="slap", description="👋 Tokat at")
    async def slap(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 **Kendine tokat atamazsın!** 😳",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        gif = await get_tenor_gif("anime slap")

        embed = discord.Embed(
            title="👋 𝗧𝗼𝗸𝗮𝘁",
            description=f"{interaction.user.mention} 💥 {kullanici.mention}\n```ŞLAK!```",
            color=0xE74C3C
        )
        if gif:
            embed.set_image(url=gif)

        embed.set_footer(text="💢 Sert vurdu")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== PAT ==========
    @app_commands.command(name="pat", description="✋ Başını okşa")
    async def pat(self, interaction: discord.Interaction, kullanici: discord.Member):
        if kullanici == interaction.user:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 **Kendi başını okşayamazsın!** 😊",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        gif = await get_tenor_gif("anime head pat")

        embed = discord.Embed(
            title="✋ 𝗢𝗸𝘀𝗮𝗺𝗮",
            description=f"{interaction.user.mention} 💝 {kullanici.mention}\n```Sevgiyle okşadı!```",
            color=0xFFC0CB
        )
        if gif:
            embed.set_image(url=gif)

        embed.set_footer(text="💗 Nazikçe")
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
