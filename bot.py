# bot.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio, sqlite3, json, os, random, datetime, aiohttp
from aiohttp import web
from dotenv import load_dotenv

# dotenv'i (yerel .env dosyası) yükle - Railway'de buna gerek yok ama yerel test için faydalı.
load_dotenv()

# ---------- CONFIG ----------
CONFIG_FILE = "config.json"
DB_NAME = "bot_data.db"

def load_config():
    """Konfigürasyonu dosyadan yükler veya varsayılan değerleri döndürür."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "TOKEN": os.getenv("TOKEN") or "",
        "OWNER_ID": None,
        "LOG_CHANNEL_ID": None,
        "AUTOROLE_NAME": "Üye"
    }

def save_config(cfg):
    """Konfigürasyonu dosyaya kaydeder."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

CONFIG = load_config()
TOKEN = CONFIG.get("TOKEN") or os.getenv("TOKEN")
OWNER_ID = int(CONFIG.get("OWNER_ID")) if CONFIG.get("OWNER_ID") else None # OWNER_ID'yi int'e çevir
LOG_CHANNEL_ID = int(CONFIG.get("LOG_CHANNEL_ID")) if CONFIG.get("LOG_CHANNEL_ID") else None # LOG_CHANNEL_ID'yi int'e çevir
AUTOROLE_NAME = CONFIG.get("AUTOROLE_NAME", "Üye")

