import discord
from discord.ext import commands
from discord import app_commands
from config import OWNER_ID
from datetime import datetime, timezone
import os
import asyncio


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # SAHİP KONTROLÜ
    async def owner_check(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐬𝐚𝐝𝐞𝐜𝐞 𝐛𝐨𝐭 𝐬𝐚𝐡𝐢𝐛𝐢 𝐤𝐮𝐥𝐥𝐚𝐧𝐚𝐛𝐢𝐥𝐢𝐫!**",
                color=0xFF0000
            )
            embed.set_footer(text="Yalnızca bot sahibi için")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    # ========== SETSTATUS ==========
    @app_commands.command(name="setstatus", description="Botun durumunu ayarlar")
    @app_commands.describe(durum="Durum (online, idle, dnd, invisible)")
    @app_commands.choices(durum=[
        app_commands.Choice(name="🟢 Online", value="online"),
        app_commands.Choice(name="🟡 Idle (Boşta)", value="idle"),
        app_commands.Choice(name="🔴 DND (Rahatsız Etmeyin)", value="dnd"),
        app_commands.Choice(name="⚫ Invisible (Görünmez)", value="invisible")
    ])
    async def setstatus(self, interaction: discord.Interaction, durum: str):
        if not await self.owner_check(interaction):
            return

        durumlar = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }

        await self.bot.change_presence(status=durumlar[durum])
        
        status_emoji = {"online": "🟢", "idle": "🟡", "dnd": "🔴", "invisible": "⚫"}
        status_name = {"online": "Online", "idle": "Idle", "dnd": "DND", "invisible": "Invisible"}
        
        embed = discord.Embed(
            title="✅ 𝐃𝐮𝐫𝐮𝐦 𝐃𝐞𝐠𝐢𝐬𝐭𝐢𝐫𝐢𝐥𝐝𝐢",
            color=0x00FF00
        )
        embed.add_field(
            name="📊 𝐘𝐞𝐧𝐢 𝐃𝐮𝐫𝐮𝐦",
            value=f"```{status_emoji[durum]} {status_name[durum]}```",
            inline=False
        )
        embed.set_footer(text=f"Değiştiren: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== SETACTIVITY ==========
    @app_commands.command(name="setactivity", description="Botun aktivitesini ayarlar")
    @app_commands.describe(
        aktivite="Aktivite metni",
        tip="Aktivite tipi"
    )
    @app_commands.choices(tip=[
        app_commands.Choice(name="🎮 Oynuyor", value="playing"),
        app_commands.Choice(name="👀 İzliyor", value="watching"),
        app_commands.Choice(name="🎧 Dinliyor", value="listening"),
        app_commands.Choice(name="🏆 Yarışıyor", value="competing")
    ])
    async def setactivity(self, interaction: discord.Interaction, aktivite: str, tip: str):
        if not await self.owner_check(interaction):
            return

        types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "competing": discord.ActivityType.competing
        }

        await self.bot.change_presence(
            activity=discord.Activity(type=types[tip], name=aktivite)
        )

        type_emoji = {
            "playing": "🎮",
            "watching": "👀",
            "listening": "🎧",
            "competing": "🏆"
        }
        
        type_name = {
            "playing": "Oynuyor",
            "watching": "İzliyor",
            "listening": "Dinliyor",
            "competing": "Yarışıyor"
        }
        
        embed = discord.Embed(
            title="✅ 𝐀𝐤𝐭𝐢𝐯𝐢𝐭𝐞 𝐃𝐞𝐠𝐢𝐬𝐭𝐢𝐫𝐢𝐥𝐝𝐢",
            color=0x00FF00
        )
        embed.add_field(
            name=f"{type_emoji[tip]} 𝐓𝐢𝐩",
            value=f"```{type_name[tip]}```",
            inline=True
        )
        embed.add_field(
            name="📝 𝐀𝐤𝐭𝐢𝐯𝐢𝐭𝐞",
            value=f"```{aktivite}```",
            inline=True
        )
        embed.set_footer(text=f"Değiştiren: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== SHUTDOWN ==========
    @app_commands.command(name="shutdown", description="Botu güvenli şekilde kapatır")
    async def shutdown(self, interaction: discord.Interaction):
        if not await self.owner_check(interaction):
            return

        embed = discord.Embed(
            title="🛑 𝐁𝐨𝐭 𝐊𝐚𝐩𝐚𝐧𝐢𝐲𝐨𝐫",
            description="```Bot güvenli bir şekilde kapatılıyor...```",
            color=0xFF0000
        )
        embed.set_footer(text=f"Kapatan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(2)
        await self.bot.close()

    # ========== RELOAD ==========
    @app_commands.command(name="reload", description="Bir komut dosyasını yeniden yükler")
    @app_commands.describe(dosya="Yeniden yüklenecek dosya adı (örn: music)")
    async def reload(self, interaction: discord.Interaction, dosya: str):
        if not await self.owner_check(interaction):
            return

        try:
            await self.bot.reload_extension(f"commands.{dosya}")
            
            embed = discord.Embed(
                title="♻️ 𝐃𝐨𝐬𝐲𝐚 𝐘𝐞𝐧𝐢𝐥𝐞𝐧𝐝𝐢",
                color=0x00FF00
            )
            embed.add_field(
                name="📁 𝐃𝐨𝐬𝐲𝐚",
                value=f"```{dosya}.py```",
                inline=False
            )
            embed.set_footer(text=f"Yeniden yükleyen: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 𝐘𝐞𝐧𝐢𝐝𝐞𝐧 𝐘𝐮𝐤𝐥𝐞𝐦𝐞 𝐇𝐚𝐭𝐚𝐬𝐢",
                description=f"```{str(e)}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== SYNC ==========
    @app_commands.command(name="sync", description="Slash komutlarını senkronize eder")
    async def sync(self, interaction: discord.Interaction):
        if not await self.owner_check(interaction):
            return

        embed = discord.Embed(
            title="🔄 𝐒𝐞𝐧𝐤𝐫𝐨𝐧𝐢𝐳𝐚𝐬𝐲𝐨𝐧 𝐁𝐚𝐬𝐥𝐢𝐲𝐨𝐫",
            description="```Komutlar senkronize ediliyor...```",
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed)
        
        try:
            synced = await self.bot.tree.sync()
            
            embed = discord.Embed(
                title="✅ 𝐒𝐞𝐧𝐤𝐫𝐨𝐧𝐢𝐳𝐚𝐬𝐲𝐨𝐧 𝐓𝐚𝐦𝐚𝐦",
                color=0x00FF00
            )
            embed.add_field(
                name="📊 𝐒𝐞𝐧𝐤𝐫𝐨𝐧𝐢𝐳𝐞 𝐄𝐝𝐢𝐥𝐞𝐧",
                value=f"```{len(synced)} komut```",
                inline=False
            )
            embed.set_footer(text=f"Senkronize eden: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ 𝐒𝐞𝐧𝐤𝐫𝐨𝐧𝐢𝐳𝐚𝐬𝐲𝐨𝐧 𝐇𝐚𝐭𝐚𝐬𝐢",
                description=f"```{str(e)}```",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(System(bot))
