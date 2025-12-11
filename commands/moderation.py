import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

warnings = {}


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== BAN ==========
    @app_commands.command(name="ban", description="Bir kullanıcıyı sunucudan yasaklar")
    @app_commands.describe(kullanici="Yasaklanacak kullanıcı", sebep="Yasaklama sebebi")
    async def ban(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if not interaction.user.guild_permissions.ban_members:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐔𝐲𝐞𝐥𝐞𝐫𝐢 𝐘𝐚𝐬𝐚𝐤𝐥𝐚' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            await kullanici.ban(reason=sebep)
            
            embed = discord.Embed(
                title="🔨 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢 𝐘𝐚𝐬𝐚𝐤𝐥𝐚𝐧𝐝𝐢",
                color=0xFF0000
            )
            embed.add_field(
                name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
                value=f"{kullanici.mention}\n```{kullanici.name}\nID: {kullanici.id}```",
                inline=True
            )
            embed.add_field(
                name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
                value=f"{interaction.user.mention}\n```{interaction.user.name}```",
                inline=True
            )
            embed.add_field(
                name="📝 𝐒𝐞𝐛𝐞𝐩",
                value=f"```{sebep}```",
                inline=False
            )
            embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
            embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== UNBAN ==========
    @app_commands.command(name="unban", description="Bir kullanıcının yasağını kaldırır")
    @app_commands.describe(user_id="Yasağı kaldırılacak kullanıcının ID'si")
    async def unban(self, interaction: discord.Interaction, user_id: str):
        if not interaction.user.guild_permissions.ban_members:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐔𝐲𝐞𝐥𝐞𝐫𝐢 𝐘𝐚𝐬𝐚𝐤𝐥𝐚' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user)
            
            embed = discord.Embed(
                title="✅ 𝐘𝐚𝐬𝐚𝐤 𝐊𝐚𝐥𝐝𝐢𝐫𝐢𝐥𝐝𝐢",
                color=0x00FF00
            )
            embed.add_field(
                name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
                value=f"```{user.name}\nID: {user.id}```",
                inline=True
            )
            embed.add_field(
                name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
                value=f"{interaction.user.mention}\n```{interaction.user.name}```",
                inline=True
            )
            embed.add_field(
                name="📋 𝐁𝐢𝐥𝐠𝐢",
                value="```Kullanıcının yasağı başarıyla kaldırıldı```",
                inline=False
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐈𝐃'𝐲𝐞 𝐬𝐚𝐡𝐢𝐩 𝐲𝐚𝐬𝐚𝐤𝐥𝐢 𝐤𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢 𝐛𝐮𝐥𝐮𝐧𝐚𝐦𝐚𝐝𝐢!**",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== KICK ==========
    @app_commands.command(name="kick", description="Bir kullanıcıyı sunucudan atar")
    @app_commands.describe(kullanici="Atılacak kullanıcı", sebep="Atma sebebi")
    async def kick(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if not interaction.user.guild_permissions.kick_members:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐔𝐲𝐞𝐥𝐞𝐫𝐢 𝐀𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            await kullanici.kick(reason=sebep)
            
            embed = discord.Embed(
                title="👢 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢 𝐀𝐭𝐢𝐥𝐝𝐢",
                color=0xFF8C00
            )
            embed.add_field(
                name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
                value=f"{kullanici.mention}\n```{kullanici.name}\nID: {kullanici.id}```",
                inline=True
            )
            embed.add_field(
                name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
                value=f"{interaction.user.mention}\n```{interaction.user.name}```",
                inline=True
            )
            embed.add_field(
                name="📝 𝐒𝐞𝐛𝐞𝐩",
                value=f"```{sebep}```",
                inline=False
            )
            embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
            embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== TIMEOUT ==========
    @app_commands.command(name="timeout", description="Kullanıcıya zaman aşımı uygular")
    @app_commands.describe(kullanici="Susturulacak kullanıcı", dakika="Süre (dakika)", sebep="Susturma sebebi")
    async def timeout(self, interaction: discord.Interaction, kullanici: discord.Member, dakika: int, sebep: str = "Sebep belirtilmedi"):
        if not interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐔𝐲𝐞𝐥𝐞𝐫𝐢 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            duration = timedelta(minutes=dakika)
            await kullanici.timeout(duration, reason=sebep)
            
            embed = discord.Embed(
                title="🔇 𝐙𝐚𝐦𝐚𝐧 𝐀𝐬𝐢𝐦𝐢 𝐔𝐲𝐠𝐮𝐥𝐚𝐧𝐝𝐢",
                color=0x808080
            )
            embed.add_field(
                name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
                value=f"{kullanici.mention}\n```{kullanici.name}```",
                inline=True
            )
            embed.add_field(
                name="⏱️ 𝐒𝐮𝐫𝐞",
                value=f"```{dakika} dakika```",
                inline=True
            )
            embed.add_field(
                name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
                value=f"{interaction.user.mention}",
                inline=True
            )
            embed.add_field(
                name="📝 𝐒𝐞𝐛𝐞𝐩",
                value=f"```{sebep}```",
                inline=False
            )
            embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
            embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== UNTIMEOUT ==========
    @app_commands.command(name="untimeout", description="Kullanıcının zaman aşımını kaldırır")
    @app_commands.describe(kullanici="Zaman aşımı kaldırılacak kullanıcı")
    async def untimeout(self, interaction: discord.Interaction, kullanici: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐔𝐲𝐞𝐥𝐞𝐫𝐢 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            await kullanici.timeout(None)
            
            embed = discord.Embed(
                title="🔊 𝐙𝐚𝐦𝐚𝐧 𝐀𝐬𝐢𝐦𝐢 𝐊𝐚𝐥𝐝𝐢𝐫𝐢𝐥𝐝𝐢",
                color=0x00FF00
            )
            embed.add_field(
                name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
                value=f"{kullanici.mention}\n```{kullanici.name}```",
                inline=True
            )
            embed.add_field(
                name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
                value=f"{interaction.user.mention}\n```{interaction.user.name}```",
                inline=True
            )
            embed.add_field(
                name="📋 𝐁𝐢𝐥𝐠𝐢",
                value="```Kullanıcı artık konuşabilir```",
                inline=False
            )
            embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
            embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== WARN ==========
    @app_commands.command(name="warn", description="Kullanıcıyı uyarır")
    @app_commands.describe(kullanici="Uyarılacak kullanıcı", sebep="Uyarı sebebi")
    async def warn(self, interaction: discord.Interaction, kullanici: discord.Member, sebep: str):
        if not interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐔𝐲𝐞𝐥𝐞𝐫𝐢 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        user_id = kullanici.id
        if user_id not in warnings:
            warnings[user_id] = []
        
        warnings[user_id].append({
            "sebep": sebep,
            "yetkili": interaction.user.name,
            "tarih": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        })
        
        embed = discord.Embed(
            title="⚠️ 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢 𝐔𝐲𝐚𝐫𝐢𝐥𝐝𝐢",
            color=0xFFFF00
        )
        embed.add_field(
            name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
            value=f"{kullanici.mention}\n```{kullanici.name}```",
            inline=True
        )
        embed.add_field(
            name="📊 𝐓𝐨𝐩𝐥𝐚𝐦 𝐔𝐲𝐚𝐫𝐢",
            value=f"```{len(warnings[user_id])}```",
            inline=True
        )
        embed.add_field(
            name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
            value=f"{interaction.user.mention}",
            inline=True
        )
        embed.add_field(
            name="📝 𝐒𝐞𝐛𝐞𝐩",
            value=f"```{sebep}```",
            inline=False
        )
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(f"{kullanici.mention}", embed=embed)

    # ========== CLEAR ==========
    @app_commands.command(name="clear", description="Belirtilen sayıda mesaj siler")
    @app_commands.describe(sayi="Silinecek mesaj sayısı (1-1000)")
    async def clear(self, interaction: discord.Interaction, sayi: int):
        if not interaction.user.guild_permissions.manage_messages:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐌𝐞𝐬𝐚𝐣𝐥𝐚𝐫𝐢 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if sayi < 1 or sayi > 1000:
            embed = discord.Embed(
                description="❌ **𝟏-𝟏𝟎𝟎𝟎 𝐚𝐫𝐚𝐬𝐢 𝐛𝐢𝐫 𝐬𝐚𝐲𝐢 𝐠𝐢𝐫𝐢𝐧!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=sayi)

        embed = discord.Embed(
            title="🗑️ 𝐌𝐞𝐬𝐚𝐣𝐥𝐚𝐫 𝐓𝐞𝐦𝐢𝐳𝐥𝐞𝐧𝐝𝐢",
            color=0x00FF00
        )
        embed.add_field(
            name="📊 𝐒𝐢𝐥𝐢𝐧𝐞𝐧 𝐌𝐞𝐬𝐚𝐣",
            value=f"```{len(deleted)} adet```",
            inline=True
        )
        embed.add_field(
            name="👮 𝐘𝐞𝐭𝐤𝐢𝐥𝐢",
            value=f"{interaction.user.mention}",
            inline=True
        )
        embed.add_field(
            name="📍 𝐊𝐚𝐧𝐚𝐥",
            value=f"{interaction.channel.mention}",
            inline=True
        )
        embed.set_footer(text=f"Moderasyon Sistemi • {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
