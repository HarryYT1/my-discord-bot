# bot.py (CLEANED PART 1)
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta, timezone
import random
import aiohttp
import yt_dlp
import os
import json
import time
import signal
from typing import List, Dict, Any, Optional

# ---------------------------
# BASIC CONFIG
# ---------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
# Use application commands (slash) via bot.tree

# OWNER ID (keep existing)
OWNER_ID = 911655070817456139

# Data file
DATA_FILE = "bot_data.json"

# ---------------------------
# GLOBAL STATE
# ---------------------------
warnings: Dict[str, Any] = {}
anti_link_servers: set = set()
anti_spam_servers: set = set()
user_messages: Dict[int, List[datetime]] = {}
music_queues: Dict[int, List[Any]] = {}
voice_clients: Dict[int, discord.VoiceClient] = {}
giveaways: Dict[str, Dict[str, Any]] = {}
welcome_dms: Dict[str, str] = {}
auto_responses: Dict[str, Dict[str, str]] = {}
chat_channel = None
auto_kick_owners: Dict[str, bool] = {}
auto_roles: Dict[str, int] = {}
anti_raid: set = set()
mod_log_channel: Dict[str, int] = {}

# ---------------------------
# YTDL / FFMPEG (music)
# ---------------------------
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
        self.title: str = data.get('title') or "Unknown title"
        self.url: str = data.get('url')
        self.duration: Optional[int] = data.get('duration')

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if data is None:
            raise Exception("YTDL returned no data")
        if 'entries' in data and data['entries']:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# ---------------------------
# PERSISTENCE
# ---------------------------
def load_data():
    global auto_responses, welcome_dms, auto_kick_owners, giveaways, auto_roles, anti_raid, mod_log_channel
    try:
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            auto_responses = data.get('auto_responses', {})
            welcome_dms = data.get('welcome_dms', {})
            auto_kick_owners = data.get('auto_kick_owners', {})
            giveaways = data.get('giveaways', {})
            auto_roles = data.get('auto_roles', {})
            anti_raid = set(data.get('anti_raid', []))
            mod_log_channel = data.get('mod_log_channel', {})
    except Exception as e:
        print(f"[load_data] hata: {e}")


def save_data():
    try:
        data = {
            'auto_responses': auto_responses,
            'welcome_dms': welcome_dms,
            'auto_kick_owners': auto_kick_owners,
            'giveaways': giveaways,
            'auto_roles': auto_roles,
            'anti_raid': list(anti_raid),
            'mod_log_channel': mod_log_channel
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[save_data] hata: {e}")


# ---------------------------
# UTIL / LOG
# ---------------------------
async def log_event(guild: discord.Guild, content: str):
    try:
        gid = str(guild.id)
        chan = None
        if gid in mod_log_channel:
            cid = mod_log_channel[gid]
            chan = guild.get_channel(cid)
        if not chan:
            for c in guild.text_channels:
                if c.name in ("mod-log", "logs", "modlog"):
                    chan = c
                    break
        if chan:
            await chan.send(content)
    except Exception:
        pass


# ---------------------------
# BOT EVENTS
# ---------------------------
@bot.event
async def on_ready():
    print(f"[READY] Bot çevrimiçi: {bot.user} (id: {bot.user.id})")
    load_data()
    # Start any background tasks if needed
    # Example: giveaway checker task (if implemented later)
    # you can start a loop like: giveaway_checker.start()
    try:
        await bot.change_presence(activity=discord.Game(name="/yardım | Hazır"))
    except Exception:
        pass


@bot.event
async def on_member_join(member: discord.Member):
    gid = str(member.guild.id)
    # Welcome DM
    try:
        if gid in welcome_dms:
            msg = welcome_dms[gid]
            try:
                await member.send(msg)
            except Exception:
                pass
    except Exception:
        pass

    # Auto role
    try:
        if gid in auto_roles:
            role_id = auto_roles[gid]
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                    await log_event(member.guild, f"✅ Otorol verildi: {member.mention} -> {role.name}")
                except Exception:
                    pass
    except Exception:
        pass

    # Anti-raid minimal check: if enabled and account too new, kick
    try:
        if member.guild.id in anti_raid:
            now = datetime.now(timezone.utc)
            age_days = (now - member.created_at).days
            limit_days = 7  # default; can be exposed to command later
            if age_days < limit_days:
                try:
                    await member.kick(reason="Anti-raid: hesap çok yeni")
                    await log_event(member.guild, f"⛔ Anti-raid: {member.mention} ({age_days} gün) atıldı.")
                except Exception:
                    pass
    except Exception:
        pass


@bot.event
async def on_voice_state_update(member, before, after):
    """
    Auto-kick-owner logic:
    If owner gets disconnected (before.channel and not after.channel) -> move listed admins out as well.
    This version reads auto_kick_owners per guild.
    """
    try:
        guild_id = str(member.guild.id)
        if guild_id in auto_kick_owners and auto_kick_owners[guild_id]:
            # check if owner left voice
            if before.channel and not after.channel and member.id == OWNER_ID:
                admin_ids = [
                    1194972270351892552,
                    1387115846068867156,
                    1297158864403435570
                ]
                for admin_id in admin_ids:
                    admin = member.guild.get_member(admin_id)
                    if admin and admin.voice and admin.voice.channel == before.channel:
                        try:
                            await admin.move_to(None)
                        except Exception:
                            pass
    except Exception:
        pass


@bot.event
async def on_message(message: discord.Message):
    # Process standard message handlers: anti-link, anti-spam, auto responses, chat behavior
    try:
        if message.author.bot:
            return

        if not message.guild:
            # DMs can be ignored or handle here
            return

        # Anti-link
        if message.guild.id in anti_link_servers:
            content = message.content.lower()
            if "http://" in content or "https://" in content or "www." in content:
                if not message.author.guild_permissions.administrator:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    embed = discord.Embed(color=0xFF0000)
                    embed.description = f"❌ {message.author.mention}, bu sunucuda link paylaşımı yasak!"
                    try:
                        await message.channel.send(embed=embed, delete_after=5)
                    except Exception:
                        pass
                    return

        # Anti-spam (simple rate limit)
        if message.guild.id in anti_spam_servers:
            user_id = message.author.id
            now = datetime.now()
            user_messages.setdefault(user_id, [])
            user_messages[user_id].append(now)
            # keep last 5 seconds
            user_messages[user_id] = [t for t in user_messages[user_id] if (now - t).total_seconds() < 5]
            if len(user_messages[user_id]) > 5:
                if not message.author.guild_permissions.administrator:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    embed = discord.Embed(color=0xFF8C00)
                    embed.description = f"⚠️ {message.author.mention}, spam yapma! Yavaşla."
                    try:
                        await message.channel.send(embed=embed, delete_after=5)
                    except Exception:
                        pass

        # Auto responses (per guild)
        gid = str(message.guild.id)
        if gid in auto_responses:
            content_lower = message.content.lower()
            for trigger, reply in auto_responses[gid].items():
                if trigger in content_lower:
                    try:
                        await message.channel.send(reply)
                    except Exception:
                        pass
                    break

        # Chatbot casual channel (optional hardcoded channel id)
        # Replace 1447579570294231123 with your chat channel id or remove block
        try:
            if message.channel.id == 1447579570294231123:
                text = message.content.lower()
                responses = [
                    "Merhaba! Nasılsın? 😊",
                    "Bugün nasıl gidiyor?",
                    "Ben bir botum, ama sohbet etmeyi seviyorum! 🤖",
                    "Harika bir gün, değil mi? ☀️",
                    "Sohbet etmek güzel, ne hakkında konuşalım? 💬"
                ]
                if text.startswith(("merhaba", "selam", "hey", "hi", "hello")):
                    await message.channel.send(f"Merhaba {message.author.mention}! 👋")
                elif "nasılsın" in text:
                    await message.channel.send("Teşekkür ederim, iyiyim! Sen nasılsın? 😊")
                elif message.content.endswith("?"):
                    await message.channel.send("İlginç bir soru! Biraz düşünmem gerekiyor. 🤔")
                else:
                    if random.random() > 0.7:
                        await message.channel.send(random.choice(responses))
        except Exception:
            pass

    except Exception as e:
        print(f"[on_message] hata: {e}")
    finally:
        try:
            await bot.process_commands(message)
        except Exception:
            pass


# ---------------------------
# SLASH COMMANDS - BASICS
# ---------------------------
@bot.tree.command(name="yardım", description="Bot komutlarını gösterir")
@app_commands.describe(kategori="Hangi komut kategorisini görmek istersin")
async def yardım(interaction: discord.Interaction, kategori: Optional[str] = None):
    categories = {
        "Tüm Komutlar": "Tüm komutları gösterir",
        "Moderasyon": "Moderasyon komutları",
        "Eğlence": "Eğlence komutları",
        "Müzik": "Müzik komutları",
        "Arama": "Arama komutları",
        "Güvenlik": "Güvenlik komutları",
        "Ayarlar": "Bot ayarları",
        "Extra": "Ekstra özellikler"
    }
    if not kategori:
        embed = discord.Embed(title="📚 Yardım Menüsü", color=0x5865F2)
        embed.description = "Aşağıdaki kategorilerden birini seçin:"
        for cat, desc in categories.items():
            embed.add_field(name=f"• {cat}", value=desc, inline=False)
        embed.set_footer(text="/yardım <kategori> şeklinde kullanın")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if kategori not in categories:
        await interaction.response.send_message("❌ Geçersiz kategori!", ephemeral=True)
        return

    embed = discord.Embed(title=f"📚 {kategori}", color=0x5865F2)
    if kategori == "Eğlence":
        embed.description = "**Eğlence Komutları:**"
        embed.add_field(name="/say", value="Bota mesaj söyletir", inline=False)
        embed.add_field(name="/joke", value="Rastgele şaka yapar", inline=False)
        embed.add_field(name="/8ball", value="Soruya rastgele cevap verir", inline=False)
        embed.add_field(name="/poll", value="Anket oluşturur", inline=False)
    elif kategori == "Müzik":
        embed.description = "**Müzik Komutları:**"
        embed.add_field(name="/play", value="Şarkı çalar", inline=False)
        embed.add_field(name="/skip", value="Şarkıyı atlar", inline=False)
        embed.add_field(name="/pause", value="Duraklatır", inline=False)
        embed.add_field(name="/resume", value="Devam ettirir", inline=False)
        embed.add_field(name="/stop", value="Kapatır", inline=False)
        embed.add_field(name="/queue", value="Kuyruğu gösterir", inline=False)
    else:
        embed.description = categories.get(kategori, "Kategori açıklaması yok")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="ping", description="Bot gecikmesini gösterir")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
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
    embed.set_author(name="🏓 Pong!")
    embed.add_field(name="📶 Bot Gecikmesi", value=f"`{latency}ms` • {durum}")
    embed.timestamp = datetime.now(timezone.utc)
    await interaction.response.send_message(embed=embed)


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
    embed.description = random.choice(jokes)
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
    ]
    cevap, color = random.choice(responses)
    embed = discord.Embed(color=color)
    embed.add_field(name="❓ Soru", value=soru, inline=False)
    embed.add_field(name="💭 Cevap", value=cevap, inline=False)
    await interaction.response.send_message(embed=embed)


