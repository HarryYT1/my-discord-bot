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
    # ➤ YENİ: Mesaj sayısını takip etmek için tablo
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
TOKEN = '' # Lütfen kendi tokeninizi buraya girin veya os.getenv("TOKEN") kullanın.

OTOMATIK_ROL_ADI = "Üye" 
AFK_DURUMU = {} 
YASAKLI_LINKLER = ['discord.gg', 'http://', 'https://', '.com', '.net', '.org'] 

VOICE_JOIN_TIMES = {} 
CEKILIS_EMOJI = "🎉"

# --- CLIENT VE TREE TANIMLAMA ---
# ➤ KRİTİK: İhtiyaç duyulan tüm Intent'ler (Durum ve Üye Bilgileri için)
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

# --- MERKEZİ LOG FONKSİYONU ---
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

    # A) AFK Kapanması (Yazı yazdığında)
    await check_afk_status(message.author, message.channel)

    # B) AFK Etiketleme Kontrolü
    for user_id_afk, sebep in AFK_DURUMU.items():
        if client.get_user(user_id_afk) in message.mentions:
            afk_kullanici = client.get_user(user_id_afk)
            await message.channel.send(f"💤 **{afk_kullanici.mention}** şu anda AFK. Sebep: **{sebep}**", delete_after=10)

    # C) Link Engel Kontrolü
    if LINK_ENGEL_AKTIF:
        mesaj_icerigi = message.content.lower()
        if any(link in mesaj_icerigi for link in YASAKLI_LINKLER) and not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"🚫 **{message.author.mention}**, bu kanalda link paylaşımına izin verilmiyor!", delete_after=5)
            except discord.Forbidden:
                pass

    # D) Anti-Spam Kontrolü
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

    # ➤ YENİ: Mesaj Sayısı Güncelleme
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_messages (user_id, count) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET count = count + 1",
        (user_id,)
    )
    conn.commit()
    conn.close()
        

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
    await interaction.response.send_message(embed=embed, ephemeral=False)


# /çekiliş (Aynı kaldı)
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


# /logayarla (Aynı kaldı)
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

# /yasakla (Aynı kaldı)
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
        await interaction.response.send_message(f'🚫 **{uye.display_name}** sunucudan yasaklandı. Sebep: **{sebep}**', ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("Botun bu üyeyi yasaklamak için yeterli izni yok.", ephemeral=True)

# /yasakkaldir (Aynı kaldı)
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
        
        await interaction.response.send_message(f'✅ **{member_to_unban.name}** kullanıcısının yasağı başarıyla kaldırıldı. Sebep: **{sebep}**', ephemeral=False)
        
    except discord.Forbidden:
        await interaction.response.send_message("Botun yasağı kaldırmak için yeterli izni yok.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Beklenmedik bir hata oluştu: `{e}`", ephemeral=True)


# /kilit (Aynı kaldı)
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
            f"🔒 **{kanal.mention}** kanalı **{sure_dakika} dakikalığına** kilitlendi. Sebep: **{sebep}**", 
            ephemeral=False
        )
        
        await asyncio.sleep(sure_saniye)
        
        yeni_perms.send_messages = None
        await kanal.set_permissions(everyone_role, overwrite=yeni_perms, reason="Süre Doldu: Kilit açıldı")
        await kanal.send(f"🔓 **{kanal.mention}** kilidi açıldı! Artık mesaj gönderebilirsiniz.")

    except discord.Forbidden:
        await interaction.response.send_message("Kanalları yönetme iznim yok!", ephemeral=True)


# /sil (Aynı kaldı)
@tree.command(name="sil", description="Belirtilen miktarda mesajı siler (Maks. 100).")
@app_commands.checks.has_permissions(manage_messages=True)
async def sil_komutu(interaction: discord.Interaction, miktar: app_commands.Range[int, 1, 100]):
    await interaction.response.defer(ephemeral=True) 
    await interaction.channel.purge(limit=miktar) 
    await interaction.followup.send(f'✅ **{miktar}** adet mesaj başarıyla silindi.', ephemeral=True)

# /afk (Aynı kaldı)
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

