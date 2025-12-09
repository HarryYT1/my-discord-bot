import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta, timezone
import random
import aiohttp
import yt_dlp
import os

# Bot ayarları
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Veri saklama
warnings = {}
anti_link_servers = set()
anti_spam_servers = set()
user_messages = {}
music_queues = {}
voice_clients = {}

# Bot owner ID (buraya kendi Discord ID'nizi yazın)
OWNER_ID = 911655070817456139  # BURAYA KENDİ ID'NİZİ YAZIN

# yt-dlp ayarları
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} olarak giriş yapıldı!')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} komut senkronize edildi!")
    except Exception as e:
        print(f"❌ Komutlar senkronize edilemedi: {e}")

# ============== MODERASYON KOMUTLARI ==============

@bot.tree.command(name="ban", description="Bir kullanıcıyı sunucudan yasaklar")
@app_commands.describe(kullanici="Yasaklanacak kullanıcı", sebep="Yasaklama sebebi")
async def ban(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await kullanici.ban(reason=sebep)
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="🔨 Kullanıcı Yasaklandı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
        embed.add_field(name="👮 Yetkili", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        embed.set_footer(text=f"Sunucu: {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="Bir kullanıcıyı sunucudan atar")
@app_commands.describe(kullanici="Atılacak kullanıcı", sebep="Atma sebebi")
async def kick(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await kullanici.kick(reason=sebep)
        embed = discord.Embed(color=0xFF8C00)
        embed.set_author(name="👢 Kullanıcı Atıldı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
        embed.add_field(name="👮 Yetkili", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        embed.set_footer(text=f"Sunucu: {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="mute", description="Bir kullanıcıyı belirli süre susturur")
@app_commands.describe(kullanici="Susturulacak kullanıcı", dakika="Süre (dakika)", sebep="Susturma sebebi")
async def mute(interaction: discord.Interaction, kullanici: discord.Member, dakika: int, sebep: str = "Sebep belirtilmedi"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        duration = timedelta(minutes=dakika)
        await kullanici.timeout(duration, reason=sebep)
        embed = discord.Embed(color=0x808080)
        embed.set_author(name="🔇 Kullanıcı Susturuldu", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
        embed.add_field(name="⏱️ Süre", value=f"`{dakika}` dakika", inline=True)
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        embed.set_footer(text=f"Yetkili: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="unmute", description="Bir kullanıcının susturmasını kaldırır")
@app_commands.describe(kullanici="Susturması kaldırılacak kullanıcı")
async def unmute(interaction: discord.Interaction, kullanici: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await kullanici.timeout(None)
        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="🔊 Susturma Kaldırıldı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
        embed.add_field(name="👮 Yetkili", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="warn", description="Bir kullanıcıyı uyarır")
@app_commands.describe(kullanici="Uyarılacak kullanıcı", sebep="Uyarı sebebi")
async def warn(interaction: discord.Interaction, kullanici: discord.Member, sebep: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    user_id = kullanici.id
    if user_id not in warnings:
        warnings[user_id] = []
    
    warnings[user_id].append({
        "sebep": sebep,
        "yetkili": interaction.user.name,
        "tarih": datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    
    embed = discord.Embed(color=0xFFFF00)
    embed.set_author(name="⚠️ Kullanıcı Uyarıldı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
    embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
    embed.add_field(name="📊 Toplam Uyarı", value=f"`{len(warnings[user_id])}`", inline=True)
    embed.add_field(name="📝 Sebep", value=sebep, inline=False)
    embed.set_footer(text=f"Yetkili: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now()
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Belirtilen sayıda mesajı siler")
@app_commands.describe(sayi="Silinecek mesaj sayısı")
async def clear(interaction: discord.Interaction, sayi: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    if sayi < 1 or sayi > 100:
        await interaction.response.send_message("❌ 1 ile 100 arasında bir sayı girin!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=sayi)
    
    embed = discord.Embed(color=0x00FF00)
    embed.set_author(name="🗑️ Mesajlar Silindi", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.add_field(name="📊 Silinen Mesaj", value=f"`{len(deleted)}` mesaj", inline=True)
    embed.add_field(name="📍 Kanal", value=interaction.channel.mention, inline=True)
    embed.set_footer(text=f"Yetkili: {interaction.user.name}")
    embed.timestamp = datetime.now()
    await interaction.followup.send(embed=embed, ephemeral=True)

# ============== ROL YÖNETİMİ ==============

@bot.tree.command(name="rolver", description="Bir kullanıcıya rol verir")
@app_commands.describe(kullanici="Rol verilecek kullanıcı", rol="Verilecek rol")
async def rolver(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await kullanici.add_roles(rol)
        embed = discord.Embed(color=rol.color)
        embed.set_author(name="✅ Rol Verildi", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
        embed.add_field(name="🎭 Rol", value=f"{rol.mention}\n`{rol.id}`", inline=True)
        embed.set_footer(text=f"Yetkili: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="rolal", description="Bir kullanıcıdan rol alır")
@app_commands.describe(kullanici="Rol alınacak kullanıcı", rol="Alınacak rol")
async def rolal(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await kullanici.remove_roles(rol)
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="❌ Rol Alındı", icon_url=kullanici.avatar.url if kullanici.avatar else None)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n`{kullanici.id}`", inline=True)
        embed.add_field(name="🎭 Rol", value=f"{rol.mention}\n`{rol.id}`", inline=True)
        embed.set_footer(text=f"Yetkili: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

# ============== BİLGİLENDİRME KOMUTLARI ==============

@bot.tree.command(name="userinfo", description="Kullanıcı bilgilerini gösterir")
@app_commands.describe(kullanici="Bilgisi görüntülenecek kullanıcı")
async def userinfo(interaction: discord.Interaction, kullanici: discord.Member = None):
    kullanici = kullanici or interaction.user
    
    # Hesap yaşını hesapla (timezone aware)
    now = datetime.now(timezone.utc)
    hesap_yasi = (now - kullanici.created_at).days
    sunucu_yasi = (now - kullanici.joined_at).days
    
    # Durum emoji
    durum_emoji = {
        discord.Status.online: "🟢 Çevrimiçi",
        discord.Status.idle: "🟡 Boşta",
        discord.Status.dnd: "🔴 Rahatsız Etmeyin",
        discord.Status.offline: "⚫ Çevrimdışı"
    }
    
    embed = discord.Embed(color=kullanici.color if kullanici.color != discord.Color.default() else 0x2F3136)
    embed.set_author(name=f"{kullanici.name} Profil Bilgileri", icon_url=kullanici.avatar.url if kullanici.avatar else None)
    embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
    
    # Genel Bilgiler
    embed.add_field(
        name="👤 Takma Adı",
        value=f"```{kullanici.display_name}```",
        inline=True
    )
    embed.add_field(
        name="🆔 Kullanıcı ID",
        value=f"```{kullanici.id}```",
        inline=True
    )
    embed.add_field(
        name="📊 Aktiflik Durumu",
        value=durum_emoji.get(kullanici.status, "⚫ Bilinmiyor"),
        inline=True
    )
    
    # Tarihler
    embed.add_field(
        name="📅 Hesap Oluşturma",
        value=f"{kullanici.created_at.strftime('%d %B %Y')}\n`{hesap_yasi} gün önce`",
        inline=True
    )
    embed.add_field(
        name="📥 Sunucuya Katılma",
        value=f"{kullanici.joined_at.strftime('%d %B %Y')}\n`{sunucu_yasi} gün önce`",
        inline=True
    )
    embed.add_field(
        name="🏆 En Yüksek Rol",
        value=kullanici.top_role.mention,
        inline=True
    )
    
    # Roller
    roller = [r.mention for r in kullanici.roles[1:]]
    if roller:
        roller_text = " ".join(roller[:15])
        if len(roller) > 15:
            roller_text += f"\n`ve {len(roller)-15} rol daha...`"
    else:
        roller_text = "`Rol yok`"
    
    embed.add_field(
        name=f"🎭 Roller [{len(kullanici.roles)-1}]",
        value=roller_text,
        inline=False
    )
    
    # İzinler
    izinler = []
    if kullanici.guild_permissions.administrator:
        izinler.append("👑 Yönetici")
    if kullanici.guild_permissions.manage_guild:
        izinler.append("⚙️ Sunucuyu Yönet")
    if kullanici.guild_permissions.manage_channels:
        izinler.append("📝 Kanalları Yönet")
    if kullanici.guild_permissions.kick_members:
        izinler.append("👢 Üyeleri At")
    if kullanici.guild_permissions.ban_members:
        izinler.append("🔨 Üyeleri Yasakla")
    
    if izinler:
        embed.add_field(
            name="🔑 Önemli İzinler",
            value=" • ".join(izinler[:5]),
            inline=False
        )
    
    embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Sunucu bilgilerini gösterir")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    
    # Kanal sayıları
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    
    # Üye durumları
    online = sum(1 for m in guild.members if m.status == discord.Status.online)
    idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
    dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
    
    # Bot sayısı
    bot_count = sum(1 for m in guild.members if m.bot)
    
    embed = discord.Embed(color=0x5865F2)
    embed.set_author(name=f"{guild.name} Sunucu Bilgileri", icon_url=guild.icon.url if guild.icon else None)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(
        name="🆔 Sunucu ID",
        value=f"```{guild.id}```",
        inline=True
    )
    embed.add_field(
        name="👑 Sunucu Sahibi",
        value=f"{guild.owner.mention}\n`{guild.owner.name}`",
        inline=True
    )
    embed.add_field(
        name="📅 Oluşturulma Tarihi",
        value=f"{guild.created_at.strftime('%d %B %Y')}\n`{(datetime.now(timezone.utc) - guild.created_at).days} gün önce`",
        inline=True
    )
    
    embed.add_field(
        name=f"👥 Üye Sayısı [{guild.member_count}]",
        value=f"🟢 Çevrimiçi: `{online}`\n🟡 Boşta: `{idle}`\n🔴 Rahatsız: `{dnd}`\n⚫ Çevrimdışı: `{offline}`\n🤖 Bot: `{bot_count}`",
        inline=True
    )
    
    embed.add_field(
        name=f"📁 Kanallar [{len(guild.channels)}]",
        value=f"💬 Metin: `{text_channels}`\n🔊 Sesli: `{voice_channels}`\n📂 Kategori: `{categories}`",
        inline=True
    )
    
    embed.add_field(
        name=f"🎭 Roller [{len(guild.roles)}]",
        value=f"En yüksek: {guild.roles[-1].mention}\n`Tüm rolleri görmek için /roleinfo kullanın`",
        inline=True
    )
    
    embed.add_field(
        name="📊 Sunucu İstatistikleri",
        value=f"😀 Emoji: `{len(guild.emojis)}`\n🎨 Sticker: `{len(guild.stickers)}`\n🚀 Boost: `{guild.premium_subscription_count}`\n⭐ Seviye: `{guild.premium_tier}`",
        inline=True
    )
    
    # Güvenlik özellikleri
    verification = {
        discord.VerificationLevel.none: "Yok",
        discord.VerificationLevel.low: "Düşük",
        discord.VerificationLevel.medium: "Orta",
        discord.VerificationLevel.high: "Yüksek",
        discord.VerificationLevel.highest: "En Yüksek"
    }
    
    embed.add_field(
        name="🔒 Güvenlik Seviyes",
        value=f"`{verification.get(guild.verification_level, 'Bilinmiyor')}`",
        inline=True
    )
    
    if guild.banner:
        embed.set_image(url=guild.banner.url)
    
    embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Kullanıcının avatarını gösterir")
@app_commands.describe(kullanici="Avatarı görüntülenecek kullanıcı")
async def avatar(interaction: discord.Interaction, kullanici: discord.Member = None):
    kullanici = kullanici or interaction.user
    
    embed = discord.Embed(color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2)
    embed.set_author(name=f"{kullanici.name} Avatar", icon_url=kullanici.avatar.url if kullanici.avatar else None)
    embed.set_image(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
    
    # Avatar linkleri
    avatar_url = kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url
    embed.add_field(
        name="🔗 Avatar Linkleri",
        value=f"[PNG]({avatar_url}?size=1024&format=png) • [JPG]({avatar_url}?size=1024&format=jpg) • [WEBP]({avatar_url}?size=1024&format=webp)",
        inline=False
    )
    
    embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="banner", description="Kullanıcının banner'ını gösterir")
@app_commands.describe(kullanici="Banner'ı görüntülenecek kullanıcı")
async def banner(interaction: discord.Interaction, kullanici: discord.Member = None):
    kullanici = kullanici or interaction.user
    
    # Kullanıcıyı fetch ederek banner bilgisini alalım
    try:
        user = await bot.fetch_user(kullanici.id)
        
        if user.banner:
            embed = discord.Embed(color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2)
            embed.set_author(name=f"{kullanici.name} Banner", icon_url=kullanici.avatar.url if kullanici.avatar else None)
            embed.set_image(url=user.banner.url)
            
            embed.add_field(
                name="🔗 Banner Linkleri",
                value=f"[PNG]({user.banner.url}?size=1024&format=png) • [JPG]({user.banner.url}?size=1024&format=jpg) • [WEBP]({user.banner.url}?size=1024&format=webp)",
                inline=False
            )
            
            embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(color=0xFF0000)
            embed.description = f"❌ {kullanici.mention} kullanıcısının banner'ı yok!"
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

        # Banner kontrolü - userinfo'ya ekle
    try:
        user = await bot.fetch_user(kullanici.id)
        if hasattr(user, 'banner') and user.banner:
            embed.set_image(url=user.banner.url)
    except:
        pass

@bot.tree.command(name="ping", description="Botun gecikme süresini gösterir")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    # Gecikme durumu
    if latency < 100:
        durum = "🟢 Mükemmel"
        color = 0x00FF00
    elif latency < 200:
        durum = "🟡 İyi"
        color = 0xFFFF00
    else:
        durum = "🔴 Yavaş"
        color = 0xFF0000
    
    embed = discord.Embed(color=color)
    embed.set_author(name="🏓 Pong!", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.add_field(name="📶 Bot Gecikmesi", value=f"`{latency}ms`\n{durum}", inline=True)
    embed.add_field(name="⚡ WebSocket", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="roleinfo", description="Rol hakkında bilgi verir")
@app_commands.describe(rol="Bilgisi görüntülenecek rol")
async def roleinfo(interaction: discord.Interaction, rol: discord.Role):
    embed = discord.Embed(color=rol.color if rol.color != discord.Color.default() else 0x2F3136)
    embed.set_author(name=f"{rol.name} Rol Bilgileri", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    
    embed.add_field(name="🆔 Rol ID", value=f"```{rol.id}```", inline=True)
    embed.add_field(name="🎨 Renk Kodu", value=f"```{str(rol.color)}```", inline=True)
    embed.add_field(name="👥 Üye Sayısı", value=f"```{len(rol.members)}```", inline=True)
    
    embed.add_field(
        name="📅 Oluşturulma Tarihi",
        value=f"{rol.created_at.strftime('%d %B %Y')}\n`{(datetime.now(timezone.utc) - rol.created_at).days} gün önce`",
        inline=True
    )
    embed.add_field(name="📊 Sıralama", value=f"```{rol.position}```", inline=True)
    embed.add_field(name="🔔 Bahsedilebilir", value="✅ Evet" if rol.mentionable else "❌ Hayır", inline=True)
    
    embed.add_field(name="🎭 Ayrı Gösterim", value="✅ Evet" if rol.hoist else "❌ Hayır", inline=True)
    embed.add_field(name="🤖 Bot Rolü", value="✅ Evet" if rol.managed else "❌ Hayır", inline=True)
    
    # İzinler
    izinler = []
    if rol.permissions.administrator:
        izinler.append("👑 Yönetici")
    if rol.permissions.manage_guild:
        izinler.append("⚙️ Sunucuyu Yönet")
    if rol.permissions.manage_roles:
        izinler.append("🎭 Rolleri Yönet")
    if rol.permissions.manage_channels:
        izinler.append("📝 Kanalları Yönet")
    if rol.permissions.kick_members:
        izinler.append("👢 Üyeleri At")
    if rol.permissions.ban_members:
        izinler.append("🔨 Üyeleri Yasakla")
    
    if izinler:
        embed.add_field(
            name=f"🔑 Önemli İzinler [{len(izinler)}]",
            value=" • ".join(izinler[:10]),
            inline=False
        )
    
    embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)

# ============== EĞLENCE KOMUTLARI ==============

@bot.tree.command(name="say", description="Bota mesaj söyletir")
@app_commands.describe(mesaj="Söylenecek mesaj")
async def say(interaction: discord.Interaction, mesaj: str):
    await interaction.response.send_message(mesaj)

@bot.tree.command(name="joke", description="Rastgele şaka yapar")
async def joke(interaction: discord.Interaction):
    jokes = [
        "Bilgisayar neden üşüdü? Çünkü pencereleri açıktı! 😄",
        "Programcı dondurma yemiyor, çünkü bug'lar eriyor! 🍦",
        "Discord botu neden mutlu? Çünkü hep online! 🤖",
        "Python neden yavaş? Çünkü yılan gibi sürünüyor! 🐍",
        "Git kullanıcısı neden üzgün? Çünkü commit etmiş! 😢",
        "Array neden bara giremiyor? Çünkü index'i yok! 🍺"
    ]
    
    embed = discord.Embed(color=0xFFD700)
    embed.set_author(name="😂 Şaka Vakti!", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.description = random.choice(jokes)
    embed.set_footer(text=f"İsteyen: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="8ball", description="Sorunuza rastgele cevap verir")
@app_commands.describe(soru="Sormak istediğiniz soru")
async def eightball(interaction: discord.Interaction, soru: str):
    responses = [
        ("✅ Kesinlikle evet!", 0x00FF00),
        ("✅ Evet, öyle görünüyor.", 0x00FF00),
        ("🤔 Belki...", 0xFFFF00),
        ("❌ Sanmıyorum.", 0xFF0000),
        ("❌ Kesinlikle hayır!", 0xFF0000),
        ("🔮 Daha sonra tekrar sor.", 0x5865F2),
        ("✨ İşaretler olumlu!", 0x00FF00),
        ("⚠️ Şüpheli...", 0xFF8C00)
    ]
    
    cevap, color = random.choice(responses)
    
    embed = discord.Embed(color=color)
    embed.set_author(name="🎱 Sihirli 8-Top", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.add_field(name="❓ Soru", value=soru, inline=False)
    embed.add_field(name="💭 Cevap", value=cevap, inline=False)
    embed.set_footer(text=f"Soran: {interaction.user.name}")
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed)

# ============== ANKET SİSTEMİ ==============

@bot.tree.command(name="poll", description="Anket oluşturur")
@app_commands.describe(soru="Anket sorusu", secenekler="Seçenekler (virgülle ayırın)")
async def poll(interaction: discord.Interaction, soru: str, secenekler: str):
    options = [s.strip() for s in secenekler.split(",")]
    
    if len(options) < 2:
        await interaction.response.send_message("❌ En az 2 seçenek girmelisiniz!", ephemeral=True)
        return
    
    if len(options) > 10:
        await interaction.response.send_message("❌ En fazla 10 seçenek girebilirsiniz!", ephemeral=True)
        return
    
    embed = discord.Embed(color=0x5865F2)
    embed.set_author(name="📊 Yeni Anket", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.title = soru
    
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    description = ""
    for i, option in enumerate(options):
        description += f"\n{emojis[i]} **{option}**"
    
    embed.description = description
    embed.set_footer(text=f"Anket oluşturan: {interaction.user.name}")
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

# ============== MÜZİK KOMUTLARI ==============

async def play_next(guild):
    if guild.id in music_queues and len(music_queues[guild.id]) > 0:
        if guild.id in voice_clients:
            voice_client = voice_clients[guild.id]
            player = music_queues[guild.id].pop(0)
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop))

@bot.tree.command(name="play", description="Şarkı çalar")
@app_commands.describe(sarki="YouTube URL'si veya şarkı adı")
async def play(interaction: discord.Interaction, sarki: str):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ Önce bir sesli kanala katılmalısınız!", ephemeral=True)
        return
    
    channel = interaction.user.voice.channel
    await interaction.response.defer()
    
    try:
        if interaction.guild.id not in voice_clients or not voice_clients[interaction.guild.id].is_connected():
            voice_client = await channel.connect()
            voice_clients[interaction.guild.id] = voice_client
        else:
            voice_client = voice_clients[interaction.guild.id]
        
        async with interaction.channel.typing():
            player = await YTDLSource.from_url(sarki, loop=bot.loop)
            
            if interaction.guild.id not in music_queues:
                music_queues[interaction.guild.id] = []
            
            if not voice_client.is_playing():
                voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(interaction.guild), bot.loop))
                
                embed = discord.Embed(color=0x1DB954)
                embed.set_author(name="🎵 Şimdi Çalıyor", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                embed.description = f"**{player.title}**"
                if player.duration:
                    mins, secs = divmod(player.duration, 60)
                    embed.add_field(name="⏱️ Süre", value=f"`{int(mins)}:{int(secs):02d}`", inline=True)
                embed.add_field(name="🎧 İsteyen", value=interaction.user.mention, inline=True)
                embed.set_footer(text="Müzik sistemi aktif")
                embed.timestamp = datetime.now()
                await interaction.followup.send(embed=embed)
            else:
                music_queues[interaction.guild.id].append(player)
                embed = discord.Embed(color=0x5865F2)
                embed.set_author(name="➕ Kuyruğa Eklendi", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                embed.description = f"**{player.title}**"
                embed.add_field(name="📊 Kuyruk Pozisyonu", value=f"`{len(music_queues[interaction.guild.id])}`", inline=True)
                embed.add_field(name="🎧 İsteyen", value=interaction.user.mention, inline=True)
                embed.set_footer(text="Sırada bekliyor...")
                await interaction.followup.send(embed=embed)
    
    except Exception as e:
        await interaction.followup.send(f"❌ Hata: {e}")

@bot.tree.command(name="skip", description="Şarkıyı atlar")
async def skip(interaction: discord.Interaction):
    if interaction.guild.id in voice_clients:
        voice_client = voice_clients[interaction.guild.id]
        if voice_client.is_playing():
            voice_client.stop()
            embed = discord.Embed(color=0xFF8C00)
            embed.set_author(name="⏭️ Şarkı Atlandı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.description = "Sıradaki şarkıya geçiliyor..."
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Şu an çalan bir şarkı yok!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bot bir sesli kanalda değil!", ephemeral=True)

@bot.tree.command(name="pause", description="Şarkıyı duraklatır")
async def pause(interaction: discord.Interaction):
    if interaction.guild.id in voice_clients:
        voice_client = voice_clients[interaction.guild.id]
        if voice_client.is_playing():
            voice_client.pause()
            embed = discord.Embed(color=0xFFFF00)
            embed.set_author(name="⏸️ Şarkı Duraklatıldı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Şu an çalan bir şarkı yok!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bot bir sesli kanalda değil!", ephemeral=True)

@bot.tree.command(name="resume", description="Şarkıyı devam ettirir")
async def resume(interaction: discord.Interaction):
    if interaction.guild.id in voice_clients:
        voice_client = voice_clients[interaction.guild.id]
        if voice_client.is_paused():
            voice_client.resume()
            embed = discord.Embed(color=0x00FF00)
            embed.set_author(name="▶️ Şarkı Devam Ediyor", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Şarkı zaten çalıyor!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bot bir sesli kanalda değil!", ephemeral=True)

@bot.tree.command(name="stop", description="Şarkıyı durdurur ve kanaldan ayrılır")
async def stop(interaction: discord.Interaction):
    if interaction.guild.id in voice_clients:
        voice_client = voice_clients[interaction.guild.id]
        music_queues[interaction.guild.id] = []
        await voice_client.disconnect()
        del voice_clients[interaction.guild.id]
        
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="⏹️ Müzik Durduruldu", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.description = "Sesli kanaldan ayrıldım ve kuyruk temizlendi."
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Bot bir sesli kanalda değil!", ephemeral=True)

@bot.tree.command(name="queue", description="Müzik kuyruğunu gösterir")
async def queue(interaction: discord.Interaction):
    if interaction.guild.id in music_queues and len(music_queues[interaction.guild.id]) > 0:
        embed = discord.Embed(color=0x5865F2)
        embed.set_author(name="📜 Müzik Kuyruğu", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        description = ""
        for i, player in enumerate(music_queues[interaction.guild.id][:10], 1):
            description += f"\n`{i}.` **{player.title}**"
        
        if len(music_queues[interaction.guild.id]) > 10:
            description += f"\n\n`ve {len(music_queues[interaction.guild.id]) - 10} şarkı daha...`"
        
        embed.description = description
        embed.set_footer(text=f"Toplam {len(music_queues[interaction.guild.id])} şarkı kuyrukta")
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="📜 Müzik Kuyruğu", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "❌ Kuyruk boş! `/play` komutu ile şarkı ekleyebilirsin."
        await interaction.response.send_message(embed=embed)

# ============== GÜVENLİK SİSTEMLERİ ==============

@bot.tree.command(name="antilink", description="Anti-link sistemini açar/kapatır")
@app_commands.describe(durum="on veya off")
async def antilink(interaction: discord.Interaction, durum: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    if durum.lower() == "on":
        anti_link_servers.add(interaction.guild.id)
        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="🔗 Anti-Link Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "✅ Anti-link sistemi **aktif edildi**!\nArtık link paylaşımları otomatik olarak silinecek."
        embed.set_footer(text=f"Aktif eden: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    elif durum.lower() == "off":
        anti_link_servers.discard(interaction.guild.id)
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="🔗 Anti-Link Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "❌ Anti-link sistemi **kapatıldı**!\nArtık linkler serbest."
        embed.set_footer(text=f"Kapatan: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)

@bot.tree.command(name="antispam", description="Anti-spam sistemini açar/kapatır")
@app_commands.describe(durum="on veya off")
async def antispam(interaction: discord.Interaction, durum: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    if durum.lower() == "on":
        anti_spam_servers.add(interaction.guild.id)
        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="🚫 Anti-Spam Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "✅ Anti-spam sistemi **aktif edildi**!\n5 saniyede 5'ten fazla mesaj spam olarak algılanacak."
        embed.set_footer(text=f"Aktif eden: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    elif durum.lower() == "off":
        anti_spam_servers.discard(interaction.guild.id)
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="🚫 Anti-Spam Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "❌ Anti-spam sistemi **kapatıldı**!"
        embed.set_footer(text=f"Kapatan: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Anti-link kontrolü
    if message.guild and message.guild.id in anti_link_servers:
        if "http://" in message.content or "https://" in message.content or "www." in message.content:
            if not message.author.guild_permissions.administrator:
                await message.delete()
                embed = discord.Embed(color=0xFF0000)
                embed.description = f"❌ {message.author.mention}, bu sunucuda link paylaşımı yasak!"
                await message.channel.send(embed=embed, delete_after=5)
                return
    
    # Anti-spam kontrolü
    if message.guild and message.guild.id in anti_spam_servers:
        user_id = message.author.id
        current_time = datetime.now()
        
        if user_id not in user_messages:
            user_messages[user_id] = []
        
        user_messages[user_id].append(current_time)
        user_messages[user_id] = [t for t in user_messages[user_id] if (current_time - t).seconds < 5]
        
        if len(user_messages[user_id]) > 5:
            if not message.author.guild_permissions.administrator:
                await message.delete()
                embed = discord.Embed(color=0xFF8C00)
                embed.description = f"⚠️ {message.author.mention}, spam yapma! Yavaşla."
                await message.channel.send(embed=embed, delete_after=5)
    
    await bot.process_commands(message)

# ============== BOT YÖNETİMİ KOMUTLARI ==============

@bot.tree.command(name="setstatus", description="Botun durum mesajını değiştirir")
@app_commands.describe(mesaj="Yeni durum mesajı")
async def setstatus(interaction: discord.Interaction, mesaj: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bu komutu sadece bot sahibi kullanabilir!", ephemeral=True)
        return
    
    await bot.change_presence(activity=discord.Game(name=mesaj))
    
    embed = discord.Embed(color=0x00FF00)
    embed.set_author(name="✅ Durum Değiştirildi", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.description = f"Yeni durum: **{mesaj}**"
    embed.timestamp = datetime.now(timezone.utc)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setactivity", description="Bot aktivitesi ayarlar")
@app_commands.describe(tur="playing, watching, listening, streaming", mesaj="Aktivite mesajı")
async def setactivity(interaction: discord.Interaction, tur: str, mesaj: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bu komutu sadece bot sahibi kullanabilir!", ephemeral=True)
        return
    
    activity_types = {
        "playing": discord.ActivityType.playing,
        "watching": discord.ActivityType.watching,
        "listening": discord.ActivityType.listening,
        "streaming": discord.ActivityType.streaming
    }
    
    if tur.lower() not in activity_types:
        await interaction.response.send_message("❌ Geçerli türler: playing, watching, listening, streaming", ephemeral=True)
        return
    
    activity = discord.Activity(type=activity_types[tur.lower()], name=mesaj)
    await bot.change_presence(activity=activity)
    
    embed = discord.Embed(color=0x00FF00)
    embed.set_author(name="✅ Aktivite Değiştirildi", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.description = f"Yeni aktivite: **{tur.capitalize()} {mesaj}**"
    embed.timestamp = datetime.now(timezone.utc)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="restart", description="Botu yeniden başlatır")
async def restart(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bu komutu sadece bot sahibi kullanabilir!", ephemeral=True)
        return
    
    embed = discord.Embed(color=0xFFFF00)
    embed.set_author(name="🔄 Bot Yeniden Başlatılıyor...", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.description = "Bot birkaç saniye içinde tekrar çevrimiçi olacak."
    await interaction.response.send_message(embed=embed)
    
    await bot.close()
    os.execv(os.sys.executable, ['python'] + os.sys.argv)

@bot.tree.command(name="shutdown", description="Botu kapatır")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bu komutu sadece bot sahibi kullanabilir!", ephemeral=True)
        return
    
    embed = discord.Embed(color=0xFF0000)
    embed.set_author(name="⚠️ Bot Kapatılıyor...", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    embed.description = "Görüşmek üzere! 👋"
    await interaction.response.send_message(embed=embed)
    
    await bot.close()

# ============== ARAMA KOMUTLARI ==============

@bot.tree.command(name="youtube", description="YouTube'da video arar")
@app_commands.describe(kelime="Aranacak kelime")
async def youtube(interaction: discord.Interaction, kelime: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        try:
            # YouTube Data API v3 (ücretsiz API key alabilirsiniz)
            search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={kelime}&type=video&maxResults=3&key=YOUR_API_KEY"
            
            # API key yoksa basit arama
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="🎥 YouTube Sonuçları", icon_url="https://cdn-icons-png.flaticon.com/512/174/174883.png")
            embed.title = f"'{kelime}' araması"
            embed.description = f"[YouTube'da ara](https://www.youtube.com/results?search_query={kelime.replace(' ', '+')})"
            
            # YouTube thumbnail
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/174/174883.png")
            
            embed.add_field(
                name="🔍 Arama İpucu",
                value="Daha iyi sonuçlar için spesifik kelimeler kullanın!",
                inline=False
            )
            
            embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

@bot.tree.command(name="google", description="Google'da arama yapar")
@app_commands.describe(soru="Aranacak soru")
async def google(interaction: discord.Interaction, soru: str):
    await interaction.response.defer()
    
    embed = discord.Embed(color=0x4285F4)
    embed.set_author(name="🔍 Google Arama", icon_url="https://cdn-icons-png.flaticon.com/512/2991/2991148.png")
    embed.title = f"'{soru}' araması"
    embed.description = f"[Google'da ara](https://www.google.com/search?q={soru.replace(' ', '+')})"
    
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2991/2991148.png")
    
    embed.add_field(
        name="💡 Hızlı Erişim",
        value="Aşağıdaki linke tıklayarak arama sonuçlarını görebilirsiniz.",
        inline=False
    )
    
    embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="imdb", description="Film/dizi bilgisi gösterir")
@app_commands.describe(film="Film veya dizi adı")
async def imdb(interaction: discord.Interaction, film: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        try:
            # OMDB API (ücretsiz: http://www.omdbapi.com/)
            # API key almanız gerekiyor
            
            embed = discord.Embed(color=0xF5C518)
            embed.set_author(name="🎬 IMDB Arama", icon_url="https://cdn-icons-png.flaticon.com/512/5977/5977585.png")
            embed.title = f"'{film}' sonuçları"
            embed.description = f"[IMDB'de ara](https://www.imdb.com/find?q={film.replace(' ', '+')})"
            
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/5977/5977585.png")
            
            embed.add_field(
                name="🎥 Film Bilgisi",
                value="IMDB'de detaylı bilgi, puanlar ve yorumlar bulabilirsiniz!",
                inline=False
            )
            
            embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.timestamp = datetime.now(timezone.utc)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

@bot.tree.command(name="anime", description="Anime bilgisi gösterir")
@app_commands.describe(isim="Anime adı")
async def anime(interaction: discord.Interaction, isim: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        try:
            # Jikan API (MyAnimeList için ücretsiz)
            url = f"https://api.jikan.moe/v4/anime?q={isim}&limit=1"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['data']:
                        anime_data = data['data'][0]
                        
                        embed = discord.Embed(
                            title=anime_data['title'],
                            url=anime_data['url'],
                            color=0x2E51A2
                        )
                        embed.set_author(name="📺 Anime Bilgisi", icon_url="https://cdn-icons-png.flaticon.com/512/3242/3242257.png")
                        
                        if anime_data.get('images'):
                            embed.set_thumbnail(url=anime_data['images']['jpg']['large_image_url'])
                        
                        if anime_data.get('synopsis'):
                            synopsis = anime_data['synopsis'][:500] + "..." if len(anime_data.get('synopsis', '')) > 500 else anime_data.get('synopsis', 'Açıklama yok')
                            embed.description = synopsis
                        
                        embed.add_field(name="⭐ Puan", value=f"`{anime_data.get('score', 'N/A')}/10`", inline=True)
                        embed.add_field(name="📺 Bölüm", value=f"`{anime_data.get('episodes', 'N/A')}`", inline=True)
                        embed.add_field(name="📅 Yıl", value=f"`{anime_data.get('year', 'N/A')}`", inline=True)
                        embed.add_field(name="🎭 Tür", value=anime_data.get('type', 'N/A'), inline=True)
                        embed.add_field(name="📊 Durum", value=anime_data.get('status', 'N/A'), inline=True)
                        
                        embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                        embed.timestamp = datetime.now(timezone.utc)
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"❌ '{isim}' adlı anime bulunamadı!")
                else:
                    await interaction.followup.send("❌ API'ye bağlanılamadı. Daha sonra tekrar deneyin.")
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

@bot.tree.command(name="manga", description="Manga bilgisi gösterir")
@app_commands.describe(isim="Manga adı")
async def manga(interaction: discord.Interaction, isim: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://api.jikan.moe/v4/manga?q={isim}&limit=1"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['data']:
                        manga_data = data['data'][0]
                        
                        embed = discord.Embed(
                            title=manga_data['title'],
                            url=manga_data['url'],
                            color=0x2E51A2
                        )
                        embed.set_author(name="📖 Manga Bilgisi", icon_url="https://cdn-icons-png.flaticon.com/512/3076/3076494.png")
                        
                        if manga_data.get('images'):
                            embed.set_thumbnail(url=manga_data['images']['jpg']['large_image_url'])
                        
                        if manga_data.get('synopsis'):
                            synopsis = manga_data['synopsis'][:500] + "..." if len(manga_data.get('synopsis', '')) > 500 else manga_data.get('synopsis', 'Açıklama yok')
                            embed.description = synopsis
                        
                        embed.add_field(name="⭐ Puan", value=f"`{manga_data.get('score', 'N/A')}/10`", inline=True)
                        embed.add_field(name="📖 Bölüm", value=f"`{manga_data.get('chapters', 'N/A')}`", inline=True)
                        embed.add_field(name="📚 Cilt", value=f"`{manga_data.get('volumes', 'N/A')}`", inline=True)
                        embed.add_field(name="🎭 Tür", value=manga_data.get('type', 'N/A'), inline=True)
                        embed.add_field(name="📊 Durum", value=manga_data.get('status', 'N/A'), inline=True)
                        
                        embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                        embed.timestamp = datetime.now(timezone.utc)
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"❌ '{isim}' adlı manga bulunamadı!")
                else:
                    await interaction.followup.send("❌ API'ye bağlanılamadı. Daha sonra tekrar deneyin.")
        except Exception as e:
            await interaction.followup.send(f"❌ Hata: {e}")

@bot.tree.command(name="steam", description="Steam oyun bilgisi gösterir")
@app_commands.describe(oyun="Oyun adı")
async def steam(interaction: discord.Interaction, oyun: str):
    await interaction.response.defer()
    
    embed = discord.Embed(color=0x171A21)
    embed.set_author(name="🎮 Steam Arama", icon_url="https://cdn-icons-png.flaticon.com/512/124/124021.png")
    embed.title = f"'{oyun}' sonuçları"
    embed.description = f"[Steam'de ara](https://store.steampowered.com/search/?term={oyun.replace(' ', '+')})"
    
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/124/124021.png")
    
    embed.add_field(
        name="🎮 Oyun Bilgisi",
        value="Steam mağazasında fiyat, özellikler ve yorumları bulabilirsiniz!",
        inline=False
    )
    
    embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.followup.send(embed=embed)

# ============== GELİŞMİŞ MODERASYON ==============

@bot.tree.command(name="slowmode", description="Kanal yavaş mod ayarı")
@app_commands.describe(sure="Saniye cinsinden süre (0 = kapalı)")
async def slowmode(interaction: discord.Interaction, sure: int):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await interaction.channel.edit(slowmode_delay=sure)
        
        embed = discord.Embed(color=0x00FF00 if sure > 0 else 0xFF0000)
        embed.set_author(name="⏱️ Yavaş Mod Ayarlandı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        if sure > 0:
            embed.description = f"✅ Bu kanalda yavaş mod **{sure} saniye** olarak ayarlandı."
        else:
            embed.description = "❌ Bu kanalda yavaş mod **kapatıldı**."
        
        embed.set_footer(text=f"Kanal: {interaction.channel.name}")
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="lock", description="Kanalı kilitler")
async def lock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="🔒 Kanal Kilitlendi", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.description = f"✅ {interaction.channel.mention} kanalı kilitlendi. Sadece yetkililer mesaj gönderebilir."
        embed.set_footer(text=f"Yetkili: {interaction.user.name}")
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="unlock", description="Kanalı açar")
async def unlock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        
        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="🔓 Kanal Açıldı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.description = f"✅ {interaction.channel.mention} kanalı açıldı. Herkes mesaj gönderebilir."
        embed.set_footer(text=f"Yetkili: {interaction.user.name}")
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="move", description="Kullanıcıyı ses kanalına taşır")
@app_commands.describe(kullanici="Taşınacak kullanıcı", kanal="Hedef ses kanalı")
async def move(interaction: discord.Interaction, kullanici: discord.Member, kanal: discord.VoiceChannel):
    if not interaction.user.guild_permissions.move_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    if not kullanici.voice:
        await interaction.response.send_message("❌ Kullanıcı bir sesli kanalda değil!", ephemeral=True)
        return
    
    try:
        await kullanici.move_to(kanal)
        
        embed = discord.Embed(color=0x5865F2)
        embed.set_author(name="🔊 Kullanıcı Taşındı", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.description = f"✅ {kullanici.mention} → {kanal.mention}"
        embed.set_footer(text=f"Yetkili: {interaction.user.name}")
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

# ============== EĞLENCE - GIF KOMUTLARI ==============

@bot.tree.command(name="hug", description="Birine sarılırsın")
@app_commands.describe(kullanici="Sarılacak kişi")
async def hug(interaction: discord.Interaction, kullanici: discord.Member):
    # Tenor API ile rastgele GIF al
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://g.tenor.com/v1/search?q=anime+hug&key=LIVDSRZULELA&limit=20") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        gif_url = random.choice(data['results'])['media'][0]['gif']['url']
                    else:
                        gif_url = "https://media.tenor.com/PLjygX8LdFEAAAAM/anime-hug.gif"
                else:
                    gif_url = "https://media.tenor.com/PLjygX8LdFEAAAAM/anime-hug.gif"
        except:
            gif_url = "https://media.tenor.com/PLjygX8LdFEAAAAM/anime-hug.gif"
    
    embed = discord.Embed(color=0xFF69B4)
    embed.set_author(name="🤗 Sarılma", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.description = f"**{interaction.user.mention}** → **{kullanici.mention}** kişisine sarıldı! 💕"
    embed.set_image(url=gif_url)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kiss", description="Birine öpücük gönderirsin")
@app_commands.describe(kullanici="Öpülecek kişi")
async def kiss(interaction: discord.Interaction, kullanici: discord.Member):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://g.tenor.com/v1/search?q=anime+kiss&key=LIVDSRZULELA&limit=20") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        gif_url = random.choice(data['results'])['media'][0]['gif']['url']
                    else:
                        gif_url = "https://media.tenor.com/9f3I6Y_3YTIAAAAM/anime-kiss.gif"
                else:
                    gif_url = "https://media.tenor.com/9f3I6Y_3YTIAAAAM/anime-kiss.gif"
        except:
            gif_url = "https://media.tenor.com/9f3I6Y_3YTIAAAAM/anime-kiss.gif"
    
    embed = discord.Embed(color=0xFF1493)
    embed.set_author(name="😘 Öpücük", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.description = f"**{interaction.user.mention}** → **{kullanici.mention}** kişisine öpücük gönderdi! 💋"
    embed.set_image(url=gif_url)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="slap", description="Birine tokat atarsın")
@app_commands.describe(kullanici="Tokat atılacak kişi")
async def slap(interaction: discord.Interaction, kullanici: discord.Member):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://g.tenor.com/v1/search?q=anime+slap&key=LIVDSRZULELA&limit=20") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        gif_url = random.choice(data['results'])['media'][0]['gif']['url']
                    else:
                        gif_url = "https://media.tenor.com/TcJ7wAk8jecAAAAM/anime-slap.gif"
                else:
                    gif_url = "https://media.tenor.com/TcJ7wAk8jecAAAAM/anime-slap.gif"
        except:
            gif_url = "https://media.tenor.com/TcJ7wAk8jecAAAAM/anime-slap.gif"
    
    embed = discord.Embed(color=0xFF4500)
    embed.set_author(name="👋 Tokat", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.description = f"**{interaction.user.mention}** → **{kullanici.mention}** kişisine tokat attı! 💥"
    embed.set_image(url=gif_url)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)

# ============== ROLLER KOMUTU (Fotoğraftaki gibi) ==============

@bot.tree.command(name="roller", description="Sunucudaki tüm rolleri gösterir")
async def roller(interaction: discord.Interaction):
    guild = interaction.guild
    roller = sorted(guild.roles[1:], key=lambda r: r.position, reverse=True)
    
    # Kategorilere ayır
    kategoriler = {
        "🏆 Yönetim": [],
        "🎨 Özel": [],
        "🎮 Oyun": [],
        "💚 Diğer": []
    }
    
    for rol in roller:
        eklendi = False
        # Yönetim rolleri
        if any(x in rol.name.lower() for x in ["admin", "mod", "yetkili", "owner"]):
            kategoriler["🏆 Yönetim"].append(rol)
            eklendi = True
        # Özel roller
        elif any(x in rol.name.lower() for x in ["vip", "boost", "premium", "special"]):
            kategoriler["🎨 Özel"].append(rol)
            eklendi = True
        # Oyun rolleri
        elif any(x in rol.name.lower() for x in ["game", "oyun", "lol", "valorant", "cs"]):
            kategoriler["🎮 Oyun"].append(rol)
            eklendi = True
        
        # Hiçbir kategoriye girmediyse "Diğer"e ekle
        if not eklendi:
            kategoriler["💚 Diğer"].append(rol)
    
    embed = discord.Embed(
        title=f"📋 {guild.name} Sunucu Rolleri",
        description=f"Toplam **{len(roller)}** rol bulunuyor\n\n",
        color=0x5865F2
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    
    # Her kategoriyi ekle
    for kategori, rol_listesi in kategoriler.items():
        if rol_listesi:
            roller_text = ""
            for rol in rol_listesi[:10]:  # Her kategoriden max 10
                roller_text += f"{rol.mention} `({len(rol.members)})`\n"
            
            if len(rol_listesi) > 10:
                roller_text += f"*+{len(rol_listesi)-10} rol daha...*\n"
            
            embed.add_field(
                name=f"{kategori} [{len(rol_listesi)}]",
                value=roller_text if roller_text else "`Rol yok`",
                inline=False
            )
    
    embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)

# ============== ÇEKİLİŞ SİSTEMİ ==============

@bot.tree.command(name="cekilis", description="Çekiliş başlatır")
@app_commands.describe(
    sure="Süre (dakika)",
    kazanan="Kazanan sayısı", 
    odul="Ödül açıklaması"
)
async def cekilis(interaction: discord.Interaction, sure: int, kazanan: int, odul: str):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
        return
    
    end_time = datetime.now(timezone.utc) + timedelta(minutes=sure)
    
    embed = discord.Embed(
        title="🎉 ÇEKİLİŞ BAŞLADI!",
        description=f"**🎁 Ödül:** {odul}\n\n🎊 Katılmak için aşağıdaki 🎉 emojisine tıklayın!",
        color=0xFF1493
    )
    embed.add_field(
        name="👥 Kazanan Sayısı",
        value=f"```{kazanan} kişi```",
        inline=True
    )
    embed.add_field(
        name="⏱️ Süre", 
        value=f"```{sure} dakika```",
        inline=True
    )
    embed.add_field(
        name="⏰ Bitiş Zamanı",
        value=f"<t:{int(end_time.timestamp())}:R>",
        inline=False
    )
    embed.set_footer(
        text=f"Çekiliş Başlatan: {interaction.user.name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    embed.set_thumbnail(url="https://media.tenor.com/M4v7yEOy_XMAAAAM/party-popper.gif")
    embed.timestamp = datetime.now(timezone.utc)
    
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await message.add_reaction("🎉")
    
    # Çekiliş bekleme
    await asyncio.sleep(sure * 60)
    
    # Güncel mesajı çek
    message = await interaction.channel.fetch_message(message.id)
    reactions = [r for r in message.reactions if str(r.emoji) == "🎉"]
    
    if reactions:
        users = []
        async for user in reactions[0].users():
            if not user.bot:
                users.append(user)
        
        if len(users) >= kazanan:
            winners = random.sample(users, kazanan)
            winner_mentions = " ".join([w.mention for w in winners])
            
            # Kazanan duyurusu
            embed_win = discord.Embed(
                title="🎊 ÇEKİLİŞ BİTTİ!",
                description=f"**🎁 Ödül:** {odul}\n\n**🏆 Kazananlar:**\n{winner_mentions}\n\n🎉 Tebrikler!",
                color=0x00FF00
            )
            embed_win.set_thumbnail(url="https://media.tenor.com/KzQXE-sM_EEAAAAM/confetti.gif")
            embed_win.timestamp = datetime.now(timezone.utc)
            
            await interaction.channel.send(content=winner_mentions, embed=embed_win)
        else:
            embed_fail = discord.Embed(
                title="❌ ÇEKİLİŞ İPTAL",
                description=f"Yeterli katılımcı yok!\n**Gerekli:** {kazanan}\n**Katılan:** {len(users)}",
                color=0xFF0000
            )
            await interaction.channel.send(embed=embed_fail)
    else:
        await interaction.channel.send("❌ Çekilişe kimse katılmadı!")

# ============== YARDIM MENÜSÜ (Kategorili) ==============

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
    
    @discord.ui.select(
        placeholder="📚 Kategori Seçin",
        options=[
            discord.SelectOption(label="📋 Tüm Komutlar", value="all", emoji="📋", description="Tüm komutları göster"),
            discord.SelectOption(label="🛡️ Moderasyon", value="mod", emoji="🛡️", description="Ban, kick, mute vs."),
            discord.SelectOption(label="🎭 Eğlence", value="fun", emoji="🎭", description="Şaka, oyun, gif komutları"),
            discord.SelectOption(label="🎵 Müzik", value="music", emoji="🎵", description="Müzik çalma komutları"),
            discord.SelectOption(label="📊 Bilgilendirme", value="info", emoji="📊", description="Kullanıcı/sunucu bilgileri"),
            discord.SelectOption(label="🔧 Ayarlar", value="settings", emoji="🔧", description="Bot ayarları"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        
        embeds = {
            "all": discord.Embed(
                title="📋 Tüm Komutlar",
                description="Bot'un tüm komutlarının listesi\n\n"
                            "🛡️ **Moderasyon:** `/ban` `/kick` `/mute` `/warn` `/clear`\n"
                            "🎭 **Eğlence:** `/joke` `/8ball` `/hug` `/kiss` `/slap` `/say`\n"
                            "🎵 **Müzik:** `/play` `/skip` `/pause` `/resume` `/stop` `/queue`\n"
                            "📊 **Bilgi:** `/userinfo` `/serverinfo` `/roleinfo` `/avatar` `/banner` `/ping`\n"
                            "🔧 **Ayarlar:** `/antilink` `/antispam` `/slowmode` `/lock` `/unlock`\n"
                            "🎁 **Diğer:** `/poll` `/cekilis` `/roller` `/rolver` `/rolal`",
                color=0x5865F2
            ),
            "mod": discord.Embed(
                title="🛡️ Moderasyon Komutları",
                description="**`/ban <kullanıcı> <sebep>`** - Kullanıcıyı yasakla\n"
                            "**`/kick <kullanıcı> <sebep>`** - Kullanıcıyı at\n"
                            "**`/mute <kullanıcı> <dakika> <sebep>`** - Sustur\n"
                            "**`/unmute <kullanıcı>`** - Susturmayı kaldır\n"
                            "**`/warn <kullanıcı> <sebep>`** - Uyarı ver\n"
                            "**`/clear <sayı>`** - Mesaj sil\n"
                            "**`/lock`** - Kanalı kilitle\n"
                            "**`/unlock`** - Kanalı aç\n"
                            "**`/slowmode <saniye>`** - Yavaş mod\n"
                            "**`/move <kullanıcı> <kanal>`** - Kullanıcıyı taşı",
                color=0xFF0000
            ),
            "fun": discord.Embed(
                title="🎭 Eğlence Komutları",
                description="**`/joke`** - Rastgele şaka\n"
                            "**`/8ball <soru>`** - Sihirli soru topu\n"
                            "**`/say <mesaj>`** - Bota mesaj söylet\n"
                            "**`/hug <kullanıcı>`** - Sarıl 🤗\n"
                            "**`/kiss <kullanıcı>`** - Öpücük gönder 😘\n"
                            "**`/slap <kullanıcı>`** - Tokat at 👋\n"
                            "**`/poll <soru> <seçenekler>`** - Anket oluştur\n"
                            "**`/cekilis <süre> <kazanan> <ödül>`** - Çekiliş başlat",
                color=0xFFD700
            ),
            "music": discord.Embed(
                title="🎵 Müzik Komutları",
                description="**`/play <şarkı>`** - Şarkı çal\n"
                            "**`/skip`** - Şarkıyı atla\n"
                            "**`/pause`** - Duraklat\n"
                            "**`/resume`** - Devam ettir\n"
                            "**`/stop`** - Durdur ve çık\n"
                            "**`/queue`** - Müzik kuyruğu",
                color=0x1DB954
            ),
            "info": discord.Embed(
                title="📊 Bilgilendirme Komutları",
                description="**`/userinfo <kullanıcı>`** - Kullanıcı bilgisi\n"
                            "**`/serverinfo`** - Sunucu bilgisi\n"
                            "**`/roleinfo <rol>`** - Rol bilgisi\n"
                            "**`/roller`** - Tüm rolleri göster\n"
                            "**`/avatar <kullanıcı>`** - Avatar göster\n"
                            "**`/banner <kullanıcı>`** - Banner göster\n"
                            "**`/ping`** - Bot gecikmesi",
                color=0x00FFFF
            ),
            "settings": discord.Embed(
                title="🔧 Ayar Komutları",
                description="**`/antilink <on/off>`** - Link engelleme\n"
                            "**`/antispam <on/off>`** - Spam engelleme\n"
                            "**`/rolver <kullanıcı> <rol>`** - Rol ver\n"
                            "**`/rolal <kullanıcı> <rol>`** - Rol al\n"
                            "**`/setstatus <mesaj>`** - Bot durumu (sadece owner)\n"
                            "**`/setactivity <tür> <mesaj>`** - Bot aktivitesi (sadece owner)",
                color=0xFF69B4
            ),
        }
        
        await interaction.response.edit_message(embed=embeds[category], view=self)

@bot.tree.command(name="yardim", description="Bot komutlarını gösterir")
async def yardim(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot Yardım Menüsü",
        description="Merhaba! Ben çok yetenekli bir Discord botuyum! 🚀\n\n"
                    "Aşağıdaki menüden kategori seçerek komutları görüntüleyebilirsin!\n\n"
                    "**📚 Kategoriler:**\n"
                    "🛡️ Moderasyon\n"
                    "🎭 Eğlence\n"
                    "🎵 Müzik\n"
                    "📊 Bilgilendirme\n"
                    "🔧 Ayarlar",
        color=0x5865F2
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text="Menüden kategori seçin!")
    embed.timestamp = datetime.now(timezone.utc)
    
    view = HelpView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Botu çalıştır - TOKEN'ı buraya yazın
import os
bot.run(os.getenv("BOT_TOKEN"))
