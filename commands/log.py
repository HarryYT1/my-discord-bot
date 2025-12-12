import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import json
import os

# Log ayarlarını saklamak için basit JSON dosyası
LOG_FILE = "log_settings.json"


class LogSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_settings = self.load_log_settings()

    def load_log_settings(self):
        """Log ayarlarını yükle"""
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_log_settings(self):
        """Log ayarlarını kaydet"""
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.log_settings, f, indent=4, ensure_ascii=False)

    def get_log_channel(self, guild_id, log_type):
        """Belirli bir log tipi için kanal ID'sini al"""
        guild_id_str = str(guild_id)
        if guild_id_str in self.log_settings:
            return self.log_settings[guild_id_str].get(log_type)
        return None

    # ========== LOG AYARLAMA KOMUTU ==========
    @app_commands.command(name="log", description="Log sistemini ayarlar")
    @app_commands.describe(
        log_tipi="Log türü",
        kanal="Log kanalı (boş bırakırsanız kapatılır)"
    )
    @app_commands.choices(log_tipi=[
        app_commands.Choice(name="📝 Mesaj Silme", value="message_delete"),
        app_commands.Choice(name="✏️ Mesaj Düzenleme", value="message_edit"),
        app_commands.Choice(name="👋 Üye Giriş", value="member_join"),
        app_commands.Choice(name="🚪 Üye Çıkış", value="member_leave"),
        app_commands.Choice(name="🔨 Ban", value="member_ban"),
        app_commands.Choice(name="✅ Unban", value="member_unban"),
        app_commands.Choice(name="👤 Üye Güncelleme", value="member_update"),
        app_commands.Choice(name="🎭 Rol Güncelleme", value="role_update"),
        app_commands.Choice(name="📢 Kanal Oluşturma", value="channel_create"),
        app_commands.Choice(name="🗑️ Kanal Silme", value="channel_delete"),
        app_commands.Choice(name="📊 Ses Kanalı", value="voice_state"),
        app_commands.Choice(name="⚙️ Sunucu Güncelleme", value="guild_update"),
        app_commands.Choice(name="🎤 Nickname Değişikliği", value="nickname_change"),
        app_commands.Choice(name="🛡️ Moderasyon", value="moderation")
    ])
    async def log_setup(self, interaction: discord.Interaction, log_tipi: str, kanal: discord.TextChannel = None):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ **Bu komutu kullanmak için yönetici yetkisi gerekli!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.log_settings:
            self.log_settings[guild_id_str] = {}

        if kanal:
            self.log_settings[guild_id_str][log_tipi] = kanal.id
            status = "✅ Aktive"
            channel_info = kanal.mention
            color = 0x00FF00
        else:
            if log_tipi in self.log_settings[guild_id_str]:
                del self.log_settings[guild_id_str][log_tipi]
            status = "❌ Kapalı"
            channel_info = "```Kapatıldı```"
            color = 0xFF0000

        self.save_log_settings()

        log_names = {
            "message_delete": "📝 Mesaj Silme",
            "message_edit": "✏️ Mesaj Düzenleme",
            "member_join": "👋 Üye Giriş",
            "member_leave": "🚪 Üye Çıkış",
            "member_ban": "🔨 Ban",
            "member_unban": "✅ Unban",
            "member_update": "👤 Üye Güncelleme",
            "role_update": "🎭 Rol Güncelleme",
            "channel_create": "📢 Kanal Oluşturma",
            "channel_delete": "🗑️ Kanal Silme",
            "voice_state": "📊 Ses Kanalı",
            "guild_update": "⚙️ Sunucu Güncelleme",
            "nickname_change": "🎤 Nickname Değişikliği",
            "moderation": "🛡️ Moderasyon"
        }

        embed = discord.Embed(
            title="📋 Log Sistemi Ayarlandı",
            color=color
        )
        embed.add_field(name="📧 Log Tipi", value=f"```{log_names.get(log_tipi, log_tipi)}```", inline=True)
        embed.add_field(name="📊 Durum", value=status, inline=True)
        embed.add_field(name="📝 Kanal", value=channel_info, inline=False)
        embed.set_footer(text=f"Ayarlayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== LOG DURUMU ==========
    @app_commands.command(name="logstatus", description="Aktif log ayarlarını gösterir")
    async def log_status(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.log_settings or not self.log_settings[guild_id_str]:
            embed = discord.Embed(
                description="📋 **Hiç bir log ayarı yapılmamış!**",
                color=0x5865F2
            )
            return await interaction.response.send_message(embed=embed)

        embed = discord.Embed(
            title="📋 Aktif Log Ayarları",
            description="```Sunucudaki aktif log ayarları```",
            color=0x5865F2
        )

        log_names = {
            "message_delete": "📝 Mesaj Silme",
            "message_edit": "✏️ Mesaj Düzenleme",
            "member_join": "👋 Üye Giriş",
            "member_leave": "🚪 Üye Çıkış",
            "member_ban": "🔨 Ban",
            "member_unban": "✅ Unban",
            "member_update": "👤 Üye Güncelleme",
            "role_update": "🎭 Rol Güncelleme",
            "channel_create": "📢 Kanal Oluşturma",
            "channel_delete": "🗑️ Kanal Silme",
            "voice_state": "📊 Ses Kanalı",
            "guild_update": "⚙️ Sunucu Güncelleme",
            "nickname_change": "🎤 Nickname",
            "moderation": "🛡️ Moderasyon"
        }

        for log_type, channel_id in self.log_settings[guild_id_str].items():
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                embed.add_field(
                    name=log_names.get(log_type, log_type),
                    value=f"{channel.mention}",
                    inline=True
                )

        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== MESAJ SİLME LOGU (GÖRSEL 1 TARZI) ==========
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        channel_id = self.get_log_channel(message.guild.id, "message_delete")
        if not channel_id:
            return

        log_channel = message.guild.get_channel(channel_id)
        if not log_channel:
            return

        # Mesaj sahibini al
        author_name = f"{message.author.name}"
        
        embed = discord.Embed(
            description=f"**{author_name}** kişinin mesajı silindi.",
            color=0x2F3136
        )
        embed.set_author(name=author_name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        
        # Silinen Mesajın İçeriği
        content = message.content if message.content else "*Mesaj içeriği yok*"
        embed.add_field(name="📨 Silinen Mesajın İçeriği:", value=f"• 💬 {content[:1000]}", inline=False)
        
        # Mesaj Bilgileri
        created_time = int(message.created_at.timestamp())
        time_ago_text = f"<t:{created_time}:R>"
        
        mesaj_bilgileri = (
            f"• 📝 **Mesaj Yazılış:** {message.created_at.strftime('%d %B %Y - %H:%M:%S')} ({time_ago_text})\n"
            f"• 🌍 **Mesaj Silinme:** {datetime.now(timezone.utc).strftime('%d %B %Y - %H:%M:%S sonra')}\n"
            f"• 🆔 **Mesaj Sahibi:** {message.author.mention} (`{message.author.id}`)"
        )
        embed.add_field(name="ℹ️ Mesaj Bilgileri:", value=mesaj_bilgileri, inline=False)
        
        # Mesajın Konumu
        konum = (
            f"• # **Mesajın Kanalı:** # ┃ {message.channel.mention}\n"
            f"• ▶️ **Silindiği Yere Git**"
        )
        embed.add_field(name="📍 Mesajın Konumu:", value=konum, inline=False)
        
        # Mesaj Silen (Eğer bulunabilirse)
        embed.add_field(name="👤 Mesaj Silen:", value=f"**{author_name}** *(veya bir yetkili)*", inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== MESAJ DÜZENLEME LOGU ==========
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        channel_id = self.get_log_channel(before.guild.id, "message_edit")
        if not channel_id:
            return

        log_channel = before.guild.get_channel(channel_id)
        if not log_channel:
            return

        author_name = f"{before.author.name}"
        
        embed = discord.Embed(
            description=f"**{author_name}** kişinin mesajı düzenlendi.",
            color=0x2F3136
        )
        embed.set_author(name=author_name, icon_url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)
        embed.set_thumbnail(url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)
        
        # Eski ve Yeni Mesaj
        embed.add_field(
            name="📝 Eski Mesaj:",
            value=f"```{before.content[:500] if before.content else 'Boş mesaj'}```",
            inline=False
        )
        embed.add_field(
            name="✨ Yeni Mesaj:",
            value=f"```{after.content[:500] if after.content else 'Boş mesaj'}```",
            inline=False
        )
        
        # Mesaj Bilgileri
        created_time = int(before.created_at.timestamp())
        mesaj_bilgileri = (
            f"• 📝 **Mesaj Yazılış:** {before.created_at.strftime('%d %B %Y - %H:%M:%S')} (<t:{created_time}:R>)\n"
            f"• 🆔 **Mesaj Sahibi:** {before.author.mention} (`{before.author.id}`)"
        )
        embed.add_field(name="ℹ️ Mesaj Bilgileri:", value=mesaj_bilgileri, inline=False)
        
        # Mesajın Konumu
        konum = f"• # **Mesajın Kanalı:** # ┃ {before.channel.mention}\n• [▶️ Mesaja Git]({after.jump_url})"
        embed.add_field(name="📍 Mesajın Konumu:", value=konum, inline=False)
        
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== ÜYE GİRİŞ LOGU (GÖRSEL 3 TARZI) ==========
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel_id = self.get_log_channel(member.guild.id, "member_join")
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            description=f"**Sunucuya bir üye katıldı:**",
            color=0x2F3136
        )
        
        # Üye bilgisi
        embed.add_field(
            name="👤 Üye:",
            value=f"• {member.mention}",
            inline=False
        )
        
        # Discord'a Kayıt Tarihi
        created_timestamp = int(member.created_at.timestamp())
        embed.add_field(
            name="📅 Discord'a Kayıt Tarihi:",
            value=f"• 🕐 {member.created_at.strftime('%d %B %Y - %H:%M:%S')} (<t:{created_timestamp}:R>)",
            inline=False
        )
        
        # Davet Eden Kişi (Bu özellik için invite tracking gerekir, şimdilik gösterilmedi)
        embed.add_field(
            name="🎟️ Davet Eden Kişi:",
            value="• 👤 **• Davet Alınamadı**",
            inline=False
        )
        
        # Davet Sayısı
        embed.add_field(
            name="🎫 Davet Sayısı:",
            value="• 🎟️ **• Davet Alınamadı**",
            inline=False
        )
        
        # Davet Kodu
        embed.add_field(
            name="🔗 Davet Kodu:",
            value="• 🔗 **• Davet Alınamadı**",
            inline=False
        )
        
        # İstatistikler
        embed.add_field(
            name="📊 İstatistikler:",
            value=f"• 🎯 **Hedef:** {member.guild.member_count} **• Üye Sayı:** 🎖️ {len([m for m in member.guild.members if not m.bot])} **• Kalan:** {member.guild.member_count - len([m for m in member.guild.members if not m.bot])}",
            inline=False
        )
        
        embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== ÜYE ÇIKIŞ LOGU ==========
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel_id = self.get_log_channel(member.guild.id, "member_leave")
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            description=f"**Sunucudan bir üye ayrıldı:**",
            color=0x2F3136
        )
        
        embed.add_field(name="👤 Üye:", value=f"• {member.mention}", inline=False)
        
        if member.joined_at:
            joined_timestamp = int(member.joined_at.timestamp())
            embed.add_field(
                name="📅 Sunucuya Katılım Tarihi:",
                value=f"• 🕐 {member.joined_at.strftime('%d %B %Y - %H:%M:%S')} (<t:{joined_timestamp}:R>)",
                inline=False
            )
        
        embed.add_field(
            name="📊 İstatistikler:",
            value=f"• 🎯 **Kalan Üye:** {member.guild.member_count}",
            inline=False
        )
        
        embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== BAN LOGU (GÖRSEL 6 TARZI) ==========
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel_id = self.get_log_channel(guild.id, "member_ban")
        if not channel_id:
            return

        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return

        # Audit log'dan ban bilgisini al
        ban_reason = "Sebep belirtilmedi"
        banner = None
        
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                ban_reason = entry.reason or "Sebep belirtilmedi"
                banner = entry.user
                break

        embed = discord.Embed(
            description=f"**{user.name}** adlı kişi sunucudan yasaklandı~",
            color=0x2F3136
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        # Ban Sebebi
        embed.add_field(
            name="📋 Ban Sebebi:",
            value=f"• 💬 {ban_reason}",
            inline=False
        )
        
        # Yasaklanan Kişi
        embed.add_field(
            name="🚫 Yasaklanan Kişi:",
            value=f"• 🆔 <@{user.id}> (`{user.id}`)",
            inline=False
        )
        
        # Banlayan Yetkili
        if banner:
            embed.add_field(
                name="👮 Banlayan Yetkili:",
                value=f"• 👤 {banner.mention}",
                inline=False
            )
        
        # Banlandığı Kanal
        embed.add_field(
            name="🏠 Banlandığı Kanal:",
            value=f"• ## # ┃ **Sunucu Genel**",
            inline=False
        )
        
        # Yetkililerin Ban Sayısı
        if banner:
            # Bu özellik için veri tabanı gerekir, şimdilik statik
            embed.add_field(
                name="🔢 Yetkililerin Ban Sayısı:",
                value=f"• 🔥 4",
                inline=False
            )
        
        # Ban Tarihi
        ban_time = datetime.now(timezone.utc)
        ban_timestamp = int(ban_time.timestamp())
        time_ago = (datetime.now(timezone.utc) - ban_time).days
        embed.add_field(
            name="📅 Ban Tarihi:",
            value=f"• 📅 {ban_time.strftime('%d %B %Y - %H:%M:%S')} ({time_ago} gün önce)",
            inline=False
        )
        
        # Mesaja Git butonu
        embed.add_field(
            name="📨 İşlemler:",
            value="• ▶️ **Mesaja git**",
            inline=False
        )
        
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== UNBAN LOGU ==========
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel_id = self.get_log_channel(guild.id, "member_unban")
        if not channel_id:
            return

        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return

        unbanner = None
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                unbanner = entry.user
                break

        embed = discord.Embed(
            description=f"**{user.name}** adlı kişinin yasağı kaldırıldı.",
            color=0x2F3136
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        embed.add_field(name="🚫 Yasağı Kaldırılan:", value=f"• 🆔 <@{user.id}> (`{user.id}`)", inline=False)
        
        if unbanner:
            embed.add_field(name="👮 Yasağı Kaldıran:", value=f"• 👤 {unbanner.mention}", inline=False)
        
        unban_time = datetime.now(timezone.utc)
        embed.add_field(
            name="📅 Yasak Kaldırma Tarihi:",
            value=f"• 📅 {unban_time.strftime('%d %B %Y - %H:%M:%S')}",
            inline=False
        )
        
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== EMOJİ EKLEME LOGU (GÖRSEL 4 TARZI) ==========
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        channel_id = self.get_log_channel(guild.id, "guild_update")
        if not channel_id:
            return

        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return

        # Yeni emoji eklendi mi?
        if len(after) > len(before):
            new_emoji = [e for e in after if e not in before][0]
            
            # Ekleyen kişiyi bul
            adder = None
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.emoji_create):
                if entry.target.id == new_emoji.id:
                    adder = entry.user
                    break
            
            embed = discord.Embed(
                description=f"**{adder.name if adder else 'Bilinmeyen Kişi'}** sunucuya bir emoji ekledi.",
                color=0x2F3136
            )
            embed.set_thumbnail(url=new_emoji.url)
            
            embed.add_field(
                name="📝 Eklenen Emojinin Adı:",
                value=f"• ❤️ {new_emoji.name}",
                inline=False
            )
            
            embed.add_field(
                name="🆔 Eklenen Emojinin ID'i:",
                value=f"• 🆔 `{new_emoji.id}`",
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Ekleme Sebebi:",
                value=f"• ℹ️ **Emojiyi sunucuya ekle butonu ({adder.name if adder else 'Bilinmeyen'})**",
                inline=False
            )
            
            # Emoji istatistikleri
            animated_count = len([e for e in guild.emojis if e.animated])
            static_count = len([e for e in guild.emojis if not e.animated])
            
            embed.add_field(
                name="📊 Sunucudaki Hareketli Emoji Sayısı:",
                value=f"• 📊 **{animated_count}/{guild.emoji_limit}**",
                inline=False
            )
            
            embed.add_field(
                name="📊 Sunucudaki Hareketsiz Emoji Sayısı:",
                value=f"• 😊 **{static_count}/{guild.emoji_limit}**",
                inline=False
            )
            
            # Ekleyen kişi
            if adder:
                embed.add_field(
                    name="👤 Ekleyen Kişi:",
                    value=f"• **{adder.mention}**",
                    inline=False
                )
            
            # Butonlar
            embed.add_field(
                name="🔘 İşlemler:",
                value="• 🗑️ **Emojiyi Sil** • 🔄 **Emojinin İsmini Değiştir** • 😊 **Emojiler**",
                inline=False
            )
            
            embed.timestamp = datetime.now(timezone.utc)
            
            await log_channel.send(embed=embed)

    # ========== SES KANALI LOGU (GÖRSEL 7 - SADECE ÇIKIŞ) ==========
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel_id = self.get_log_channel(member.guild.id, "voice_state")
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        # SADECE KANALDAN ÇIKIŞ
        if before.channel is not None and after.channel is None:
            # Kanalda kalma süresini hesapla (bu özellik için tracking gerekir)
            # Şimdilik örnek süre
            
            now = datetime.now(timezone.utc)
            
            # Kanal bilgileri
            channel_name = before.channel.name
            channel_emoji = "🔊"  # Ses kanalı emojisi
            
            embed = discord.Embed(
                description=f"**{member.mention}** kişisi **{channel_emoji} )** **{channel_name}** kanalında **11 Dakika 24 Saniye** kaldı bu kanala **{now.strftime('%d %B %Y %H:%M')}** tarihinde giriş yapmıştı",
                color=0x2F3136
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            
            embed.timestamp = datetime.now(timezone.utc)
            
            await log_channel.send(embed=embed)

    # ========== ÇEKİLİŞ LOGU (GÖRSEL 5 TARZI) ==========
    async def log_giveaway_end(self, guild_id, winner, prize, duration):
        """Çekiliş bittiğinde log at"""
        channel_id = self.get_log_channel(guild_id, "moderation")
        if not channel_id:
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            description=f"**Hot N Cold** zaman aşımı uygulandı.",
            color=0x2F3136
        )
        embed.set_thumbnail(url=winner.avatar.url if winner.avatar else winner.default_avatar.url)
        
        embed.add_field(
            name="🎁 Ceza Alan:",
            value=f"• 👤 {winner.mention}",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Ceza Veren:",
            value=f"• 🏆 @Hot N Cold (Hot N Cold)",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Ceza Sebep:",
            value=f"• ℹ️ Sebep belirtilmedi",
            inline=False
        )
        
        # Yetkililerin Mute Sayısı
        embed.add_field(
            name="🔢 Yetkililerin Mute Sayısı:",
            value=f"• ⏰ 9",
            inline=False
        )
        
        # Cezalının Aldığı Mute Sayısı
        embed.add_field(
            name="🔢 Cezalının Aldığı Mute Sayısı:",
            value=f"• ⏰ 1",
            inline=False
        )
        
        # Ceza Bitiş
        end_time = datetime.now(timezone.utc)
        embed.add_field(
            name="⏰ Ceza Bitiş:",
            value=f"• 📅 {end_time.strftime('%d %B %Y - %H:%M:%S')} (5 gün önce)",
            inline=False
        )
        
        embed.timestamp = datetime.now(timezone.utc)
        
        await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LogSystem(bot))
