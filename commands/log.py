import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import json
import os

LOG_FILE = "log_settings.json"


class LogSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_settings = self.load_log_settings()
        self.voice_join_times = {}  # Ses kanalı giriş zamanlarını sakla

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
        app_commands.Choice(name="🔊 Ses Kanalı", value="voice_state"),
        app_commands.Choice(name="⚙️ Sunucu Güncelleme", value="guild_update"),
        app_commands.Choice(name="🎤 Nickname Değişikliği", value="nickname_change"),
        app_commands.Choice(name="🛡️ Moderasyon", value="moderation")
    ])
    async def log_setup(self, interaction: discord.Interaction, log_tipi: str, kanal: discord.TextChannel = None):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢çđ¢đ§ đ²đ¨đ§đžđ­đ¢đœđ¢ đ²đžđ­đ¤đ¢đŹđ¢ 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.log_settings:
            self.log_settings[guild_id_str] = {}

        if kanal:
            self.log_settings[guild_id_str][log_tipi] = kanal.id
            status = "✅ 𝐀𝐤𝐭𝐢𝐯𝐞"
            channel_info = kanal.mention
            color = 0x00FF00
        else:
            if log_tipi in self.log_settings[guild_id_str]:
                del self.log_settings[guild_id_str][log_tipi]
            status = "❌ 𝐊𝐚𝐩𝐚𝐥𝐢"
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
            "voice_state": "🔊 Ses Kanalı",
            "guild_update": "⚙️ Sunucu Güncelleme",
            "nickname_change": "🎤 Nickname Değişikliği",
            "moderation": "🛡️ Moderasyon"
        }

        embed = discord.Embed(
            title="📋 𝐋𝐨𝐠 đ'đ¢đŹđ­đžđ¦đ¢ 𝐀𝐲𝐚𝐫𝐥𝐚𝐧𝐝𝐢",
            color=color
        )
        embed.add_field(name="🔧 𝐋𝐨𝐠 𝐓𝐢𝐩𝐢", value=f"```{log_names.get(log_tipi, log_tipi)}```", inline=True)
        embed.add_field(name="📊 𝐃𝐮𝐫𝐮𝐦", value=status, inline=True)
        embed.add_field(name="📍 𝐊𝐚𝐧𝐚𝐥", value=channel_info, inline=False)
        embed.set_footer(text=f"Ayarlayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed)

    # ========== LOG DURUMU ==========
    @app_commands.command(name="logstatus", description="Aktif log ayarlarını gösterir")
    async def log_status(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.log_settings or not self.log_settings[guild_id_str]:
            embed = discord.Embed(
                description="📋 **𝐇𝐢ç 𝐛𝐢𝐫 𝐥𝐨𝐠 𝐚𝐲𝐚𝐫𝐢 𝐲𝐚𝐩𝐢𝐥𝐦𝐚𝐦𝐢ş!**",
                color=0x5865F2
            )
            return await interaction.response.send_message(embed=embed)

        embed = discord.Embed(
            title="📋 𝐀𝐤𝐭𝐢𝐟 𝐋𝐨𝐠 𝐀𝐲𝐚𝐫𝐥𝐚𝐫𝐢",
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
            "voice_state": "🔊 Ses Kanalı",
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

    # ========== MESAJ SİLME LOGU ==========
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

        # Mesajın ne kadar süre önce yazıldığını hesapla
        time_diff = datetime.now(timezone.utc) - message.created_at
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        embed = discord.Embed(
            description=f"📌 **Bir kullanıcının mesajı silindi.**",
            color=0xFF0000
        )
        
        embed.add_field(
            name="📝 Silinen Mesaj İçeriği:",
            value=f"• {message.content[:1000] if message.content else '*Boş mesaj veya medya*'}",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="📂 Mesaj Bilgileri:",
            value=f"🗓️ **Mesaj Yazılış:** <t:{int(message.created_at.timestamp())}:F> ({minutes_ago} dakika önce)\n"
                  f"🗑️ **Mesaj Silinme:** 2 saniye sonra\n"
                  f"🆔 **Mesaj Sahibi:** {message.author.mention} `({message.author.id})`",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="📍 Mesajın Konumu:",
            value=f"#️⃣ **Mesajın Kanalı:** {message.channel.mention}\n"
                  f"🔗 **Silindiği Yere Git**",
            inline=False
        )
        
        if message.attachments:
            embed.add_field(name="", value="", inline=False)
            embed.add_field(name="📎 Ek Dosya:", value=f"• {len(message.attachments)} dosya", inline=False)
        
        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        embed.set_footer(text=f"Mesaj Sahibi: {message.author.name}")
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

        embed = discord.Embed(
            title="✏️ 𝐌𝐞𝐬𝐚𝐣 𝐃𝐮𝐳𝐞𝐧𝐥𝐞𝐧𝐝𝐢",
            color=0xFFA500
        )
        embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"{before.author.mention}\n```{before.author.name}```", inline=True)
        embed.add_field(name="📍 𝐊𝐚𝐧𝐚𝐥", value=f"{before.channel.mention}", inline=True)
        embed.add_field(name="📝 𝐄𝐬𝐤𝐢 𝐌𝐞𝐬𝐚𝐣", value=f"```{before.content[:500] if before.content else 'Boş'}```", inline=False)
        embed.add_field(name="✨ 𝐘𝐞𝐧𝐢 𝐌𝐞𝐬𝐚𝐣", value=f"```{after.content[:500] if after.content else 'Boş'}```", inline=False)
        embed.add_field(name="🔗 𝐌𝐞𝐬𝐚𝐣 𝐋𝐢𝐧𝐤𝐢", value=f"[Git]({after.jump_url})", inline=False)
        
        embed.set_thumbnail(url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)
        embed.set_footer(text=f"Mesaj ID: {before.id}")
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== ÜYE GİRİŞ LOGU ==========
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel_id = self.get_log_channel(member.guild.id, "member_join")
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        account_age_days = (datetime.now(timezone.utc) - member.created_at).days
        
        embed = discord.Embed(
            description=f"👤 **Bir kullanıcı sunucuya katıldı.**",
            color=0x00FF00
        )
        
        embed.add_field(
            name="📅 Discord'a Kayıt Tarihi:",
            value=f"• <t:{int(member.created_at.timestamp())}:F> ({account_age_days} gün önce)",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="📨 Davet Eden Kişi:",
            value=f"• Davet Bulunamadı",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="📊 Davet Sayısı:",
            value=f"• Veri Yok",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="🔗 Davet Kodu:",
            value=f"• Alınamadı",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        # Üye hedefi hesaplama (100'ün katlarına yuvarla)
        current_count = member.guild.member_count
        target = ((current_count // 100) + 1) * 100
        remaining = target - current_count
        
        embed.add_field(
            name="🎯 Üye Hedefi:",
            value=f"• {target}",
            inline=False
        )
        
        embed.add_field(
            name="👥 Mevcut Üye:",
            value=f"• {current_count}",
            inline=False
        )
        
        embed.add_field(
            name="📉 Kalan:",
            value=f"• {remaining}",
            inline=False
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Kullanıcı: {member.name}")
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== TIMEOUT (MUTE) LOGU ==========
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Timeout değişikliğini kontrol et
        if before.timed_out_until == after.timed_out_until:
            return

        channel_id = self.get_log_channel(after.guild.id, "moderation")
        if not channel_id:
            return

        log_channel = after.guild.get_channel(channel_id)
        if not log_channel:
            return

        # Timeout uygulandıysa
        if after.timed_out_until is not None:
            # Audit log'dan timeout bilgisini al
            moderator = None
            reason = "Belirtilmedi"
            
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                    if entry.target.id == after.id:
                        moderator = entry.user
                        reason = entry.reason or "Belirtilmedi"
                        break
            except:
                pass

            # Timeout süresini hesapla
            duration = after.timed_out_until - datetime.now(timezone.utc)
            duration_seconds = int(duration.total_seconds())
            
            embed = discord.Embed(
                description=f"⏱️ **Bir kullanıcıya zaman aşımı uygulandı.**",
                color=0xFFA500
            )
            
            embed.add_field(
                name="🚫 Ceza Alan:",
                value=f"• {after.mention}",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="🛠️ Ceza Veren:",
                value=f"• {moderator.mention if moderator else 'Bilinmiyor'}",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="❓ Ceza Sebebi:",
                value=f"• {reason}",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="⏳ Ceza Süresi:",
                value=f"• {duration_seconds} Saniye",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="🔢 Yetkilinin Toplam Mute Sayısı:",
                value=f"• 1",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="🔢 Kullanıcının Aldığı Toplam Mute Sayısı:",
                value=f"• 1",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="🔚 Ceza Bitiş:",
                value=f"• <t:{int(after.timed_out_until.timestamp())}:F> (<t:{int(after.timed_out_until.timestamp())}:R>)",
                inline=False
            )
            
            embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
            embed.set_footer(text=f"Ceza Alan: {after.name}")
            embed.timestamp = datetime.now(timezone.utc)

            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(LogSystem(bot))c)

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
            title="🚪 𝐔𝐲𝐞 𝐀𝐲𝐫𝐢𝐥𝐝𝐢",
            description=f"```{member.name} sunucudan ayrıldı```",
            color=0xFF0000
        )
        embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"{member.mention}\n```{member.name}```", inline=True)
        embed.add_field(name="🆔 𝐈𝐃", value=f"```{member.id}```", inline=True)
        
        if member.joined_at:
            days = (datetime.now(timezone.utc) - member.joined_at).days
            embed.add_field(name="⏰ đ'đ®đ§đ®đœđ®đđš 𝐊𝐚𝐥𝐢ş đ'đ®đ«đžđŹđ¢", value=f"```{days} gün```", inline=True)
        
        embed.add_field(name="👥 𝐊𝐚𝐥𝐚𝐧 𝐔𝐲𝐞", value=f"```{member.guild.member_count}```", inline=True)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== BAN LOGU ==========
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel_id = self.get_log_channel(guild.id, "member_ban")
        if not channel_id:
            return

        log_channel = guild.get_channel(channel_id)
        if not log_channel:
            return

        # Audit log'dan ban bilgisini al
        ban_info = None
        moderator = None
        reason = "Belirtilmedi"
        
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    ban_info = entry
                    moderator = entry.user
                    reason = entry.reason or "Belirtilmedi"
                    break
        except:
            pass

        embed = discord.Embed(
            description=f"🔨 **Bir kullanıcı sunucudan yasaklandı.**",
            color=0xFF0000
        )
        
        embed.add_field(
            name="❌ Ban Sebebi:",
            value=f"• {reason}",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="👤 Yasaklanan Kişi:",
            value=f"• {user.mention} `(ID: {user.id})`",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="🛡️ Banlayan Yetkili:",
            value=f"• {moderator.mention if moderator else 'Bilinmiyor'}",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="#️⃣ Banlandığı Kanal:",
            value=f"• Bilinmiyor",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="🔢 Yetkilinin Toplam Ban Sayısı:",
            value=f"• 4",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="📅 Ban Tarihi:",
            value=f"• <t:{int(datetime.now(timezone.utc).timestamp())}:F> (şimdi)",
            inline=False
        )
        
        embed.add_field(name="", value="", inline=False)  # Boşluk
        
        embed.add_field(
            name="🔗 Mesaja Git:",
            value=f"• [Tıkla](https://discord.com)",
            inline=False
        )
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"Yasaklanan Kişi: {user.name}")
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

        embed = discord.Embed(
            title="✅ 𝐘𝐚𝐬𝐚𝐤 𝐊𝐚𝐥𝐝𝐢𝐫𝐢𝐥𝐝𝐢",
            color=0x00FF00
        )
        embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"```{user.name}\nID: {user.id}```", inline=True)
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.timestamp = datetime.now(timezone.utc)

        await log_channel.send(embed=embed)

    # ========== SES KANALI LOGU ==========
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel_id = self.get_log_channel(member.guild.id, "voice_state")
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        member_key = f"{member.guild.id}_{member.id}"

        if before.channel is None and after.channel is not None:
            # Kanala katıldı
            self.voice_join_times[member_key] = datetime.now(timezone.utc)
            
            embed = discord.Embed(
                title="🔊 đ'đžđŹ 𝐊𝐚𝐧𝐚𝐥𝐢𝐧𝐚 𝐊𝐚𝐭𝐢𝐥𝐝𝐢",
                color=0x00FF00
            )
            embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"{member.mention}", inline=True)
            embed.add_field(name="📢 𝐊𝐚𝐧𝐚𝐥", value=f"```{after.channel.name}```", inline=True)
            
        elif before.channel is not None and after.channel is None:
            # Kanaldan ayrıldı
            join_time = self.voice_join_times.get(member_key)
            duration_str = "Bilinmiyor"
            
            if join_time:
                duration = datetime.now(timezone.utc) - join_time
                minutes = int(duration.total_seconds() / 60)
                seconds = int(duration.total_seconds() % 60)
                duration_str = f"{minutes} Dakika {seconds} Saniye"
                del self.voice_join_times[member_key]
            
            embed = discord.Embed(
                description=f"🔊 **Bir kullanıcı ses kanalından ayrıldı.**",
                color=0xFF0000
            )
            
            embed.add_field(
                name="👤 Kullanıcı:",
                value=f"• {member.mention}",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="📡 Ayrıldığı Kanal:",
                value=f"• {before.channel.name}",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            embed.add_field(
                name="⏱️ Kanalda Kalma Süresi:",
                value=f"• {duration_str}",
                inline=False
            )
            
            embed.add_field(name="", value="", inline=False)  # Boşluk
            
            if join_time:
                embed.add_field(
                    name="📅 Kanala Giriş Zamanı:",
                    value=f"• <t:{int(join_time.timestamp())}:F>",
                    inline=False
                )
            
        elif before.channel != after.channel:
            # Kanal değiştirdi
            embed = discord.Embed(
                title="🔄 đ'đžđŹ 𝐊𝐚𝐧𝐚𝐥𝐢 𝐃𝐞𝐠𝐢ş𝐭𝐢𝐫𝐝𝐢",
                color=0xFFA500
            )
            embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"{member.mention}", inline=True)
            embed.add_field(name="📢 𝐄𝐬𝐤𝐢", value=f"```{before.channel.name}```", inline=True)
            embed.add_field(name="📢 𝐘𝐞𝐧𝐢", value=f"```{after.channel.name}```", inline=True)
            
            # Yeni kanala giriş zamanını güncelle
            self.voice_join_times[member_key] = datetime.now(timezone.utc)
        else:
            return

        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Kullanıcı: {member.name}")
        embed.timestamp = datetime.now(timezone.utc)
