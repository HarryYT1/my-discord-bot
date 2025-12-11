import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Kullanıcı bilgilerini gösterir")
    async def userinfo(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        now = datetime.now(timezone.utc)
        hesap_yasi = (now - kullanici.created_at).days
        sunucu_yasi = (now - kullanici.joined_at).days

        durum_emoji = {
            discord.Status.online: "🟢 Çevrimiçi",
            discord.Status.idle: "🟡 Boşta",
            discord.Status.dnd: "🔴 Rahatsız Etmeyin",
            discord.Status.offline: "⚫ Çevrimdışı"
        }

        banner_url = None
        try:
            user = await self.bot.fetch_user(kullanici.id)
            if user.banner:
                banner_url = user.banner.url
        except:
            pass

        embed = discord.Embed(
            color=kullanici.color if kullanici.color != discord.Color.default() else 0x2F3136,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(name=f"{kullanici.name} Genel Bilgileri", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)

        embed.add_field(name="👨‍💼 Takma Adı", value=f"```{kullanici.display_name}```", inline=True)
        embed.add_field(name="🆔 Kullanıcı ID", value=f"```{kullanici.id}```", inline=True)
        embed.add_field(name="🌐 Durum", value=durum_emoji.get(kullanici.status, "⚫ Bilinmiyor"), inline=True)

        embed.add_field(name="📅 Sunucuya Katılma", value=f"{kullanici.joined_at.strftime('%d %B %Y')}\n`{sunucu_yasi} gün önce`", inline=True)
        embed.add_field(name="📅 Hesap Yaşı", value=f"`{hesap_yasi} gün`", inline=True)

        if banner_url:
            embed.add_field(name="🖼️ Banner", value=f"[Görüntüle]({banner_url})", inline=False)
            embed.set_image(url=banner_url)
        else:
            embed.add_field(name="🖼️ Banner", value="Bu kullanıcıda banner yok.", inline=False)

        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Sunucu bilgilerini gösterir")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        online = sum(1 for m in guild.members if m.status == discord.Status.online)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
        bot_count = sum(1 for m in guild.members if m.bot)

        embed = discord.Embed(color=0x5865F2)
        embed.set_author(name=f"{guild.name} Sunucu Bilgileri", icon_url=guild.icon.url if guild.icon else None)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.add_field(name="🆔 Sunucu ID", value=f"`{guild.id}`")
        embed.add_field(name="👑 Sunucu Sahibi", value=f"{guild.owner.mention}", inline=True)
        embed.add_field(
            name="📅 Oluşturulma",
            value=f"{guild.created_at.strftime('%d %B %Y')} (`{(datetime.now(timezone.utc) - guild.created_at).days} gün`)",
            inline=True
        )

        embed.add_field(
            name=f"👥 Üyeler [{guild.member_count}]",
            value=f"🟢 Çevrimiçi: `{online}`\n🟡 Boşta: `{idle}`\n🔴 Rahatsız: `{dnd}`\n⚫ Çevrim dışı: `{offline}`\n🤖 Bot: `{bot_count}`",
            inline=True
        )

        embed.add_field(
            name=f"📁 Kanallar [{len(guild.channels)}]",
            value=f"💬 Metin: `{len(guild.text_channels)}`\n🔊 Sesli: `{len(guild.voice_channels)}`\n📂 Kategori: `{len(guild.categories)}`",
            inline=True
        )

        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Bot gecikmesini gösterir")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(color=0x00FF00 if latency < 150 else 0xFFFF00 if latency < 300 else 0xFF0000)
        embed.set_author(name="🏓 Pong!")
        embed.add_field(name="Gecikme", value=f"`{latency} ms`")
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Kullanıcının avatarını gösterir")
    async def avatar(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user

        embed = discord.Embed(color=kullanici.color)
        embed.set_author(name=f"{kullanici.name} Avatar")
        embed.set_image(url=kullanici.avatar.url)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="banner", description="Kullanıcının banner'ını gösterir")
    async def banner(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        try:
            user = await self.bot.fetch_user(kullanici.id)
            if user.banner:
                embed = discord.Embed(color=kullanici.color)
                embed.set_author(name=f"{kullanici.name} Banner")
                embed.set_image(url=user.banner.url)
                embed.timestamp = datetime.now(timezone.utc)
                return await interaction.response.send_message(embed=embed)
            else:
                return await interaction.response.send_message("❌ Bu kullanıcının banner'ı yok!", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"Hata: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Info(bot))
