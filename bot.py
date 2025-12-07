import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio 
import json 
import os 
import sqlite3 
import random 

# --- DOSYA VE DB YÖNETİMİ ---
CONFIG_FILE = 'config.json'
DB_NAME = 'bot_data.db' 

def load_config():
    """Konfigürasyonu dosyadan yükler veya yoksa varsayılan değerleri döndürür."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("UYARI: config.json dosyası bozuk. Varsayılan ayarlar kullanılıyor.")
            return {"LOG_KANAL_ID": None}
    return {"LOG_KANAL_ID": None} 

def save_config(config):
    """Konfigürasyonu dosyaya kaydeder."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def setup_db():
    """SQLite veritabanını ve gerekli tabloları oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_logs (
            user_id INTEGER PRIMARY KEY,
            total_voice_seconds INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS giveaway_participants (
            message_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (message_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_messages (
            user_id INTEGER PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- CONFIG VE AYARLAR ---
CONFIG = load_config() 

SPAM_TAKIP = {}
SPAM_LIMIT = 5   
SPAM_ZAMAN = 5   
LINK_ENGEL_AKTIF = True 
TOKEN = '' 
OTOMATIK_ROL_ADI = "Üye" 
AFK_DURUMU = {} 
YASAKLI_LINKLER = ['discord.gg', 'http://', 'https://', '.com', '.net', '.org'] 

VOICE_JOIN_TIMES = {} 
CEKILIS_EMOJI = "🎉"

# --- CLIENT VE TREE TANIMLAMA ---
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- DÜĞME (BUTTON) ETKİLEŞİMİ SINIFI ---
class CekilisKatilim(discord.ui.View):
    def __init__(self, message_id, prize, winner_count, timeout=None):
        super().__init__(timeout=timeout)
        self.message_id = message_id
        self.prize = prize
        self.winner_count = winner_count

    @discord.ui.button(label="🎉 Çekilişe Katıl", style=discord.ButtonStyle.green, custom_id="katil_button")
    async def katil_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM giveaway_participants WHERE message_id = ? AND user_id = ?",
            (self.message_id, user_id)
        )
        is_participating = cursor.fetchone()
        
        if is_participating:
            await interaction.response.send_message(
                "❌ Zaten bu çekilişe katılmışsın!", 
                ephemeral=True
            )
        else:
            cursor.execute(
                "INSERT INTO giveaway_participants (message_id, user_id) VALUES (?, ?)",
                (self.message_id, user_id)
            )
            conn.commit()
            await interaction.response.send_message(
                f"✅ **{self.prize}** çekilişine başarıyla katıldın!", 
                ephemeral=True
            )
            
        conn.close()


# --- YARDIMCI FONKSİYONLAR ---

def durum_cevir(status):
    ceviriler = {
        discord.Status.online: "🟢 Çevrimiçi",
        discord.Status.idle: "🌙 Boşta",
        discord.Status.dnd: "⛔ Rahatsız Etmeyin",
        discord.Status.offline: "⚫ Çevrimdışı/Görünmez",
        discord.Status.do_not_disturb: "⛔ Rahatsız Etmeyin"
    }
    return ceviriler.get(status, "Bilinmiyor")

def format_seconds(seconds):
    """Saniyeyi Gün, Saat, Dakika, Saniye formatına çevirir."""
    if seconds is None or seconds == 0:
        return "0 Saniye"
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days: parts.append(f"**{days}** Gün")
    if hours: parts.append(f"**{hours}** Saat")
    if minutes: parts.append(f"**{minutes}** Dakika")
    if seconds: parts.append(f"**{seconds}** Saniye")
    
    return " ".join(parts) if parts else "0 Saniye"

async def check_afk_status(member: discord.Member, channel: discord.TextChannel = None):
    """Üyenin AFK durumunu kontrol eder ve varsa kaldırır."""
    global AFK_DURUMU
    user_id = member.id
    
    if user_id in AFK_DURUMU:
        try:
            del AFK_DURUMU[user_id]
            display_name_clean = member.display_name.replace('[AFK] ', '')
            if len(display_name_clean) > 32:
                 display_name_clean = display_name_clean[:32]
                 
            await member.edit(nick=display_name_clean)
            
            if channel:
                await channel.send(f"👋 **{member.mention}**, AFK durumundan başarıyla çıktın.", delete_after=5)
            return True
        except Exception:
            return False
    return False

async def log_event(guild, title, description, color, fields=None):
    log_id = CONFIG.get("LOG_KANAL_ID") 
    if not log_id:
        return
    
    try:
        log_channel = guild.get_channel(log_id)
    except Exception:
        return

    if not log_channel:
        return
        
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    
    embed.set_footer(text=f"Bot ID: {client.user.id}")
    
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

    try:
        await log_channel.send(embed=embed)
    except discord.Forbidden:
        pass 

# --- EVENTLER (OLAYLAR) ---

@client.event
async def on_ready():
    setup_db() 
    await tree.sync() 

    await client.change_presence(
        activity=discord.Game("𝐌𝐲 𝐁𝐨𝐬𝐬 𝐇𝐚𝐫𝐫𝐲"), 
        status=discord.Status.online
    )

    print(f'Bot olarak giriş yaptık: {client.user}') 
    print(f'Log Kanal ID: {CONFIG["LOG_KANAL_ID"] or "AYARLANMAMIŞ"}')
    print('----------------------------------')
    print('TÜM SLASH KOMUTLARI VE VERİTABANI BAŞARIYLA HAZIRLANDI.')

@tree.error 
async def on_tree_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions) or isinstance(error, app_commands.MissingAnyPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ **HATA:** Bu komutu kullanmaya yetkin yok!", 
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ **HATA:** Bu komutu kullanmaya yetkin yok!", 
                ephemeral=True
            )
        return
    
    print(f"Komut çalıştırılırken beklenmedik bir hata oluştu: {error}")
    
    if not interaction.response.is_done():
        try:
            await interaction.response.send_message(
                f"❌ **HATA OLUŞTU:** Komut çalıştırılırken beklenmedik bir hata oluştu.", 
                ephemeral=True
            )
        except Exception:
            pass 

@client.event
async def on_member_join(member):
    try:
        role = discord.utils.get(member.guild.roles, name=OTOMATIK_ROL_ADI)
        if role:
            await member.add_roles(role)
    except discord.Forbidden:
        pass
        
    fields = [
        ("Kullanıcı ID", f"`{member.id}`", True),
        ("Discord Kayıt Tarihi", discord.utils.format_dt(member.created_at, "R"), False)
    ]
    await log_event(
        member.guild,
        "🟢 Üye Katıldı",
        f"**{member.mention}** ({member.display_name}) sunucuya katıldı.\n**Kayıt Durumu**: {'Yeni Hesap' if (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days < 7 else 'Eski Hesap'}",
        discord.Color.green(),
        fields=fields
    )

@client.event
async def on_member_remove(member):
    fields = [
        ("Kullanıcı ID", f"`{member.id}`", True),
        ("Sunucuda Kalma Süresi", f"{(datetime.datetime.now(datetime.timezone.utc) - member.joined_at).days} Gün", False)
    ]
    await log_event(
        member.guild,
        "🔴 Üye Ayrıldı",
        f"**{member.display_name}** sunucudan ayrıldı. Ayrılmadan önceki toplam üye: **{member.guild.member_count + 1}**",
        discord.Color.red(),
        fields=fields
    )

@client.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
        
    await log_event(
        message.guild,
        "🗑️ Mesaj Silindi",
        f"**{message.author.mention}** tarafından gönderilen bir mesaj silindi.",
        discord.Color.dark_red(),
        fields=[
            ("Kanal", message.channel.mention, True),
            ("Mesaj ID", f"`{message.id}`", True),
            ("İçerik Önizlemesi", f"```{message.content[:500]}```" if message.content else "*Gömülü mesaj veya dosya*", False)
        ]
    )

@client.event
async def on_message_edit(before, after):
    if before.content == after.content or before.author.bot or not before.guild:
        return

    await log_event(
        before.guild,
        "📝 Mesaj Düzenlendi",
        f"**{before.author.mention}** bir mesajı {before.channel.mention} kanalında düzenledi.",
        discord.Color.orange(),
        fields=[
            ("Link", f"[Mesaja Git]({after.jump_url})", False),
            ("Eski İçerik", f"```{before.content[:500]}```", False),
            ("Yeni İçerik", f"```{after.content[:500]}```", False)
        ]
    )
    
@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None or after.channel is not None:
        await check_afk_status(member)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    user_id = member.id
    
    if before.channel is None and after.channel is not None:
        VOICE_JOIN_TIMES[user_id] = now
        await log_event(
            member.guild,
            "🔊 Sesli Kanala Katıldı",
            f"**{member.display_name}** {after.channel.mention} kanalına katıldı.",
            discord.Color.blue(),
            fields=[("Kullanıcı ID", f"`{user_id}`", False)]
        )
    
    elif before.channel is not None and after.channel is None:
        duration = 0
        if user_id in VOICE_JOIN_TIMES:
            join_time = VOICE_JOIN_TIMES.pop(user_id)
            duration = (now - join_time).total_seconds()
            
            cursor.execute(
                "INSERT INTO voice_logs (user_id, total_voice_seconds) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET total_voice_seconds = total_voice_seconds + ?",
                (user_id, duration, duration)
            )
            conn.commit()
            
            await log_event(
                member.guild,
                "🔇 Sesli Kanaldan Ayrıldı",
                f"**{member.display_name}** {before.channel.mention} kanalından ayrıldı.",
                discord.Color.dark_blue(),
                fields=[
                    ("Kullanıcı ID", f"`{user_id}`", True),
                    ("Kanalda Kalma Süresi", format_seconds(duration), False)
                ]
            )
        else:
             await log_event(
                member.guild,
                "🔇 Sesli Kanaldan Ayrıldı",
                f"**{member.display_name}** {before.channel.mention} kanalından ayrıldı. Süre hesaplanamadı (Bot yeniden başlatıldı).",
                discord.Color.dark_blue(),
            )

    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        duration = 0
        if user_id in VOICE_JOIN_TIMES:
            join_time = VOICE_JOIN_TIMES.pop(user_id)
            duration = (now - join_time).total_seconds()

            cursor.execute(
                "INSERT INTO voice_logs (user_id, total_voice_seconds) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET total_voice_seconds = total_voice_seconds + ?",
                (user_id, duration, duration)
            )
            
            VOICE_JOIN_TIMES[user_id] = now
            conn.commit()
        
        await log_event(
            member.guild,
            "➡️ Sesli Kanal Değiştirdi",
            f"**{member.display_name}** {before.channel.mention} kanalından {after.channel.mention} kanalına geçti.",
            discord.Color.purple(),
            fields=[
                ("Kullanıcı ID", f"`{user_id}`", True),
                ("Önceki Kanal Süresi", format_seconds(duration), False)
            ]
        )
    
    conn.close()

@client.event
async def on_message(message):
    global SPAM_TAKIP, AFK_DURUMU

    if message.author.bot:
        return

    await check_afk_status(message.author, message.channel)

    for user_id_afk, sebep in AFK_DURUMU.items():
        if client.get_user(user_id_afk) in message.mentions:
            afk_kullanici = client.get_user(user_id_afk)
            await message.channel.send(f"💤 **{afk_kullanici.mention}** şu anda AFK. Sebep: **{sebep}**", delete_after=10)

    if LINK_ENGEL_AKTIF:
        mesaj_icerigi = message.content.lower()
        if any(link in mesaj_icerigi for link in YASAKLI_LINKLER) and not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"🚫 **{message.author.mention}**, bu kanalda link paylaşımına izin verilmiyor!", delete_after=5)
            except discord.Forbidden:
                pass

    user_id = message.author.id
    current_time = message.created_at.timestamp()
    
    if user_id not in SPAM_TAKIP:
        SPAM_TAKIP[user_id] = []
    
    SPAM_TAKIP[user_id] = [t for t in SPAM_TAKIP[user_id] if t > current_time - SPAM_ZAMAN]
    SPAM_TAKIP[user_id].append(current_time)
    
    if len(SPAM_TAKIP[user_id]) > SPAM_LIMIT:
        try:
            await message.author.timeout(datetime.timedelta(minutes=60), reason="Spam yapma")
            
            await log_event(
                message.guild,
                "🛡️ Otomatik Susturma (Anti-Spam)",
                f"**{message.author.mention}** spam yaptığı için otomatik olarak 60 dakika susturuldu.",
                discord.Color.darker_grey(),
                fields=[
                    ("Kullanıcı ID", f"`{message.author.id}`", False),
                    ("Süre", "60 Dakika", False)
                ]
            )

            await message.channel.send(
                f"🚨 **{message.author.mention}**, spam yaptığın için 1 saat susturuldun. 🚨",
                delete_after=10
            )
            await message.channel.purge(limit=len(SPAM_TAKIP[user_id]), check=lambda m: m.author == message.author)
        except discord.Forbidden:
            await message.channel.send("⚠️ Botun susturma veya mesaj silme izni yok!")
            
        SPAM_TAKIP[user_id] = [] 
        

# --- SLASH KOMUTLARI (COMMANDS) ---

# /yardım
@tree.command(name="yardım", description="Botun tüm komutlarını kategorilere ayrılmış bir şekilde gösterir.")
async def yardim_komutu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 BOT KOMUT VE MODÜLLERİ",
        description=f"Botumuzdaki tüm aktif sistem ve komutlara hızlı erişim.\n\n"
                    f"**My Boss Harry Destek Sunucusu:** discord.gg/bJNh74tqRz",
        color=discord.Color.dark_teal()
    )

    embed.add_field(
        name="🛡️ Yönetim & Moderasyon",
        value="`/yasakla`, `/yasakkaldir`, `/kilit`, `/sil`, `/logayarla`",
        inline=False
    )

    embed.add_field(
        name="🎁 Çekiliş Sistemi",
        value="`/çekiliş` (Butonlu ve ephemeral onay mesajlı)",
        inline=False
    )

    embed.add_field(
        name="📊 Analiz & Bilgi Sistemleri",
        value="`/kullanici`, `/koruma`, `/avatar`, `/roller`, `/sunucu`",
        inline=False
    )

    embed.add_field(
        name="🛠️ Kullanıcı Araçları",
        value="`/afk`, `/hatırlatıcı`",
        inline=False
    )

    embed.add_field(
        name="🔊 Sesli Kanal Araçları",
        value="`/çek`, `/taşı`",
        inline=False
    )

    embed.set_footer(text="Komutları kullanmak için sohbet kutusuna '/' yazın.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# 1. /çekiliş 
@tree.command(name="çekiliş", description="Yeni bir çekiliş başlatır.")
@app_commands.checks.has_permissions(manage_guild=True)
async def cekilis_komutu(
    interaction: discord.Interaction, 
    süre_dakika: app_commands.Range[int, 1, 1440], 
    kazanan_sayisi: app_commands.Range[int, 1, 10], 
    ödül: str
):
    channel = interaction.channel
    end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=süre_dakika)
    
    embed = discord.Embed(
        title="🎉 ÇEKİLİŞ BAŞLADI 🎉",
        description="Katılmak için aşağıdaki **'🎉 Çekilişe Katıl'** düğmesine tıklayın!", 
        color=discord.Color.yellow()
    )
    embed.add_field(name="🎁 Ödül", value=ödül, inline=False)
    embed.add_field(name="👤 Kazanacak Kişi Sayısı", value=str(kazanan_sayisi), inline=True)
    embed.add_field(name="⏰ Bitiş Zamanı", value=discord.utils.format_dt(end_time, "R"), inline=True)
    embed.set_footer(text=f"Başlatan: {interaction.user.display_name}")
    
    await interaction.response.send_message(f"✅ Çekiliş **{channel.mention}** kanalında başlatıldı!", ephemeral=True)
    
    view = CekilisKatilim(
        message_id=0,
        prize=ödül, 
        winner_count=kazanan_sayisi,
        timeout=süre_dakika * 60 
    )
    
    cekilis_mesaj = await channel.send(
        embed=embed, 
        view=view
    )
    
    view.message_id = cekilis_mesaj.id
    await cekilis_mesaj.edit(view=view)
    
    await asyncio.sleep(süre_dakika * 60)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT user_id FROM giveaway_participants WHERE message_id = ?",
        (cekilis_mesaj.id,)
    )
    participant_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("DELETE FROM giveaway_participants WHERE message_id = ?", (cekilis_mesaj.id,))
    conn.commit()
    conn.close()
    
    try:
        guncel_mesaj = await channel.fetch_message(cekilis_mesaj.id)
    except discord.NotFound:
        return

    katilimcilar = []
    for user_id in participant_ids:
        user = interaction.guild.get_member(user_id)
        if user and not user.bot:
            katilimcilar.append(user)

    if katilimcilar:
        kazanan_sayisi = min(kazanan_sayisi, len(katilimcilar))
        kazananlar = random.sample(katilimcilar, kazanan_sayisi)

        kazananlar_mention = " ".join([k.mention for k in kazananlar])
        
        kazanan_embed = discord.Embed(
            title="🎉 ÇEKİLİŞ SONUCU 🎉",
            description=f"Tebrikler, **{ödül}** ödülünü kazananlar belli oldu!",
            color=discord.Color.gold()
        )
        kazanan_embed.add_field(name="🎁 Ödül", value=ödül, inline=False)
        kazanan_embed.add_field(name="🏆 Kazananlar", value=kazananlar_mention, inline=False)
        kazanan_embed.set_footer(text="Çekiliş sona erdi.")
        
        await channel.send(
            f"🎉 **ÇEKİLİŞ SONA ERDİ!** {kazananlar_mention} tebrikler, **{ödül}** kazandınız!",
            embed=kazanan_embed
        )
        
        await guncel_mesaj.edit(embed=kazanan_embed, view=None)

    else:
        bitis_embed = discord.Embed(
            title="❌ ÇEKİLİŞ SONA ERDİ",
            description="Yeterli katılımcı olmadığı için kazanan belirlenemedi.",
            color=discord.Color.red()
        )
        await channel.send("Yeterli katılım sağlanamadı.", embed=bitis_embed)
        await guncel_mesaj.edit(embed=bitis_embed, view=None)


# 2. /logayarla 
@tree.command(name="logayarla", description="Log kanalını belirler.")
@app_commands.checks.has_permissions(administrator=True)
async def log_ayarla_komutu(interaction: discord.Interaction, kanal: discord.TextChannel):
    global CONFIG
    
    CONFIG["LOG_KANAL_ID"] = kanal.id
    save_config(CONFIG)
    
    await interaction.response.send_message(
        f"✅ **LOG Sistemi** başarıyla güncellendi!\n"
        f"Loglar artık {kanal.mention} kanalına gönderilecektir.",
        ephemeral=True
    )

# 3. /yasakla Komutu 
@tree.command(name="yasakla", description="Belirtilen üyeyi sunucudan yasaklar.")
@app_commands.checks.has_permissions(ban_members=True)
async def yasakla_komutu(interaction: discord.Interaction, uye: discord.Member, sebep: str = "Sebep belirtilmemiş"):
    try:
        await uye.ban(reason=sebep)
        
        await log_event(
            interaction.guild,
            "🔨 Üye Yasaklandı",
            f"**{uye.mention}** sunucudan yasaklandı.",
            discord.Color.dark_magenta(),
            fields=[
                ("Yetkili", interaction.user.mention, True),
                ("Kullanıcı ID", f"`{uye.id}`", True),
                ("Sebep", sebep, False)
            ]
        )
        await interaction.response.send_message(f'✅ **{uye.display_name}** sunucudan yasaklandı. Sebep: **{sebep}**', ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Botun bu üyeyi yasaklamak için yeterli izni yok.", ephemeral=True)

# 4. /yasakkaldir 
@tree.command(name="yasakkaldir", description="Yasaklı bir üyeyi ID ile sunucudan yasağını kaldırır.")
@app_commands.checks.has_permissions(ban_members=True)
async def yasak_kaldir_komutu(interaction: discord.Interaction, kullanici_id: str, sebep: str = "Sebep belirtilmemiş"):
    try:
        member_id = int(kullanici_id)
    except ValueError:
        await interaction.response.send_message("❌ **HATA:** Geçerli bir Kullanıcı ID'si girmediniz (sadece rakam olmalı).", ephemeral=True)
        return

    try:
        banned_users = [entry.user for entry in await interaction.guild.bans()]
        member_to_unban = discord.utils.get(banned_users, id=member_id)

        if not member_to_unban:
            await interaction.response.send_message(f"❌ **HATA:** `{kullanici_id}` ID'sine sahip yasaklı bir kullanıcı bulunamadı.", ephemeral=True)
            return

        await interaction.guild.unban(member_to_unban, reason=sebep)
        
        await log_event(
            interaction.guild,
            "✅ Üye Yasağı Kaldırıldı",
            f"**{member_to_unban.name}** kullanıcısının yasağı kaldırıldı.",
            discord.Color.dark_green(),
            fields=[
                ("Yetkili", interaction.user.mention, True),
                ("Kullanıcı ID", f"`{kullanici_id}`", True),
                ("Sebep", sebep, False)
            ]
        )
        
        await interaction.response.send_message(f'✅ **{member_to_unban.name}** kullanıcısının yasağı başarıyla kaldırıldı. Sebep: **{sebep}**', ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message("Botun yasağı kaldırmak için yeterli izni yok.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Beklenmedik bir hata oluştu: `{e}`", ephemeral=True)


# 5. /kilit Komutu 
@tree.command(name="kilit", description="Kullanılan metin kanalını belirli bir süre kilitler (dakika cinsinden).")
@app_commands.checks.has_permissions(manage_channels=True)
async def kilit_komutu(interaction: discord.Interaction, sure_dakika: app_commands.Range[int, 1, None], sebep: str = "Yönetim Kararı"):
    kanal = interaction.channel
    sure_saniye = sure_dakika * 60 
    
    everyone_role = interaction.guild.default_role
    yeni_perms = kanal.overwrites_for(everyone_role)
    yeni_perms.send_messages = False
    
    try:
        await kanal.set_permissions(everyone_role, overwrite=yeni_perms, reason=f"Kilitlendi: {sebep}")
        
        await interaction.response.send_message(
            f"✅ **{kanal.mention}** kanalı **{sure_dakika} dakikalığına** kilitlendi. Sebep: **{sebep}**", 
            ephemeral=True
        )
        await interaction.channel.send(f"🔒 **KANAL KİLİTLENDİ!** Kanal **{sure_dakika} dakika** boyunca yetkililer hariç kullanıma kapalıdır. Sebep: **{sebep}**")
        
        await asyncio.sleep(sure_saniye)
        
        yeni_perms.send_messages = None
        await kanal.set_permissions(everyone_role, overwrite=yeni_perms, reason="Süre Doldu: Kilit açıldı")
        await kanal.send(f"🔓 **{kanal.mention}** kilidi açıldı! Artık mesaj gönderebilirsiniz.")

    except discord.Forbidden:
        await interaction.response.send_message("Kanalları yönetme iznim yok!", ephemeral=True)


# 6. /sil Komutu 
@tree.command(name="sil", description="Belirtilen miktarda mesajı siler (Maks. 100).")
@app_commands.checks.has_permissions(manage_messages=True)
async def sil_komutu(interaction: discord.Interaction, miktar: app_commands.Range[int, 1, 100]):
    await interaction.response.defer(ephemeral=True) 
    await interaction.channel.purge(limit=miktar) 
    await interaction.followup.send(f'✅ **{miktar}** adet mesaj başarıyla silindi.', ephemeral=True)

# 7. /afk Komutu (Halka açık olması için ephemeral=False bırakılmıştır)
@tree.command(name="afk", description="Botunuzu AFK (Klavye Başında Değil) durumuna geçirir.")
async def afk_komutu(interaction: discord.Interaction, sebep: str = "Sebep belirtilmemiş"):
    user_id = interaction.user.id
    AFK_DURUMU[user_id] = sebep

    yeni_nick = f"[AFK] {interaction.user.display_name}"
    try:
        if len(yeni_nick) > 32:
            yeni_nick = f"[AFK] {interaction.user.display_name[:26]}"
            
        await interaction.user.edit(nick=yeni_nick)
        await interaction.response.send_message(f"💤 **{interaction.user.mention}** AFK durumuna geçti. Sebep: **{sebep}**", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message(f"💤 AFK durumuna geçtin, ancak botun rolü nickini değiştirmeye yetmiyor. Sebep: **{sebep}**", ephemeral=True)

# 8. /çek Komutu 
@tree.command(name="çek", description="Girdiğin üyeyi senin bulunduğun sesli kanala taşırsın.")
@app_commands.checks.has_permissions(move_members=True)
async def cek_komutu(interaction: discord.Interaction, uye: discord.Member):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("Önce bir sesli kanala katılmalısın!", ephemeral=True)
        return
    if not uye.voice or not uye.voice.channel:
        await interaction.response.send_message(f"**{uye.display_name}** şu anda bir sesli kanalda değil.", ephemeral=True)
        return
    
    hedef_kanal = interaction.user.voice.channel
    
    try:
        await uye.move_to(hedef_kanal)
        await interaction.response.send_message(f"✅ **{uye.display_name}** başarılı bir şekilde **{hedef_kanal.name}** kanalına çekildi.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Üyeyi taşımak için yeterli yetkim yok veya üye yetkili.", ephemeral=True)

# 9. /taşı Komutu 
@tree.command(name="taşı", description="Girdiğin üyeyi istediğin sesli kanala taşırsın.")
@app_commands.checks.has_permissions(move_members=True)
async def tasi_komutu(interaction: discord.Interaction, uye: discord.Member, kanal: discord.VoiceChannel):
    if not uye.voice or not uye.voice.channel:
        await interaction.response.send_message(f"**{uye.display_name}** şu anda bir sesli kanalda değil.", ephemeral=True)
        return
    
    try:
        await uye.move_to(kanal)
        await interaction.response.send_message(f"✅ **{uye.display_name}** başarılı bir şekilde **{kanal.name}** kanalına taşındı.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Üyeyi taşımak için yeterli yetkim yok veya üye yetkili.", ephemeral=True)

# 10. /hatırlatıcı Komutu 
@tree.command(name="hatırlatıcı", description="Belirtilen süre sonunda seni etiketleyerek bir şeyi hatırlatır (dakika cinsinden).")
async def hatirlatici_komutu(interaction: discord.Interaction, sure_dakika: app_commands.Range[int, 1, None], mesaj: str):
    sure_saniye = sure_dakika * 60 
    
    await interaction.response.send_message(f"✅ Hatırlatıcın ayarlandı. **{sure_dakika} dakika** sonra sana hatırlatacağım.", ephemeral=True)
    
    await asyncio.sleep(sure_saniye)
    
    await interaction.followup.send(f"🔔 **HATIRLATICI:** {interaction.user.mention} \n> Hatırlatılacak mesaj: **{mesaj}**")


# 11. /koruma Komutu 
@tree.command(name="koruma", description="Botun aktif koruma sistemlerinin durumunu gösterir.")
async def koruma_komutu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ Bot Koruma Sistemleri Durumu",
        description="Botunuzun aktif güvenlik ve otomasyon özelliklerinin özeti:",
        color=discord.Color.dark_red()
    )
    
    embed.add_field(
        name="💬 Sohbet Korumaları", 
        value=(
            f"**Anti-Spam (Flood)**: {'✅ Aktif' if SPAM_LIMIT else '❌ Kapalı'} ({SPAM_LIMIT} mesaj / {SPAM_ZAMAN} sn)\n"
            f"**Link Engel**: {'✅ Aktif' if LINK_ENGEL_AKTIF else '❌ Kapalı'}"
        ), 
        inline=False
    )
    
    embed.add_field(
        name="👥 Üye & Yönetim Otomasyonları", 
        value=(
            f"**AFK Sistemi**: ✅ Aktif\n"
            f"**Otomatik Rol ({OTOMATIK_ROL_ADI})**: {'✅ Aktif' if OTOMATIK_ROL_ADI else '❌ Kapalı'}"
        ), 
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 12. /avatar Komutu 
@tree.command(name="avatar", description="Bir kullanıcının avatarını tam boy gösterir.")
async def avatar_komutu(interaction: discord.Interaction, uye: discord.Member):
    avatar_url = uye.avatar.url if uye.avatar else uye.default_avatar.url
    embed = discord.Embed(
        title=f"🖼️ {uye.display_name} Avatarı",
        color=discord.Color.dark_teal()
    )
    embed.set_image(url=avatar_url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 13. /kullanici Komutu (YENİLENDİ: Detaylı ve Görseldeki Gibi Analiz)
@tree.command(name="kullanici", description="Bir kullanıcının detaylı sunucu ve Discord bilgilerini gösterir.")
async def kullanici_komutu(interaction: discord.Interaction, uye: discord.Member = None):
    # Kullanıcı belirtilmezse komutu kullananı kullan
    uye = uye or interaction.user
    
    # 1. Ses Süresi Verisi
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_voice_seconds FROM voice_logs WHERE user_id = ?", (uye.id,))
    db_result = cursor.fetchone()
    conn.close()
    
    total_voice_time = db_result[0] if db_result else 0
    formatted_voice_time = format_seconds(total_voice_time)
    
    # 2. Embed Rengi ve Rol Bilgileri
    # En yüksek rolün rengini kullan. Eğer renk yoksa (default), yeşil kullan.
    color = uye.color if uye.color != discord.Color.default() else discord.Color.green()
    
    # Rolleri hiyerarşik olarak sıralayıp listeleyelim (@everyone hariç)
    roller = sorted(
        [r for r in uye.roles if r.name != "@everyone"], 
        key=lambda r: r.position, 
        reverse=True
    )
    # Rol isimlerini al ve 1024 karakter sınırına kadar birleştir
    roller_isimleri = ", ".join([r.mention for r in roller])
    roller_str = roller_isimleri[:1020] + "..." if len(roller_isimleri) > 1020 else roller_isimleri
    
    # 3. AFK ve Ses Durumu
    afk_sebep = AFK_DURUMU.get(uye.id)
    afk_durumu = f"✅ AFK. Sebep: **{afk_sebep}**" if afk_sebep else "❌ AFK Değil"
    
    ses_kanali = uye.voice.channel.mention if uye.voice and uye.voice.channel else "Yok"
    
    
    embed = discord.Embed(
        title=f"👤 {uye.display_name} Kullanıcı Profili",
        description=f"**Kullanıcı Adı:** {uye.mention}\n"
                    f"**ID:** `{uye.id}`",
        color=color
    )
    
    # Alan 1: Durum Bilgileri
    embed.add_field(
        name="Durum ve Aktivite", 
        value=(
            f"**Discord Durumu:** {durum_cevir(uye.status)}\n"
            f"**AFK Durumu:** {afk_durumu}"
        ), 
        inline=True
    )
    
    # Alan 2: Ses Bilgisi
    embed.add_field(
        name="Ses Kanalı", 
        value=(
            f"**Anlık Kanal:** {ses_kanali}\n"
            f"**Toplam Ses Süresi:** {formatted_voice_time}"
        ), 
        inline=True
    )

    # Alan 3: Kayıt Bilgileri
    embed.add_field(
        name="Kayıt Tarihleri",
        value=(
            f"**Sunucuya Katılım:** {discord.utils.format_dt(uye.joined_at, 'R')}\n"
            f"**Discord'a Katılım:** {discord.utils.format_dt(uye.created_at, 'R')}"
        ),
        inline=False
    )
    
    # Alan 4: Roller
    embed.add_field(
        name=f"Roller ({len(roller)})", 
        value=roller_str if roller_str else "Yok", 
        inline=False
    )
    
    embed.set_thumbnail(url=uye.avatar.url if uye.avatar else uye.default_avatar.url)
    embed.set_footer(text=f"Analizi İsteyen: {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# 14. /roller Komutu (Sade ve Hiyerarşik)
@tree.command(name="roller", description="Sunucudaki tüm rolleri hiyerarşik olarak listeler ve üye sayısını gösterir.")
async def roller_komutu(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True) 
    
    roles = sorted(
        [r for r in interaction.guild.roles if r.name != "@everyone"], 
        key=lambda r: r.position, 
        reverse=True
    )
    
    if not roles:
        await interaction.followup.send("❌ Sunucuda `@everyone` dışında özel bir rol bulunmamaktadır.", ephemeral=True)
        return

    roller_listesi = []
    
    for i, role in enumerate(roles):
        member_count = len(role.members) 
        
        rol_satiri = f"**{i+1}.** {role.mention} **({member_count} Üye)**"
        
        if role.managed and role.hoist:
             rol_satiri += " `[Bot]`"
        
        roller_listesi.append(rol_satiri)
        
    roller_str = "\n".join(roller_listesi)
    
    if len(roller_str) > 4000:
        roller_str = roller_str[:4000] + "\n... (Liste çok uzun olduğu için kesildi.)"

    embed = discord.Embed(
        title=f"👑 {interaction.guild.name} Rol Listesi",
        description=roller_str, 
        color=discord.Color.dark_blue()
    )
    
    embed.set_footer(text=f"Toplam Rol Sayısı: {len(roles)} | Hiyerarşik Sıralama")
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# 15. /sunucu Komutu 
@tree.command(name="sunucu", description="Sunucu bilgilerini gösterir.")
async def sunucu_komutu(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"🌍 {guild.name} Sunucu Bilgileri",
        color=discord.Color.purple()
    )
    embed.add_field(name="Kurucu", value=guild.owner.mention, inline=True)
    embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=True)
    embed.add_field(name="Rol Sayısı", value=len(guild.roles), inline=True)
    embed.add_field(name="Sunucu ID", value=f"`{guild.id}`", inline=False)
    embed.add_field(name="Oluşturulma", value=discord.utils.format_dt(guild.created_at, "R"), inline=False)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- BOTU ÇALIŞTIRMA ---

client.run(os.getenv("TOKEN"))
