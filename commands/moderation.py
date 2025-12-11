import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

warnings = {}

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bir kullanıcıyı sunucudan yasaklar")
    @app_commands.describe(kullanici="Yasaklanacak kullanıcı", sebep="Sebep")
    async def ban(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        try:
            await kullanici.ban(reason=sebep)
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="🔨 Kullanıcı Yasaklandı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
            embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
            embed.add_field(name="👮 Yetkili", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="📝 Sebep", value=sebep, inline=False)
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @app_commands.command(name="kick", description="Bir kullanıcıyı sunucudan atar")
    async def kick(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        try:
            await kullanici.kick(reason=sebep)
            embed = discord.Embed(color=0xFF8C00)
            embed.set_author(name="👢 Kullanıcı Atıldı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
            embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`")
            embed.add_field(name="📝 Sebep", value=sebep)
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @app_commands.command(name="mute", description="Kullanıcıyı susturur")
    async def mute(self, interaction: discord.Interaction, kullanici: discord.Member, dakika: int, sebep: str = "Sebep belirtilmedi"):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        try:
            duration = timedelta(minutes=dakika)
            await kullanici.timeout(duration, reason=sebep)
            embed = discord.Embed(color=0x808080)
            embed.set_author(name="🔇 Kullanıcı Susturuldu")
            embed.add_field(name="Kullanıcı", value=kullanici.mention)
            embed.add_field(name="Süre", value=f"{dakika} dakika")
            embed.add_field(name="Sebep", value=sebep)
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @app_commands.command(name="unmute", description="Susturmayı kaldırır")
    async def unmute(self, interaction: discord.Interaction, kullanici: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        try:
            await kullanici.timeout(None)
            embed = discord.Embed(color=0x00FF00)
            embed.set_author(name="🔊 Susturma Kaldırıldı")
            embed.add_field(name="Kullanıcı", value=kullanici.mention)
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @app_commands.command(name="warn", description="Kullanıcıyı uyarır")
    async def warn(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        user_id = kullanici.id
        if user_id not in warnings:
            warnings[user_id] = []
        warnings[user_id].append({
            "sebep": sebep,
            "yetkili": interaction.user.name,
            "tarih": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        embed = discord.Embed(color=0xFFFF00)
        embed.set_author(name="⚠️ Kullanıcı Uyarıldı")
        embed.add_field(name="Kullanıcı", value=kullanici.mention)
        embed.add_field(name="Sebep", value=sebep)
        embed.add_field(name="Toplam Uyarı", value=len(warnings[user_id]))
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear", description="Mesaj temizler")
    async def clear(self, interaction: discord.Interaction, sayi: int):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
        if sayi < 1 or sayi > 1000:
            return await interaction.response.send_message("❌ 1-1000 arası sayı gir!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=sayi)

        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="🗑️ Mesajlar Silindi")
        embed.add_field(name="Silinen", value=len(deleted))
        embed.timestamp = datetime.now()
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