# ---------------------------
# SEARCH COMMANDS (simple links)
# ---------------------------
@bot.tree.command(name="youtube", description="YouTube'da arama yapar")
@app_commands.describe(kelime="Aranacak kelime", gizli="Mesajı sadece sen gör (True/False)")
async def youtube(interaction: discord.Interaction, kelime: str, gizli: bool = False):
    await interaction.response.defer(ephemeral=gizli)
    search_url = f"https://www.youtube.com/results?search_query={kelime.replace(' ', '+')}"
    embed = discord.Embed(color=0xFF0000)
    embed.set_author(name="🎥 YouTube Arama Sonuçları")
    embed.title = f"'{kelime}' için YouTube Sonuçları"
    embed.add_field(name="🔗 YouTube'da Ara", value=f"[YouTube'da görüntüle]({search_url})", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=gizli)


@bot.tree.command(name="google", description="Google'da arama yapar")
@app_commands.describe(soru="Aranacak soru", gizli="Mesajı sadece sen gör (True/False)")
async def google(interaction: discord.Interaction, soru: str, gizli: bool = False):
    await interaction.response.defer(ephemeral=gizli)
    search_url = f"https://www.google.com/search?q={soru.replace(' ', '+')}"
    embed = discord.Embed(color=0x4285F4)
    embed.set_author(name="🔍 Google Arama Sonuçları")
    embed.title = f"'{soru}' için Google Sonuçları"
    embed.add_field(name="🔗 Google'da Ara", value=f"[Google'da görüntüle]({search_url})", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=gizli)


@bot.tree.command(name="imdb", description="IMDB araması yapar")
@app_commands.describe(film="Film veya dizi adı", gizli="Mesajı sadece sen gör (True/False)")
async def imdb(interaction: discord.Interaction, film: str, gizli: bool = False):
    await interaction.response.defer(ephemeral=gizli)
    search_url = f"https://www.imdb.com/find?q={film.replace(' ', '+')}"
    embed = discord.Embed(color=0xF5C518)
    embed.set_author(name="🎬 IMDB Arama Sonuçları")
    embed.title = f"'{film}' için IMDB Sonuçları"
    embed.add_field(name="🔗 IMDB'de Ara", value=f"[IMDB'de görüntüle]({search_url})", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=gizli)