# /çek (Aynı kaldı)
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
        await interaction.response.send_message(f"➡️ **{uye.display_name}** başarılı bir şekilde **{hedef_kanal.name}** kanalına çekildi.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("Üyeyi taşımak için yeterli yetkim yok veya üye yetkili.", ephemeral=True)

# /taşı (Aynı kaldı)
@tree.command(name="taşı", description="Girdiğin üyeyi istediğin sesli kanala taşırsın.")
@app_commands.checks.has_permissions(move_members=True)
async def tasi_komutu(interaction: discord.Interaction, uye: discord.Member, kanal: discord.VoiceChannel):
    if not uye.voice or not uye.voice.channel:
        await interaction.response.send_message(f"**{uye.display_name}** şu anda bir sesli kanalda değil.", ephemeral=True)
        return
    
    try:
        await uye.move_to(kanal)
        await interaction.response.send_message(f"➡️ **{uye.display_name}** başarılı bir şekilde **{kanal.name}** kanalına taşındı.", ephemeral=False)
    except discord.Forbidden:
        await interaction.response.send_message("Üyeyi taşımak için yeterli yetkim yok veya üye yetkili.", ephemeral=True)

# /hatırlatıcı (Aynı kaldı)
@tree.command(name="hatırlatıcı", description="Belirtilen süre sonunda seni etiketleyerek bir şeyi hatırlatır (dakika cinsinden).")
async def hatirlatici_komutu(interaction: discord.Interaction, sure_dakika: app_commands.Range[int, 1, None], mesaj: str):
    sure_saniye = sure_dakika * 60 
    
    await interaction.response.send_message(f"⏰ Tamam **{interaction.user.mention}**, **{sure_dakika} dakika** sonra sana **'{mesaj}'** mesajını hatırlatacağım.", ephemeral=False)
    
    await asyncio.sleep(sure_saniye)
    
    await interaction.followup.send(f"🔔 **HATIRLATICI:** {interaction.user.mention} \n> Hatırlatılacak mesaj: **{mesaj}**")


# /koruma (Aynı kaldı)
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
    
    await interaction.response.send_message(embed=embed)


# /avatar (Aynı kaldı)
@tree.command(name="avatar", description="Bir kullanıcının avatarını tam boy gösterir.")
async def avatar_komutu(interaction: discord.Interaction, uye: discord.Member = None):
    uye = uye or interaction.user
    avatar_url = uye.avatar.url if uye.avatar else uye.default_avatar.url
    embed = discord.Embed(
        title=f"🖼️ {uye.display_name} Avatarı",
        color=discord.Color.dark_teal()
    )
    embed.set_image(url=avatar_url)
    await interaction.response.send_message(embed=embed)


# 14. /kullanici Komutu (➤ TAMAMEN YENİLENDİ ve Detaylandırıldı)
@tree.command(name="kullanici", description="Bir kullanıcının detaylı sunucu ve Discord bilgilerini gösterir.")
async def kullanici_komutu(interaction: discord.Interaction, uye: discord.Member = None):
    uye = uye or interaction.user
    
    # 1. Ses Süresi Verisi
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_voice_seconds FROM voice_logs WHERE user_id = ?", (uye.id,))
    voice_result = cursor.fetchone()
    total_voice_time = voice_result[0] if voice_result else 0
    formatted_voice_time = format_seconds(total_voice_time)

    # 2. Mesaj Sayısı Verisi
    cursor.execute("SELECT count FROM user_messages WHERE user_id = ?", (uye.id,))
    message_result = cursor.fetchone()
    message_count = message_result[0] if message_result else 0
    conn.close()
    
    # 3. Embed Rengi ve Rol Bilgileri
    color = uye.color if uye.color != discord.Color.default() else discord.Color.dark_teal()
    
    # 4. Rozetleri Al ve Çevir
    rozetler = []
    
    flag_cevirileri = {
        "partner": "🤝 Partner", 
        "hypesquad_events": "🌐 HypeSquad Etkinlikleri",
        "bug_hunter_level_1": "🐛 Bug Hunter Seviye 1",
        "hypesquad_bravery": "🛡️ Cesaret HypeSquad",
        "hypesquad_brilliance": "💡 Brilliance HypeSquad",
        "hypesquad_balance": "⚖️ Denge HypeSquad",
        "early_supporter": "🎉 Erken Destekçi",
        "verified_developer": "💻 Onaylı Bot Geliştiricisi",
        "active_developer": "🛠️ Aktif Geliştirici"
    }
    
    flags = [str(flag).split('.')[-1] for flag in uye.public_flags.all()]
    for flag in flags:
        if flag in flag_cevirileri:
            rozetler.append(flag_cevirileri[flag])
    
    if uye.premium_since:
        rozetler.append("⭐ Sunucu Destekçisi (Booster)")
        
    rozet_str = ", ".join(rozetler) if rozetler else "Yok"
    
    
    # 5. Aktivite Bilgisi
    aktivite_str = "Yok"
    if uye.activity:
        if uye.activity.type == discord.ActivityType.playing:
            aktivite_str = f"🎮 **{uye.activity.name}**"
        elif uye.activity.type == discord.ActivityType.streaming:
            aktivite_str = f"🔴 **{uye.activity.name}**"
        elif uye.activity.type == discord.ActivityType.listening:
            aktivite_str = f"🎶 **{uye.activity.name}**"
        elif uye.activity.type == discord.ActivityType.watching:
            aktivite_str = f"👀 **{uye.activity.name}**"
        else:
            # Diğer aktivite türleri (Özel Durum vs.)
            aktivite_str = f"🔔 **{getattr(uye.activity, 'name', 'Özel Durum')}**"
    
    # 6. AFK Bilgisi
    afk_sebep = AFK_DURUMU.get(uye.id)
    afk_durumu = f"✅ AFK. Sebep: **{afk_sebep}**" if afk_sebep else "❌ AFK Değil"
    
    # 7. Ana Embed Oluşturma
    embed = discord.Embed(
        title=f"👤 {uye.display_name} Detaylı Bilgileri",
        description=f"**Kullanıcı:** {uye.mention}\n"
                    f"**ID:** `{uye.id}`",
        color=color
    )
    
    embed.set_thumbnail(url=uye.avatar.url if uye.avatar else uye.default_avatar.url)
    
    # --- GRUP 1: DURUM VE AKTİVİTE ---
    embed.add_field(
        name="🌐 Durum ve Aktiflik", 
        value=(
            f"**Discord Durumu:** {durum_cevir(uye.status)}\n"
            f"**AFK Durumu:** {afk_durumu}\n"
            f"**Aktivite:** {aktivite_str}\n"
            f"**Rozetler:** {rozet_str}"
        ), 
        inline=False
    )
    
    # --- GRUP 2: KAYIT VE ZAMAN ---
    embed.add_field(
        name="📅 Zaman Bilgileri",
        value=(
            f"**Discord'a Katılım:** {discord.utils.format_dt(uye.created_at, 'R')}\n"
            f"**Sunucuya Katılım:** {discord.utils.format_dt(uye.joined_at, 'R')}"
        ),
        inline=True
    )

    # --- GRUP 3: SES VE İSTATİSTİK ---
    embed.add_field(
        name="🔊 Ses & İstatistik", 
        value=(
            f"**Ses Kanalı:** {uye.voice.channel.mention if uye.voice and uye.voice.channel else 'Yok'}\n"
            f"**Toplam Ses Süresi:** {formatted_voice_time}\n"
            f"**Toplam Mesaj Sayısı:** `{message_count}`"
        ), 
        inline=True
    )

    # --- GRUP 4: ROLLER ---
    roles_display = sorted(
        [r for r in uye.roles if r.name != "@everyone"], 
        key=lambda r: r.position, 
        reverse=True
    )
    
    # Rolleri etiketleyerek birleştir ve 1024 karakter sınırına dikkat et.
    roles_mention = [r.mention for r in roles_display]
    roller_str = " ".join(roles_mention)
    
    if len(roller_str) > 1020:
        roller_str = roller_str[:1020] + "..." 
    elif not roles_display:
        roller_str = "*Sunucuda özel rolü yok.*"

    embed.add_field(
        name=f"👑 Roller ({len(roles_display)})", 
        value=roller_str, 
        inline=False
    )
    
    embed.set_footer(text=f"Analizi İsteyen: {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)


# 15. /roller Komutu (➤ GÜNCELLENDİ: Üye sayısı ve Hiyerarşik Sıralama)
@tree.command(name="roller", description="Sunucudaki tüm rolleri hiyerarşik olarak listeler ve üye sayısını gösterir.")
async def roller_komutu(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False) 
    
    roles = sorted(
        [r for r in interaction.guild.roles if r.name != "@everyone"], 
        key=lambda r: r.position, 
        reverse=True
    )
    
    if not roles:
        await interaction.followup.send("❌ Sunucuda `@everyone` dışında özel bir rol bulunmamaktadır.")
        return

    roller_listesi = []
    
    for role in roles:
        member_count = len(role.members) 
        
        # Rol adını renklendirmek için mention kullanıyoruz.
        rol_satiri = f"{role.mention} **({member_count} Üye)**"
        
        # Eğer rol ayrı gösteriliyorsa (hoist) taç ikonu ekle
        if role.hoist: 
             rol_satiri += " 👑"
        
        roller_listesi.append(rol_satiri)
        
    roller_str = "\n".join(roller_listesi)
    
    if len(roller_str) > 4000:
        roller_str = roller_str[:4000] + "\n... (Liste çok uzun olduğu için kesildi.)"

    embed = discord.Embed(
        title=f"👑 {interaction.guild.name} Rol Listesi",
        description=f"**@ Roller [{len(roles)}/{interaction.guild.member_count}]**\n\n{roller_str}", 
        color=discord.Color.dark_blue()
    )
    
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
    embed.set_footer(text=f"Listelenen Toplam Rol Sayısı: {len(roles)} | Hiyerarşik Sıralama")
    
    await interaction.followup.send(embed=embed)


# 16. /sunucu Komutu (Aynı kaldı)
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
        
    await interaction.response.send_message(embed=embed)

# --- BOTU ÇALIŞTIRMA ---

client.run(os.getenv("TOKEN")