# ---------- DATABASE SETUP ----------
def setup_db():
    """SQLite veritabanı tablolarını oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # voice_logs, giveaway_participants, user_messages, warns tabloları oluşturuluyor.
    # ... (Orijinal kodunuzdaki tüm tablo oluşturma komutları burada) ...
    c.execute("""CREATE TABLE IF NOT EXISTS voice_logs (user_id INTEGER PRIMARY KEY, total_voice_seconds INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS giveaway_participants (message_id INTEGER, user_id INTEGER, PRIMARY KEY (message_id, user_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_messages (user_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS warns (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER, mod_id INTEGER, reason TEXT, timestamp INTEGER)""")
    conn.commit()
    conn.close()

# ---------- GLOBAL STATE ----------
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SPAM_TRACK = {}
SPAM_LIMIT = 5
SPAM_WINDOW = 5  # seconds
LINK_BLOCK_ACTIVE = True
BANNED_LINKS = ['discord.gg', 'http://', 'https://', '.com', '.net', '.org']
VOICE_JOIN = {}  # user_id -> datetime
AFK = {}  # user_id -> reason
GIVEAWAY_TASKS = {}  # message_id -> task
PRESENCE_STATE = {"activity_type": "playing", "text": "My Boss Harry", "status": "online"}

# ---------- HELPERS ----------
def format_seconds(seconds):
    """Saniye değerini okunabilir süre formatına çevirir (G-S-D-s)."""
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days: parts.append(f"{days}g") # gün
    if hours: parts.append(f"{hours}s") # saat
    if minutes: parts.append(f"{minutes}d") # dakika
    if seconds: parts.append(f"{seconds}s") # saniye
    return " ".join(parts) if parts else "0s"

async def log_event(guild: discord.Guild, title: str, desc: str, color=discord.Color.blurple(), fields=None):
    """Belirtilen log kanalına embed gönderir."""
    if not LOG_CHANNEL_ID: return
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if not ch: return
    embed = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.datetime.utcnow())
    if fields:
        for n, v, i in fields:
            embed.add_field(name=n, value=v, inline=i)
    try:
        await ch.send(embed=embed)
    except Exception:
        pass

def owner_only(inter):
    """Komutun sadece bot sahibi tarafından kullanılıp kullanılmadığını kontrol eder."""
    return inter.user.id == OWNER_ID

# ---------- AIOHTTP SIMPLE API (Presence Endpoint) ----------
async def handle_presence(request):
    """Botun durum bilgisini JSON olarak döndürür."""
    return web.json_response(PRESENCE_STATE)

async def start_aiohttp():
    """Railway'in beklediği PORT üzerinde web sunucusunu başlatır."""
    port = int(os.environ.get("PORT", 8080))  # Railway portunu alır (varsayılan 8080)
    app = web.Application()
    app.add_routes([web.get('/', handle_presence)]) # Kök dizini de dinle (Railway kontrolü için)
    app.add_routes([web.get('/presence', handle_presence)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Presence API running on http://0.0.0.0:{port}/")

# ---------- CLIENT EVENTS ----------
@client.event
async def on_ready():
    """Bot başlatıldığında çalışır."""
    setup_db()
    await tree.sync()
    print(f"Bot ready: {client.user} (ID: {client.user.id})")
    await apply_presence_from_state()
    # AIOHTTP'yi botun event loop'unda başlat
    client.loop.create_task(start_aiohttp()) 
    print("Web server task scheduled.")

# ... (on_member_join, on_member_remove, on_message_delete, on_message_edit, on_voice_state_update, on_message olayları aynı kalır) ...
@client.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=AUTOROLE_NAME)
    if role:
        try: await member.add_roles(role)
        except Exception: pass
    await log_event(member.guild, "Üye Katıldı", f"{member.mention} sunucuya katıldı.", discord.Color.green(), fields=[("ID", f"{member.id}", True)])

@client.event
async def on_member_remove(member):
    await log_event(member.guild, "Üye Ayrıldı", f"{member.display_name} sunucudan ayrıldı.", discord.Color.red())

@client.event
async def on_message_delete(message):
    if not message.guild or message.author.bot: return
    await log_event(message.guild, "Mesaj Silindi", f"Mesaj sahibi: {message.author.mention}", discord.Color.dark_red(), fields=[("Kanal", message.channel.mention, True), ("İçerik", message.content[:400] or "Gömülü", False)])

@client.event
async def on_message_edit(before, after):
    if not before.guild or before.author.bot or before.content == after.content: return
    await log_event(before.guild, "Mesaj Düzenlendi", f"{before.author.mention} bir mesaj düzenledi.\n[Mesaja Git]({after.jump_url})", discord.Color.orange(), fields=[("Eski", before.content[:500] or "—", False), ("Yeni", after.content[:500] or "—", False)])

@client.event
async def on_voice_state_update(member, before, after):
    uid = member.id
    now = datetime.datetime.utcnow()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    delta = 0 # Delta'yı başlat
    
    # Kanal değişimini ele al
    if uid in VOICE_JOIN:
        start = VOICE_JOIN.pop(uid)
        delta = (now - start).total_seconds()
        # Sesli süreyi güncelle
        cur.execute("INSERT INTO voice_logs (user_id, total_voice_seconds) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET total_voice_seconds = total_voice_seconds + ?", (uid, int(delta), int(delta)))
        conn.commit()

    if before.channel is None and after.channel is not None:
        # Katılım
        VOICE_JOIN[uid] = now
        await log_event(member.guild, "Sesli Katılım", f"{member.mention} {after.channel.mention} kanalına katıldı.", discord.Color.blue())
    elif before.channel is not None and after.channel is None:
        # Ayrılma
        if delta > 0:
            await log_event(member.guild, "Sesli Ayrılma", f"{member.mention} {before.channel.mention} kanalından ayrıldı.", discord.Color.dark_blue(), fields=[("Süre", format_seconds(delta), False)])
        else:
             await log_event(member.guild, "Sesli Ayrılma", f"{member.mention} {before.channel.mention} kanalından ayrıldı (süre kaydı yok).", discord.Color.dark_blue())
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        # Kanal Değiştirme
        VOICE_JOIN[uid] = now
        await log_event(member.guild, "Ses Kanal Değişikliği", f"{member.mention} {before.channel.mention} -> {after.channel.mention}", discord.Color.purple(), fields=[("Son Süre", format_seconds(delta), False)])
        
    conn.close()

@client.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # AFK kaldır & uyarısı (Orijinal kodunuzdaki AFK mantığı)
    if message.author.id in AFK:
        try:
            del AFK[message.author.id]
            nick = message.author.display_name
            if nick.startswith("[AFK] "):
                try: await message.author.edit(nick=nick.replace("[AFK] ", "")[:32])
                except Exception: pass
            await message.channel.send(f"👋 {message.author.mention} AFK modundan çıktın.", delete_after=5)
        except Exception: pass

    for u_id, reason in AFK.items():
        user = client.get_user(u_id)
        if user and user in message.mentions:
            try: await message.channel.send(f"💤 {user.mention} şu anda AFK. Sebep: {reason}", delete_after=8)
            except Exception: pass

    # Link blok
    if LINK_BLOCK_ACTIVE and not message.author.guild_permissions.manage_messages:
        s = message.content.lower()
        if any(x in s for x in BANNED_LINKS):
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, bu kanalda link paylaşımı yasak!", delete_after=5)
                return
            except discord.Forbidden: pass

    # Spam kontrol
    uid = message.author.id
    now_ts = message.created_at.timestamp()
    arr = SPAM_TRACK.get(uid, [])
    arr = [t for t in arr if t > now_ts - SPAM_WINDOW]
    arr.append(now_ts)
    SPAM_TRACK[uid] = arr
    if len(arr) > SPAM_LIMIT:
        try:
            await message.author.timeout(datetime.timedelta(minutes=60), reason="Spam")
            await message.channel.send(f"🚨 {message.author.mention} spam nedeniyle 60 dakika susturuldu.", delete_after=8)
            await message.channel.purge(limit=len(arr)+1, check=lambda m: m.author.id==uid)
        except Exception:
            await message.channel.send("⚠️ Botun timeout veya purge yetkisi yok.")
        SPAM_TRACK[uid] = []

    # Mesaj sayacı
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO user_messages (user_id, count) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET count = count + 1", (uid,))
    conn.commit()
    conn.close()
    
# ---------- PRESENCE HELP ----------
async def apply_presence_from_state():
    """PRESENCE_STATE'e göre botun durumunu (presence) ayarlar."""
    try:
        a = PRESENCE_STATE.get("activity_type", "playing").lower()
        t = PRESENCE_STATE.get("text", "")
        s = PRESENCE_STATE.get("status", "online")
        st = discord.Status.online
        if s == "idle": st = discord.Status.idle
        if s == "dnd": st = discord.Status.dnd
        if s == "offline": st = discord.Status.offline
        act = None
        if a == "playing": act = discord.Game(t)
        elif a == "listening": act = discord.Activity(type=discord.ActivityType.listening, name=t)
        elif a == "watching": act = discord.Activity(type=discord.ActivityType.watching, name=t)
        elif a == "streaming": act = discord.Streaming(name=t, url="https://twitch.tv/") if t else discord.Activity(type=discord.ActivityType.playing, name=t)
        else: act = discord.Game(t)
        await client.change_presence(activity=act, status=st)
    except Exception as e:
        print("Presence apply error:", e)

# ---------- GIVEAWAY BUTTON VIEW (Tekrar tanımlamayı engellemek için kontrol edildi) ----------
try:
    class GiveawayView(discord.ui.View):
        def __init__(self, message_id, prize, winners):
            super().__init__(timeout=None)
            self.message_id = message_id
            self.prize = prize
            self.winners = winners

        @discord.ui.button(label="🎉 Çekilişe Katıl", style=discord.ButtonStyle.green, custom_id="giveaway_join")
        async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
            uid = interaction.user.id
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT * FROM giveaway_participants WHERE message_id = ? AND user_id = ?", (self.message_id, uid))
            if cur.fetchone():
                await interaction.response.send_message("❌ Zaten katıldın.", ephemeral=True)
            else:
                cur.execute("INSERT INTO giveaway_participants (message_id, user_id) VALUES (?, ?)", (self.message_id, uid))
                conn.commit()
                await interaction.response.send_message(f"✅ {interaction.user.mention} çekilişe katıldı: **{self.prize}**", ephemeral=True)
            conn.close()
except NameError:
    # GiveawayView zaten tanımlı, pas geç.
    pass


# ---------- SLASH COMMANDS ----------
# ... (Tüm slash komutları orijinal kodunuzdaki gibi burada devam eder) ...

# Komutları tekrar yazmıyorum, orijinal kodunuzdaki tüm komutlar (yardım, yasakla, mute, warn, daily, rps, çekiliş vb.) buraya kopyalanmalıdır.
# Sadece eksik/düzeltilmesi gereken bazı temel komutları ekliyorum:

@tree.command(name="yardım", description="Botun komutlarını gösterir.")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 Komutlar", color=discord.Color.blurple())
    embed.add_field(name="Moderasyon", value="/yasakla /yasakkaldir /kick /mute /unmute /warn /warnings /sil", inline=False)
    embed.add_field(name="Ekonomi", value="/balance /daily /pay /slot", inline=False)
    embed.add_field(name="Genel/Eğlence", value="/yardım /ping /sunucu /kullanici /avatar /roller /meme /joke /8ball /rps", inline=False)
    embed.add_field(name="Diğer", value="/afk /hatırlatıcı /çekiliş /status /logayarla", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="ping", description="Botun gecikme süresini gösterir.")
async def cmd_ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 **{latency}**ms")
    
@tree.command(name="kullanici", description="Kullanıcı bilgisini gösterir.")
async def cmd_kullanici(interaction: discord.Interaction, uye: discord.Member = None):
    uye = uye or interaction.user
    embed = discord.Embed(title=f"👤 {uye.display_name} Bilgileri", color=uye.color)
    embed.add_field(name="ID", value=uye.id, inline=True)
    embed.add_field(name="Katılma", value=discord.utils.format_dt(uye.joined_at, 'R'), inline=True)
    embed.add_field(name="Hesap Oluşturma", value=discord.utils.format_dt(uye.created_at, 'R'), inline=True)
    embed.set_thumbnail(url=uye.avatar.url if uye.avatar else uye.default_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ... (Diğer tüm komutlarınızı buraya yapıştırın. Örneğin yasakla, kick, sil, mute, daily, çekiliş, status vb.) ...
# (Orijinal kodunuzda olan tüm komutlar bu kısımda olmalıdır.)

@tree.command(name="yasakla", description="Üyeyi yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
async def cmd_ban(interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmedi"):
     try:
         await interaction.guild.ban(uye, reason=sebep)
         await log_event(interaction.guild, "Üye Yasaklandı", f"{uye.mention} yasaklandı. Sebep: {sebep}", discord.Color.dark_magenta(), fields=[("Yetkili", interaction.user.mention, True)])
         await interaction.response.send_message(f"✅ {uye.display_name} yasaklandı.")
     except Exception as e:
         await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)
# ...

# --- Main Bot Run ---
if __name__ == "__main__":
    if not TOKEN:
        print("FATAL HATA: Discord bot TOKEN'ı eksik. .env dosyanızı veya config.json'u kontrol edin.")
    elif OWNER_ID is None:
         print("UYARI: OWNER_ID ayarlanmamış. /status gibi sahibi gerektiren komutlar çalışmayabilir.")
    
    # Bot'u çalıştır
    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure:
        print("GİRİŞ BAŞARISIZ: Token geçersiz. Lütfen doğru bir Discord bot tokenı kullandığınızdan emin olun.")
    except Exception as e:
        print(f"Bilinmeyen hata: {e}")