# ---------------------------
# AVATAR / BANNER / ROLE COMMANDS
# ---------------------------
@app_commands.describe(kullanici="Avatarı gösterilecek kullanıcı", gizli="Mesajı sadece sen görsün mü? True/False")
async def avatar(interaction: discord.Interaction, kullanici: discord.Member = None, gizli: bool = False):

    kullanici = kullanici or interaction.user  # Eğer kullanıcı seçilmemişse komutu kullanan kişi alınır

    embed = discord.Embed(
        title=f"{kullanici.name} - Avatar",
        color=0x5865F2
    )

    # Avatar URL – Yoksa varsayılan avatar
    avatar_url = kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url

    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"İsteyen: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

    await interaction.response.send_message(embed=embed, ephemeral=gizli)

@app_commands.describe(kullanici="Banner'ı gösterilecek kullanıcı", gizli="Mesaj gizli mi?")
async def banner(interaction: discord.Interaction, kullanici: discord.Member = None, gizli: bool = False):
    kullanici = kullanici or interaction.user
    try:
        user = await bot.fetch_user(kullanici.id)
        if user.banner:
            embed = discord.Embed(color=0x5865F2)
            embed.set_author(name=f"{kullanici.name} Banner", icon_url=kullanici.avatar.url if kullanici.avatar else None)
            embed.set_image(url=user.banner.url)
            await interaction.response.send_message(embed=embed, ephemeral=gizli)
        else:
            await interaction.response.send_message("❌ Banner bulunamadı.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


@bot.tree.command(name="serverinfo", description="Sunucu bilgilerini gösterir")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    online = sum(1 for m in guild.members if m.status == discord.Status.online)
    idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
    dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
    bot_count = sum(1 for m in guild.members if m.bot)
    embed = discord.Embed(color=0x5865F2)
    embed.set_author(name=f"{guild.name} Sunucu Bilgileri", icon_url=guild.icon.url if guild.icon else None)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="🆔 Sunucu ID", value=f"```{guild.id}```", inline=True)
    embed.add_field(name="👑 Sunucu Sahibi", value=f"{guild.owner.mention}\n`{guild.owner.name}`", inline=True)
    embed.add_field(name="📅 Oluşturulma", value=f"{guild.created_at.strftime('%d %B %Y')}\n`{(datetime.now(timezone.utc)-guild.created_at).days} gün önce`", inline=True)
    embed.add_field(name=f"👥 Üyeler [{guild.member_count}]", value=f"🟢 `{online}` • 🟡 `{idle}` • 🔴 `{dnd}` • ⚫ `{offline}` • 🤖 `{bot_count}`", inline=True)
    embed.add_field(name=f"📁 Kanallar [{len(guild.channels)}]", value=f"💬 `{text_channels}` • 🔊 `{voice_channels}` • 📂 `{categories}`", inline=True)
    embed.add_field(name=f"🎭 Roller [{len(guild.roles)}]", value=f"En yüksek: {guild.roles[-1].mention if guild.roles else 'Yok'}", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rolver", description="Bir kullanıcıya rol verir")
@app_commands.describe(kullanici="Rol verilecek kullanıcı", rol="Verilecek rol")
async def rolver(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    try:
        await kullanici.add_roles(rol)
        await interaction.response.send_message(f"✅ {kullanici.mention} kullanıcısına {rol.mention} verildi.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


@bot.tree.command(name="rolal", description="Bir kullanıcıdan rol alır")
@app_commands.describe(kullanici="Rol alınacak kullanıcı", rol="Alınacak rol")
async def rolal(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    try:
        await kullanici.remove_roles(rol)
        await interaction.response.send_message(f"✅ {kullanici.mention} kullanıcısından {rol.mention} alındı.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
# ---------------------------
# PART 2 — ROLE PAGES, WELCOME DM, AUTOKICKOWNER, GIVEAWAYS, EMOJI/STICKER, OTO CEVAP, TOP, MODERASYON
# ---------------------------

# Role pages view (paginated embed)
class RolePages(discord.ui.View):
    def __init__(self, pages: List[str], timeout: int = 120):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current = 0

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current > 0:
            self.current -= 1
            embed = interaction.message.embeds[0]
            embed.description = self.pages[self.current]
            embed.set_footer(text=f"Sayfa {self.current+1}/{len(self.pages)}")
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
    async def nxt(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current < len(self.pages) - 1:
            self.current += 1
            embed = interaction.message.embeds[0]
            embed.description = self.pages[self.current]
            embed.set_footer(text=f"Sayfa {self.current+1}/{len(self.pages)}")
            await interaction.response.edit_message(embed=embed, view=self)


# ============== WELCOME DM SİSTEMİ ==============
@bot.tree.command(name="welcomedm", description="Hoş geldin DM sistemini ayarlar (on/off)")
@app_commands.describe(durum="on/off", mesaj="Özel DM mesajı (opsiyonel)")
async def welcomedm(interaction: discord.Interaction, durum: str, mesaj: Optional[str] = None):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)

    gid = str(interaction.guild.id)
    if durum.lower() == "on":
        welcome_dms[gid] = mesaj or "Sunucumuza hoş geldin! 🎉\nKuralları okumayı unutma ve iyi eğlenceler!"
        save_data()
        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="👋 Hoş Geldin DM Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "✅ Hoş geldin DM sistemi **aktif edildi**!\nYeni gelen üyelere DM gönderilecek."
        embed.add_field(name="📝 Mesaj", value=welcome_dms[gid], inline=False)
        return await interaction.response.send_message(embed=embed)
    elif durum.lower() == "off":
        if gid in welcome_dms:
            del welcome_dms[gid]
            save_data()
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="👋 Hoş Geldin DM Sistemi", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.description = "❌ Hoş geldin DM sistemi **kapatıldı**!"
        return await interaction.response.send_message(embed=embed)
    else:
        return await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)


# ============== AUTO KICK OWNER ==============
@bot.tree.command(name="autokickowner", description="Owner sesten atılınca adminleri de çıkartır (on/off)")
@app_commands.describe(durum="on/off")
async def autokickowner(interaction: discord.Interaction, durum: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Bu komutu sadece bot sahibi kullanabilir!", ephemeral=True)

    gid = str(interaction.guild.id)
    if durum.lower() == "on":
        auto_kick_owners[gid] = True
        save_data()
        embed = discord.Embed(color=0x00FF00)
        embed.set_author(name="👑 Auto Kick Owner", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.description = "✅ Auto kick owner sistemi **aktif edildi**! Owner sesten atılınca belirlenen adminler de çıkarılacak."
        return await interaction.response.send_message(embed=embed)
    elif durum.lower() == "off":
        if gid in auto_kick_owners:
            del auto_kick_owners[gid]
            save_data()
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="👑 Auto Kick Owner", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.description = "❌ Auto kick owner sistemi **kapatıldı**!"
        return await interaction.response.send_message(embed=embed)
    else:
        return await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)


# ============== GIVEAWAY (ÇEKİLİŞ) ==============
# start giveaway command
@bot.tree.command(name="çekiliş", description="Çekiliş başlatır")
@app_commands.describe(ödül="Çekiliş ödülü", süre="Süre (dakika)", kazanan="Kazanan sayısı")
async def cekilis(interaction: discord.Interaction, ödül: str, süre: int, kazanan: int = 1):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)

    if süre < 1 or süre > 10080:
        return await interaction.response.send_message("❌ Süre 1-10080 dakika arasında olmalı!", ephemeral=True)
    if kazanan < 1 or kazanan > 50:
        return await interaction.response.send_message("❌ Kazanan sayısı 1-50 arasında olmalı!", ephemeral=True)

    end_time = int((datetime.now(timezone.utc) + timedelta(minutes=süre)).timestamp())
    embed = discord.Embed(color=0xFFD700)
    embed.set_author(name="🎉 YENİ ÇEKİLİŞ!", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.title = f"🎁 Ödül: {ödül}"
    embed.add_field(name="👑 Host", value=interaction.user.mention, inline=True)
    embed.add_field(name="⏱️ Süre", value=f"<t:{end_time}:R> (<t:{end_time}:T>)", inline=True)
    embed.add_field(name="🎖️ Kazanan", value=f"`{kazanan}` kişi", inline=True)
    embed.add_field(name="🎰 Katılım", value="Katılmak için 🎉 tepkisine tıklayın!", inline=False)
    msg = await interaction.response.send_message(embed=embed)
    # fetch sent message
    message = await interaction.original_response()
    try:
        await message.add_reaction("🎉")
    except Exception:
        pass

    giveaway_id = str(message.id)
    giveaways[giveaway_id] = {
        "guild_id": interaction.guild.id,
        "channel_id": interaction.channel.id,
        "message_id": message.id,
        "host_id": interaction.user.id,
        "prize": ödül,
        "winners": kazanan,
        "end_time": end_time
    }
    save_data()


# Background checker for giveaways
async def check_giveaways():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now_ts = int(datetime.now(timezone.utc).timestamp())
        to_remove = []
        for gid, g in list(giveaways.items()):
            try:
                if now_ts >= int(g.get("end_time", 0)):
                    guild = bot.get_guild(g["guild_id"])
                    if not guild:
                        to_remove.append(gid)
                        continue
                    channel = guild.get_channel(g["channel_id"])
                    if not channel:
                        to_remove.append(gid)
                        continue
                    try:
                        message = await channel.fetch_message(g["message_id"])
                    except Exception:
                        to_remove.append(gid)
                        continue

                    # find reaction
                    reaction = None
                    for r in message.reactions:
                        if str(r.emoji) == "🎉":
                            reaction = r
                            break

                    participants = []
                    if reaction:
                        async for user in reaction.users():
                            if not user.bot:
                                participants.append(user)

                    if not participants:
                        embed = discord.Embed(color=0xFF0000)
                        embed.set_author(name="🎉 ÇEKİLİŞ SONUÇLANDI!", icon_url=guild.icon.url if guild.icon else None)
                        embed.title = f"🎁 Ödül: {g['prize']}"
                        embed.description = "❌ Katılımcı bulunamadığı için çekiliş iptal edildi!"
                        await channel.send(embed=embed)
                    else:
                        winners = random.sample(participants, min(g["winners"], len(participants)))
                        winners_mentions = " ".join(w.mention for w in winners)
                        embed = discord.Embed(color=0x00FF00)
                        embed.set_author(name="🎉 ÇEKİLİŞ SONUÇLANDI!", icon_url=guild.icon.url if guild.icon else None)
                        embed.title = f"🎁 Ödül: {g['prize']}"
                        embed.description = f"**Kazananlar:** {winners_mentions}"
                        embed.add_field(name="👑 Host", value=f"<@{g['host_id']}>", inline=True)
                        embed.add_field(name="🎖️ Kazanan Sayısı", value=f"`{len(winners)}`", inline=True)
                        embed.add_field(name="🎰 Katılımcı", value=f"`{len(participants)}`", inline=True)
                        await channel.send(f"🎉 Tebrikler {winners_mentions}! {g['prize']}", embed=embed)

                    to_remove.append(gid)
            except Exception as e:
                print(f"[check_giveaways] hata: {e}")
                to_remove.append(gid)

        for gid in to_remove:
            if gid in giveaways:
                del giveaways[gid]
        if to_remove:
            save_data()
        await asyncio.sleep(30)


# start giveaways checker task if not already
try:
    bot.loop.create_task(check_giveaways())
except Exception:
    pass


# ============== EMOJI / RANDOM EMOJI COMMANDS ==============
@bot.tree.command(name="emojiekle", description="Sunucuya emoji ekler (URL kullanılırsa çalışır)")
@app_commands.describe(emoji="Emoji URL'si veya emoji char", isim="Emoji ismi (opsiyonel)")
async def emojiekle(interaction: discord.Interaction, emoji: str, isim: Optional[str] = None):
    if not interaction.user.guild_permissions.manage_emojis:
        return await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
    await interaction.response.defer()

    try:
        if emoji.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        name = isim or "custom"
                        added = await interaction.guild.create_custom_emoji(name=name, image=data)
                        embed = discord.Embed(color=0x00FF00)
                        embed.description = f"✅ Emoji eklendi: {added} (`{added.id}`)"
                        return await interaction.followup.send(embed=embed)
                    else:
                        return await interaction.followup.send("❌ URL'den emoji alınamadı.")
        else:
            # emoji char (unicode) — can't add to server, just echo
            return await interaction.response.send_message(f"✅ Emoji: {emoji}")
    except Exception as e:
        return await interaction.followup.send(f"❌ Hata: {e}")


@bot.tree.command(name="randomemoji", description="Rastgele emoji gösterir")
async def randomemoji(interaction: discord.Interaction):
    emojis = ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🥸", "🤩", "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓"]
    selected = random.choice(emojis)
    embed = discord.Embed(color=0xFFD700)
    embed.description = f"**Emoji:** {selected}\n**Kodu:** `{selected}`"
    await interaction.response.send_message(embed=embed)


# ============== STICKER (basit) ==============
@bot.tree.command(name="stickerekle", description="Sunucuya sticker ekler (URL girin)")
@app_commands.describe(url="Sticker görüntü URL'si", isim="Sticker ismi", etiketler="Virgülle ayrılmış etiketler")
async def stickerekle(interaction: discord.Interaction, url: str, isim: str, etiketler: Optional[str] = ""):
    if not interaction.user.guild_permissions.manage_emojis_and_stickers:
        return await interaction.response.send_message("❌ Bu komutu kullanmak için yetkiniz yok!", ephemeral=True)
    await interaction.response.defer()
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send("❌ URL'den sticker alınamadı.")
                data = await resp.read()
        # discord.py sticker creation API differs between versions; try common approaches
        try:
            # For discord.py >=2.4 (experimental): Guild.stickers.create(...)
            sticker = await interaction.guild.create_sticker(name=isim, description=etiketler or None, tags=",".join([t.strip() for t in etiketler.split(",")]) if etiketler else None, file=discord.File(fp=io.BytesIO(data), filename="sticker.png"))
            return await interaction.followup.send(f"✅ Sticker eklendi: `{sticker.name}` (`{sticker.id}`)")
        except Exception:
            # Fallback: inform and provide link
            return await interaction.followup.send("❌ Sticker oluşturulamadı (botunuzun sticker izinlerini ve library sürümünü kontrol edin).")
    except Exception as e:
        return await interaction.followup.send(f"❌ Hata: {e}")


# ============== OTO CEVAP ==============
@bot.tree.command(name="otocevap", description="Otomatik cevap sistemi ekle/kaldır")
@app_commands.describe(anahtar="Anahtar kelime", cevap="Verilecek cevap", durum="on/off")
async def otocevap(interaction: discord.Interaction, anahtar: str, cevap: str, durum: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)
    gid = str(interaction.guild.id)
    if durum.lower() == "on":
        auto_responses.setdefault(gid, {})
        auto_responses[gid][anahtar.lower()] = cevap
        save_data()
        embed = discord.Embed(color=0x00FF00)
        embed.description = f"✅ Otomatik cevap eklendi: `{anahtar}` → `{cevap}`"
        return await interaction.response.send_message(embed=embed)
    elif durum.lower() == "off":
        if gid in auto_responses and anahtar.lower() in auto_responses[gid]:
            del auto_responses[gid][anahtar.lower()]
            if not auto_responses[gid]:
                del auto_responses[gid]
            save_data()
        embed = discord.Embed(color=0xFF0000)
        embed.description = f"❌ Otomatik cevap kaldırıldı: `{anahtar}`"
        return await interaction.response.send_message(embed=embed)
    else:
        return await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)


# ============== TOP (İSTATİSTİKLER) ==============
@bot.tree.command(name="top", description="Sunucu istatistiklerini gösterir")
@app_commands.describe(tür="ses/mesaj/genel")
async def top(interaction: discord.Interaction, tür: str = "genel"):
    await interaction.response.defer()
    guild = interaction.guild
    if tür == "ses":
        voice_members = [m for m in guild.members if m.voice and m.voice.channel]
        if not voice_members:
            return await interaction.followup.send("❌ Şu anda sesli kanalda kimse yok.")
        desc = ""
        for i, m in enumerate(voice_members[:10], 1):
            desc += f"`{i}.` {m.mention} — {m.voice.channel.name}\n"
        embed = discord.Embed(title="🔊 Ses İstatistikleri", description=desc, color=0x5865F2)
        embed.set_footer(text=f"Toplam: {len(voice_members)} üye")
        return await interaction.followup.send(embed=embed)
    elif tür == "mesaj":
        # placeholder
        embed = discord.Embed(title="💬 Mesaj İstatistikleri", description="Detaylı mesaj istatistikleri devre dışı.", color=0x5865F2)
        return await interaction.followup.send(embed=embed)
    else:
        online = sum(1 for m in guild.members if m.status == discord.Status.online)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
        embed = discord.Embed(title=f"{guild.name} İstatistikleri", color=0x5865F2)
        embed.add_field(name="Üyeler", value=f"Toplam: `{guild.member_count}`", inline=False)
        embed.add_field(name="Durumlar", value=f"🟢 `{online}` • 🟡 `{idle}` • 🔴 `{dnd}` • ⚫ `{offline}`", inline=False)
        return await interaction.followup.send(embed=embed)


# ============== MODERASYON KOMUTLARI ==============
@bot.tree.command(name="ban", description="Kullanıcıyı yasaklar")
@app_commands.describe(kullanici="Yasaklanacak kullanıcı", sebep="Sebep", gizli="Sadece sen görsün (True/False)")
async def ban_cmd(interaction: discord.Interaction, kullanici: discord.Member, sebep: Optional[str] = "Belirtilmedi", gizli: bool = False):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    try:
        await interaction.guild.ban(kullanici, reason=sebep)
        embed = discord.Embed(color=0xFF0000)
        embed.set_author(name="🔨 Kullanıcı Yasaklandı")
        embed.add_field(name="Kullanıcı", value=f"{kullanici.mention} (`{kullanici.id}`)")
        embed.add_field(name="Sebep", value=sebep)
        await interaction.response.send_message(embed=embed, ephemeral=gizli)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


@bot.tree.command(name="kick", description="Kullanıcıyı atar")
@app_commands.describe(kullanici="Atılacak kullanıcı", sebep="Sebep", gizli="Sadece sen görsün (True/False)")
async def kick_cmd(interaction: discord.Interaction, kullanici: discord.Member, sebep: Optional[str] = "Belirtilmedi", gizli: bool = False):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    try:
        await interaction.guild.kick(kullanici, reason=sebep)
        embed = discord.Embed(color=0xFF8C00)
        embed.set_author(name="👢 Kullanıcı Atıldı")
        embed.add_field(name="Kullanıcı", value=f"{kullanici.mention} (`{kullanici.id}`)")
        embed.add_field(name="Sebep", value=sebep)
        await interaction.response.send_message(embed=embed, ephemeral=gizli)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


async def _ensure_muted_role(guild: discord.Guild) -> discord.Role:
    role = discord.utils.get(guild.roles, name="Muted")
    if not role:
        perms = discord.Permissions(send_messages=False, speak=False)
        role = await guild.create_role(name="Muted", permissions=perms)
        # apply channel overrides if required (skipped)
    return role


@bot.tree.command(name="mute", description="Bir kullanıcıyı rol bazlı susturur")
@app_commands.describe(kullanici="Susturulacak kullanıcı", dakika="Süre (dakika, 0 = kalıcı)", sebep="Sebep", gizli="Sadece sen görsün (True/False)")
async def mute_cmd(interaction: discord.Interaction, kullanici: discord.Member, dakika: int = 0, sebep: Optional[str] = "Belirtilmedi", gizli: bool = False):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    try:
        role = await _ensure_muted_role(interaction.guild)
        await kullanici.add_roles(role)
        if dakika > 0:
            await interaction.response.send_message(f"🔇 {kullanici.mention} {dakika} dakika susturuldu.", ephemeral=gizli)
            async def _unmute_later(member_id, guild_id, role_id, delay):
                await asyncio.sleep(delay)
                try:
                    g = bot.get_guild(guild_id)
                    if not g:
                        return
                    member = g.get_member(member_id)
                    if member:
                        r = discord.utils.get(g.roles, id=role_id)
                        if r and r in member.roles:
                            await member.remove_roles(r)
                except Exception:
                    pass
            bot.loop.create_task(_unmute_later(kullanici.id, interaction.guild.id, role.id, dakika * 60))
        else:
            await interaction.response.send_message(f"🔇 {kullanici.mention} kalıcı olarak susturuldu.", ephemeral=gizli)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


@bot.tree.command(name="unmute", description="Susturmayı kaldırır")
@app_commands.describe(kullanici="Susturması kaldırılacak kişi", gizli="Sadece sen görsün (True/False)")
async def unmute_cmd(interaction: discord.Interaction, kullanici: discord.Member, gizli: bool = False):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    try:
        role = discord.utils.get(interaction.guild.roles, name="Muted")
        if role and role in kullanici.roles:
            await kullanici.remove_roles(role)
            await interaction.response.send_message(f"🔊 {kullanici.mention} artık susturulmadı.", ephemeral=gizli)
        else:
            await interaction.response.send_message("❌ Kullanıcı susturulmamış.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


@bot.tree.command(name="warn", description="Kullanıcıyı uyarır (basit)")
@app_commands.describe(kullanici="Uyarılacak kişi", sebep="Sebep", gizli="Sadece sen görsün (True/False)")
async def warn_cmd(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi", gizli: bool = False):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    gid = str(interaction.guild.id)
    gw = warnings.setdefault(gid, {})
    uw = gw.setdefault(str(kullanici.id), [])
    uw.append({"by": interaction.user.id, "reason": sebep, "time": int(time.time())})
    save_data()
    await interaction.response.send_message(f"⚠️ {kullanici.mention} uyarıldı. Sebep: {sebep}", ephemeral=gizli)


@bot.tree.command(name="clear", description="Mesajları siler (1-100)")
@app_commands.describe(sayi="Silinecek mesaj sayısı", gizli="Sadece sen görsün (True/False)")
async def clear_cmd(interaction: discord.Interaction, sayi: int, gizli: bool = False):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Yetkiniz yok.", ephemeral=True)
    if sayi < 1 or sayi > 100:
        return await interaction.response.send_message("❌ 1 ile 100 arasında bir sayı girin.", ephemeral=True)
    try:
        deleted = await interaction.channel.purge(limit=sayi)
        embed = discord.Embed(color=0x00FF00)
        embed.description = f"🧹 {len(deleted)} mesaj silindi."
        await interaction.response.send_message(embed=embed, ephemeral=gizli)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
# ============== KANAL KİLİTLEME ==============
@bot.tree.command(name="lock", description="Kanalı kilitler")
@app_commands.describe(gizli="Sadece sen gör (True/False)")
async def lock_cmd(interaction: discord.Interaction, gizli: bool = False):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

    try:
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        embed = discord.Embed(color=0xFF0000)
        embed.description = f"🔒 **Kanal kilitlendi!**"
        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


# ============== KANAL AÇMA ==============
@bot.tree.command(name="unlock", description="Kanalın kilidini açar")
@app_commands.describe(gizli="Sadece sen gör (True/False)")
async def unlock_cmd(interaction: discord.Interaction, gizli: bool = False):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

    try:
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

        embed = discord.Embed(color=0x00FF00)
        embed.description = f"🔓 **Kanal kilidi açıldı!**"
        await interaction.response.send_message(embed=embed, ephemeral=gizli)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


# ============== YAVAŞ MOD ==============
@bot.tree.command(name="slowmode", description="Kanal için yavaş mod ayarlar")
@app_commands.describe(saniye="Süre (0 = kapat)", gizli="Sadece sen gör (True/False)")
async def slowmode_cmd(interaction: discord.Interaction, saniye: int, gizli: bool = False):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

    if saniye < 0 or saniye > 21600:
        return await interaction.response.send_message("❌ Süre 0-21600 saniye olmalıdır.", ephemeral=True)

    try:
        await interaction.channel.edit(slowmode_delay=saniye)
        if saniye == 0:
            msg = "⏱️ Yavaş mod **kapatıldı**."
        else:
            msg = f"⏱️ Yavaş mod: `{saniye}` saniye olarak ayarlandı."

        embed = discord.Embed(color=0x5865F2)
        embed.description = msg
        await interaction.response.send_message(embed=embed, ephemeral=gizli)
    except Exception as e:
        return await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


# ============== KULLANICIYI SES KANALINA TAŞIMA ==============
@bot.tree.command(name="move", description="Bir kullanıcıyı ses kanalına taşır")
@app_commands.describe(kullanici="Taşınacak kullanıcı", kanal="Hedef ses kanalı")
async def move_cmd(interaction: discord.Interaction, kullanici: discord.Member, kanal: discord.VoiceChannel):
    if not interaction.user.guild_permissions.move_members:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

    try:
        if not kullanici.voice:
            return await interaction.response.send_message("❌ Kullanıcı bir ses kanalında değil.", ephemeral=True)

        await kullanici.move_to(kanal)
        embed = discord.Embed(color=0x00FF00)
        embed.description = f"👥 {kullanici.mention} → **{kanal.name}** kanalına taşındı."
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        return await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


# ============== ANTI-LINK ==============
@bot.tree.command(name="antilink", description="Sunucuda link engelleme sistemini aç/kapat")
@app_commands.describe(durum="on/off")
async def antilink_cmd(interaction: discord.Interaction, durum: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

    gid = interaction.guild.id

    if durum.lower() == "on":
        anti_link_servers.add(gid)
        embed = discord.Embed(color=0x00FF00)
        embed.description = "🛡️ Anti-link sistemi **aktif edildi**."
        return await interaction.response.send_message(embed=embed)

    elif durum.lower() == "off":
        if gid in anti_link_servers:
            anti_link_servers.remove(gid)
        embed = discord.Embed(color=0xFF0000)
        embed.description = "❌ Anti-link sistemi **kapandı**."
        return await interaction.response.send_message(embed=embed)

    await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)


# ============== ANTI-SPAM ==============
@bot.tree.command(name="antispam", description="Anti-spam sistemini aç/kapat")
@app_commands.describe(durum="on/off")
async def antispam_cmd(interaction: discord.Interaction, durum: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Yetkiniz yok!", ephemeral=True)

    gid = interaction.guild.id

    if durum.lower() == "on":
        anti_spam_servers.add(gid)
        embed = discord.Embed(color=0x00FF00)
        embed.description = "🛡️ Anti-spam sistemi **aktif edildi**."
        return await interaction.response.send_message(embed=embed)

    elif durum.lower() == "off":
        if gid in anti_spam_servers:
            anti_spam_servers.remove(gid)
        embed = discord.Embed(color=0xFF0000)
        embed.description = "❌ Anti-spam sistemi **kapandı**."
        return await interaction.response.send_message(embed=embed)

    await interaction.response.send_message("❌ Sadece 'on' veya 'off' yazabilirsiniz!", ephemeral=True)


# ============== ON MESSAGE EVENT ==============
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti-link
    if message.guild and message.guild.id in anti_link_servers:
        if any(x in message.content for x in ["http://", "https://", "www."]):
            if not message.author.guild_permissions.administrator:
                await message.delete()
                embed = discord.Embed(color=0xFF0000)
                embed.description = f"❌ {message.author.mention}, bu sunucuda link paylaşımı yasak!"
                await message.channel.send(embed=embed, delete_after=5)
                return

    # Anti-spam
    if message.guild and message.guild.id in anti_spam_servers:
        uid = message.author.id
        now = datetime.now()

        if uid not in user_messages:
            user_messages[uid] = []

        user_messages[uid].append(now)
        user_messages[uid] = [
            t for t in user_messages[uid] if (now - t).seconds < 5
        ]

        if len(user_messages[uid]) > 5:
            if not message.author.guild_permissions.administrator:
                await message.delete()
                embed = discord.Embed(color=0xFFA500)
                embed.description = f"⚠️ {message.author.mention}, spam yapma!"
                await message.channel.send(embed=embed, delete_after=5)

    # Auto-reply
    if message.guild:
        gid = str(message.guild.id)
        if gid in auto_responses:
            lower = message.content.lower()
            for key, val in auto_responses[gid].items():
                if key in lower:
                    await message.channel.send(val)
                    break

    await bot.process_commands(message)


# ============== AVATAR ==============
@bot.tree.command(name="avatar", description="Kullanıcının avatarını gösterir")
@app_commands.describe(kullanici="Avatarı görülecek kişi", gizli="Sadece sen gör (True/False)")
async def avatar_cmd(interaction: discord.Interaction, kullanici: Optional[discord.Member] = None, gizli: bool = False):
    user = kullanici or interaction.user
    embed = discord.Embed(color=0x5865F2)
    embed.set_author(name=f"{user.name} - Avatar")
    embed.set_image(url=user.avatar.url if user.avatar else user.default_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=gizli)


# ============== BANNER ==============
@bot.tree.command(name="banner", description="Kullanıcı bannerını gösterir (varsa)")
@app_commands.describe(kullanici="Bannerı görülecek kişi", gizli="Sadece sen gör (True/False)")
async def banner_cmd(interaction: discord.Interaction, kullanici: Optional[discord.Member] = None, gizli: bool = False):
    user = kullanici or interaction.user
    try:
        u = await bot.fetch_user(user.id)
        if u.banner:
            embed = discord.Embed(color=0x5865F2)
            embed.set_author(name=f"{u.name} - Banner")
            embed.set_image(url=u.banner.url)
            await interaction.response.send_message(embed=embed, ephemeral=gizli)
        else:
            await interaction.response.send_message("❌ Bu kullanıcının bannerı yok.", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Banner alınamadı.", ephemeral=True)

# ============== MÜZİK SİSTEMİ — YTDL ==============
import youtube_dl

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}

FFMPEG_OPTIONS = {
    "options": "-vn"
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


# ============== MÜZİK DEĞİŞKENLERİ ==============
music_queues = {}
voice_clients = {}


# ============== SONRAKİ ŞARKI OYNATMA ==============
async def play_next_song(guild):
    guild_id = guild.id

    if guild_id not in music_queues or len(music_queues[guild_id]) == 0:
        return

    voice_client = voice_clients.get(guild_id)
    if not voice_client:
        return

    next_player = music_queues[guild_id].pop(0)

    voice_client.play(
        next_player,
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next_song(guild), bot.loop
        )
    )


# ============== /play ==============
@bot.tree.command(name="play", description="Şarkı çalar (YouTube URL veya arama)")
@app_commands.describe(sarki="YouTube URL'si veya şarkı adı")
async def play_cmd(interaction: discord.Interaction, sarki: str):
    if not interaction.user.voice:
        return await interaction.response.send_message(
            "❌ Bir ses kanalına katılmalısın!", ephemeral=True
        )

    voice_channel = interaction.user.voice.channel
    await interaction.response.defer()

    # Bot bağlı değilse bağlan
    if interaction.guild.id not in voice_clients:
        voice_client = await voice_channel.connect()
        voice_clients[interaction.guild.id] = voice_client
    else:
        voice_client = voice_clients[interaction.guild.id]

    # Şarkıyı alıyoruz
    try:
        player = await YTDLSource.from_url(sarki, loop=bot.loop, stream=True)
    except Exception as e:
        return await interaction.followup.send(f"❌ Şarkı alınamadı: {e}")

    # Kuyruğu oluştur
    if interaction.guild.id not in music_queues:
        music_queues[interaction.guild.id] = []

    # Eğer çalmıyorsa direkt oynat
    if not voice_client.is_playing() and not voice_client.is_paused():
        voice_client.play(
            player,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next_song(interaction.guild), bot.loop
            )
        )

        embed = discord.Embed(color=0x1DB954)
        embed.set_author(
            name="🎵 Şimdi Oynatılıyor",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.description = f"**{player.title}**"
        await interaction.followup.send(embed=embed)

    else:
        music_queues[interaction.guild.id].append(player)

        embed = discord.Embed(color=0x5865F2)
        embed.set_author(
            name="➕ Kuyruğa Eklendi",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.description = f"**{player.title}**"
        embed.add_field(
            name="📊 Sıradaki Pozisyon",
            value=f"`{len(music_queues[interaction.guild.id])}`",
            inline=True
        )
        await interaction.followup.send(embed=embed)


# ============== /skip ==============
@bot.tree.command(name="skip", description="Çalan müziği atlar")
async def skip_cmd(interaction: discord.Interaction):
    gid = interaction.guild.id

    if gid in voice_clients and voice_clients[gid].is_playing():
        voice_clients[gid].stop()

        embed = discord.Embed(color=0xFF8C00)
        embed.set_author(
            name="⏭️ Şarkı Atlandı",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.description = "Sıradaki şarkıya geçiliyor..."
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Şu anda müzik çalmıyor!", ephemeral=True)


# ============== /pause ==============
@bot.tree.command(name="pause", description="Müziği duraklatır")
async def pause_cmd(interaction: discord.Interaction):
    gid = interaction.guild.id

    if gid in voice_clients and voice_clients[gid].is_playing():
        voice_clients[gid].pause()

        embed = discord.Embed(color=0xFFFF00)
        embed.set_author(
            name="⏸️ Duraklatıldı",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Şu anda müzik çalmıyor!", ephemeral=True)


# ============== /resume ==============
@bot.tree.command(name="resume", description="Müziği devam ettirir")
async def resume_cmd(interaction: discord.Interaction):
    gid = interaction.guild.id

    if gid in voice_clients and voice_clients[gid].is_paused():
        voice_clients[gid].resume()

        embed = discord.Embed(color=0x00FF00)
        embed.set_author(
            name="▶️ Devam Ediyor",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Müzik zaten oynuyor!", ephemeral=True)


# ============== /stop ==============
@bot.tree.command(name="stop", description="Müziği durdurur ve kanaldan çıkar")
async def stop_cmd(interaction: discord.Interaction):
    gid = interaction.guild.id

    if gid in voice_clients:
        vc = voice_clients[gid]

        music_queues[gid] = []
        await vc.disconnect()
        del voice_clients[gid]

        embed = discord.Embed(color=0xFF0000)
        embed.set_author(
            name="⏹️ Müzik Durduruldu",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.description = "Ses kanalından çıkıldı ve sıra temizlendi."
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Bot ses kanalında değil!", ephemeral=True)


# ============== /queue ==============
@bot.tree.command(name="queue", description="Müzik kuyruğunu gösterir")
async def queue_cmd(interaction: discord.Interaction):
    gid = interaction.guild.id

    if gid not in music_queues or len(music_queues[gid]) == 0:
        embed = discord.Embed(color=0xFF0000)
        embed.description = "❌ Kuyruk boş!"
        return await interaction.response.send_message(embed=embed)

    embed = discord.Embed(color=0x5865F2)
    embed.set_author(
        name="📜 Müzik Kuyruğu",
        icon_url=interaction.guild.icon.url if interaction.guild.icon else None
    )

    description = ""
    for i, player in enumerate(music_queues[gid][:10], 1):
        description += f"`{i}.` **{player.title}**\n"

    if len(music_queues[gid]) > 10:
        description += f"\n`{len(music_queues[gid]) - 10}` şarkı daha var..."

    embed.description = description
    await interaction.response.send_message(embed=embed)
# ---------------------------
# PART 5 — EXTRA KOMUTLAR, OWNER YÖNETİMİ, RESTART/SHUTDOWN, BOT.RUN
# ---------------------------

# ============== EĞLENCE / MİNİ ==============
@bot.tree.command(name="flip", description="Yazı tura atar")
async def flip(interaction: discord.Interaction):
    choice = random.choice(["Yazı", "Tura"])
    embed = discord.Embed(color=0xFFD700, description=f"🎲 Sonuç: **{choice}**")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="roll", description="Zar atar (1-6)")
async def roll(interaction: discord.Interaction):
    n = random.randint(1, 6)
    embed = discord.Embed(color=0xFFD700, description=f"🎲 Zar sonucu: **{n}**")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sayhi", description="Bota selam gönderir")
async def sayhi(interaction: discord.Interaction):
    await interaction.response.send_message(f"Selam {interaction.user.mention}! 👋")

# ============== POLL (Gelişmiş) ==============
@bot.tree.command(name="poll", description="Anket oluşturur (2-10 seçenek)")
@app_commands.describe(soru="Anket sorusu", secenekler="Seçenekleri virgülle ayırın")
async def poll_cmd(interaction: discord.Interaction, soru: str, secenekler: str):
    options = [s.strip() for s in secenekler.split(",") if s.strip()]
    if len(options) < 2 or len(options) > 10:
        return await interaction.response.send_message("❌ 2 ile 10 arasında seçenek girin.", ephemeral=True)

    emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    description = ""
    for i, opt in enumerate(options):
        description += f"{emojis[i]} {opt}\n"

    embed = discord.Embed(title=f"📊 {soru}", description=description, color=0x5865F2)
    embed.set_footer(text=f"Anket oluşturuldu: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    for i in range(len(options)):
        try:
            await msg.add_reaction(emojis[i])
        except Exception:
            pass

# ============== OWNER / ADMIN UTILITIES ==============
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

@bot.tree.command(name="setstatus", description="Bot statusunu değiştirir (OWNER)")
@app_commands.describe(text="Görünen durum metni")
async def setstatus(interaction: discord.Interaction, text: str):
    if not is_owner(interaction.user.id):
        return await interaction.response.send_message("❌ Bu komutu sadece owner kullanabilir.", ephemeral=True)
    try:
        await bot.change_presence(activity=discord.Game(name=text))
        await interaction.response.send_message(f"✅ Status güncellendi: `{text}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="setactivity", description="Bot aktivitesini ayarlar (playing/listening/watching/competing)")
@app_commands.describe(activity="playing/listening/watching/competing", text="Aktivite metni")
async def setactivity(interaction: discord.Interaction, activity: str, text: str):
    if not is_owner(interaction.user.id):
        return await interaction.response.send_message("❌ Sadece owner kullanabilir.", ephemeral=True)
    activity = activity.lower()
    try:
        if activity == "playing":
            act = discord.Game(name=text)
        elif activity == "listening":
            act = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif activity == "watching":
            act = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif activity == "competing":
            act = discord.Activity(type=discord.ActivityType.competing, name=text)
        else:
            return await interaction.response.send_message("❌ Geçersiz aktivite tipi.", ephemeral=True)

        await bot.change_presence(activity=act)
        await interaction.response.send_message(f"✅ Aktivite ayarlandı: {activity} `{text}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="restart", description="Botu yeniden başlatır (OWNER)")
async def restart_cmd(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        return await interaction.response.send_message("❌ Sadece owner kullanabilir.", ephemeral=True)
    await interaction.response.send_message("🔁 Bot yeniden başlatılıyor...", ephemeral=True)
    try:
        save_data()
    except Exception:
        pass
    # Attempt graceful shutdown then exit (supervisor should restart)
    await asyncio.sleep(1)
    os._exit(0)

@bot.tree.command(name="shutdown", description="Botu kapatır (OWNER)")
async def shutdown_cmd(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        return await interaction.response.send_message("❌ Sadece owner kullanabilir.", ephemeral=True)
    await interaction.response.send_message("⛔ Bot kapatılıyor...", ephemeral=True)
    try:
        save_data()
    except Exception:
        pass
    await asyncio.sleep(1)
    os._exit(0)

# ============== MAINTENANCE / UTILS ==============
@bot.tree.command(name="save", description="Verileri kaydeder (OWNER)")
async def save_cmd(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        return await interaction.response.send_message("❌ Sadece owner kullanabilir.", ephemeral=True)
    try:
        save_data()
        await interaction.response.send_message("✅ Veriler kaydedildi.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="load", description="Verileri yükler (OWNER)")
async def load_cmd(interaction: discord.Interaction):
    if not is_owner(interaction.user.id):
        return await interaction.response.send_message("❌ Sadece owner kullanabilir.", ephemeral=True)
    try:
        load_data()
        await interaction.response.send_message("✅ Veriler yüklendi.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)


# ============== ERROR HANDLING FOR APP COMMANDS ==============
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    try:
        # Most common: MissingPermissions, MissingRequiredArgument, CommandInvokeError
        await interaction.response.send_message(f"❌ Komut hatası: {error}", ephemeral=True)
    except Exception:
        pass
    print(f"[app_command_error] {error}")


# ============== GRACEFUL EXIT HANDLER ==============
def _shutdown_handler(*args):
    try:
        save_data()
    except Exception:
        pass
    try:
        loop = asyncio.get_event_loop()
        loop.stop()
    except Exception:
        pass

try:
    signal.signal(signal.SIGINT, lambda s, f: _shutdown_handler())
    signal.signal(signal.SIGTERM, lambda s, f: _shutdown_handler())
except Exception:
    pass


# ============== LAUNCH (TOKEN) ==============
# Token from env or token.txt fallback
TOKEN = os.getenv("bot_token")
if not TOKEN:
    try:
        with open("token.txt", "r", encoding="utf-8") as tf:
            TOKEN = tf.read().strip()
    except Exception:
        TOKEN = None

if __name__ == "__main__":
    if not TOKEN:
        print("❌ HATA: Bot tokeni bulunamadı! TOKEN değişkenini kontrol et.")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Bot başlatılamadı: {e}")

