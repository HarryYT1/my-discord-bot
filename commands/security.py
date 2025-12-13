import discord
from discord.ext import commands
from discord import app_commands
import re
import time
from datetime import datetime


class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam = {}
        self.whitelisted_users = {}  # guild_id: [user_ids]
        self.enabled_filters = {}  # guild_id: {filter_name: bool}
        
        self.kufur_listesi = [
            "amk", "aq", "orospu", "yarrak", "piç", "göt", "sik", "amına", "salak"
        ]
        
        self.reklam_pattern = r"(discord\.gg|dsc\.gg|invite|boost|nitro|takipçi|instagram\.com|t\.me)"

    def get_filters(self, guild_id):
        """Sunucu için filtreleri getir"""
        if guild_id not in self.enabled_filters:
            self.enabled_filters[guild_id] = {
                "antilink": True,
                "antikufur": True,
                "antispam": True,
                "reklam": True
            }
        return self.enabled_filters[guild_id]

    def is_whitelisted(self, guild_id, user_id):
        """Kullanıcının whitelist'te olup olmadığını kontrol et"""
        if guild_id not in self.whitelisted_users:
            return False
        return user_id in self.whitelisted_users[guild_id]

    # ====== WHITELIST EKLE ======
    @app_commands.command(name="whitelist", description="🛡️ Bir kullanıcıyı güvenlik filtrelerinden muaf tutar")
    @app_commands.describe(kullanici="Muaf tutulacak kullanıcı")
    async def whitelist_add(self, interaction: discord.Interaction, kullanici: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için yönetici yetkiniz olmalı!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        
        if guild_id not in self.whitelisted_users:
            self.whitelisted_users[guild_id] = []
        
        if kullanici.id in self.whitelisted_users[guild_id]:
            embed = discord.Embed(
                description=f"⚠️ {kullanici.mention} zaten muaf listesinde!",
                color=0xFFA500
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        self.whitelisted_users[guild_id].append(kullanici.id)
        
        embed = discord.Embed(
            title="✅ Muaf Listesine Eklendi",
            color=0x00FF00
        )
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n{kullanici.name}", inline=True)
        embed.add_field(name="🛡️ Durum", value="Muaf", inline=True)
        embed.add_field(
            name="📋 Detaylar",
            value="Bu kullanıcı artık tüm güvenlik filtrelerinden muaf tutulacak",
            inline=False
        )
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # ====== WHITELIST ÇIKAR ======
    @app_commands.command(name="unwhitelist", description="🗑️ Bir kullanıcıyı muaf listesinden çıkarır")
    @app_commands.describe(kullanici="Muaf listesinden çıkarılacak kullanıcı")
    async def whitelist_remove(self, interaction: discord.Interaction, kullanici: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için yönetici yetkiniz olmalı!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        
        if guild_id not in self.whitelisted_users or kullanici.id not in self.whitelisted_users[guild_id]:
            embed = discord.Embed(
                description=f"⚠️ {kullanici.mention} muaf listesinde değil!",
                color=0xFFA500
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        self.whitelisted_users[guild_id].remove(kullanici.id)
        
        embed = discord.Embed(
            title="🗑️ Muaf Listesinden Çıkarıldı",
            color=0xFF6B6B
        )
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention}\n{kullanici.name}", inline=True)
        embed.add_field(name="🛡️ Durum", value="Normal", inline=True)
        embed.add_field(
            name="📋 Detaylar",
            value="Bu kullanıcı artık güvenlik filtrelerine tabi olacak",
            inline=False
        )
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # ====== WHITELIST LİSTESİ ======
    @app_commands.command(name="whitelistshow", description="📋 Muaf tutulan kullanıcıları gösterir")
    async def whitelist_show(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id not in self.whitelisted_users or not self.whitelisted_users[guild_id]:
            embed = discord.Embed(
                description="📋 Muaf listesi boş!",
                color=0x5865F2
            )
            return await interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(
            title="🛡️ Muaf Kullanıcılar",
            description="Aşağıdaki kullanıcılar güvenlik filtrelerinden muaf tutulmaktadır",
            color=0x00FF7F
        )
        
        users_text = ""
        for user_id in self.whitelisted_users[guild_id]:
            user = interaction.guild.get_member(user_id)
            if user:
                users_text += f"✅ {user.mention} - `{user.name}`\n"
        
        embed.add_field(name=f"👥 Toplam ({len(self.whitelisted_users[guild_id])})", value=users_text or "Kimse yok", inline=False)
        
        await interaction.response.send_message(embed=embed)

    # ====== FİLTRE AÇ/KAPAT ======
    @app_commands.command(name="filter", description="🔧 Güvenlik filtrelerini açıp kapatır")
    @app_commands.describe(
        filtre="Filtre türü",
        durum="Durumu (aç veya kapat)"
    )
    async def filter_toggle(self, interaction: discord.Interaction, filtre: str, durum: str):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için yönetici yetkiniz olmalı!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        filters = self.get_filters(guild_id)
        
        filtre = filtre.lower()
        if filtre not in filters:
            embed = discord.Embed(
                title="❌ Geçersiz Filtre",
                description="Geçerli filtreler: antilink, antikufur, antispam, reklam",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if durum not in ["aç", "kapat"]:
            embed = discord.Embed(
                description="❌ Durum 'aç' veya 'kapat' olmalı!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        filters[filtre] = (durum == "aç")
        
        status_emoji = "🟢" if durum == "aç" else "🔴"
        status_color = 0x00FF00 if durum == "aç" else 0xFF0000
        
        embed = discord.Embed(
            title=f"{status_emoji} Filtre {durum.upper()}ILDI",
            color=status_color
        )
        embed.add_field(name="🔧 Filtre", value=filtre, inline=True)
        embed.add_field(name="📊 Durum", value=durum.upper(), inline=True)
        
        await interaction.response.send_message(embed=embed)

    # ====== FİLTRE DURUMU ======
    @app_commands.command(name="filterstatus", description="📊 Aktif filtrelerin durumunu gösterir")
    async def filter_status(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        filters = self.get_filters(guild_id)
        
        embed = discord.Embed(
            title="🛡️ Güvenlik Filtreleri",
            description="Sunucudaki güvenlik filtrelerinin durumu",
            color=0x5865F2
        )
        
        for filtre, acik in filters.items():
            durum = "🟢 AÇIK" if acik else "🔴 KAPALI"
            emoji_map = {
                "antilink": "🔗",
                "antikufur": "🚫",
                "antispam": "📵",
                "reklam": "📢"
            }
            embed.add_field(
                name=f"{emoji_map.get(filtre, '🔧')} {filtre.upper()}",
                value=durum,
                inline=True
            )
        
        # Whitelist sayısı
        whitelist_count = len(self.whitelisted_users.get(guild_id, []))
        embed.add_field(
            name="👥 Muaf Kullanıcı",
            value=f"{whitelist_count} kişi",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    # ====== MESAJ EVENTİ ======
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild:
            return
        
        # Whitelist kontrolü
        if self.is_whitelisted(msg.guild.id, msg.author.id):
            return
        
        # Yönetici kontrolü
        if msg.author.guild_permissions.administrator:
            return
        
        filters = self.get_filters(msg.guild.id)
        
        # ===== Anti-Link =====
        if filters.get("antilink", True):
            if "http://" in msg.content or "https://" in msg.content:
                try:
                    await msg.delete()
                    embed = discord.Embed(
                        title="🔗 Link Engellendi",
                        description=f"{msg.author.mention}\nLink paylaşmak yasaktır!",
                        color=0xFF0000
                    )
                    await msg.channel.send(embed=embed, delete_after=5)
                except:
                    pass
                return

        # ===== Küfür Filtresi =====
        if filters.get("antikufur", True):
            if any(k in msg.content.lower() for k in self.kufur_listesi):
                try:
                    await msg.delete()
                    embed = discord.Embed(
                        title="🚫 Küfür Engellendi",
                        description=f"{msg.author.mention}\nKüfür etmek yasaktır!",
                        color=0xFF0000
                    )
                    await msg.channel.send(embed=embed, delete_after=5)
                except:
                    pass
                return

        # ===== Reklam Engeli =====
        if filters.get("reklam", True):
            if re.search(self.reklam_pattern, msg.content.lower()):
                try:
                    await msg.delete()
                    embed = discord.Embed(
                        title="📢 Reklam Engellendi",
                        description=f"{msg.author.mention}\nReklam yapmak yasaktır!",
                        color=0xFF0000
                    )
                    await msg.channel.send(embed=embed, delete_after=5)
                except:
                    pass
                return

        # ===== Anti-Spam =====
        if filters.get("antispam", True):
            user_id = msg.author.id
            current_time = time.time()
            
            if user_id not in self.antispam:
                self.antispam[user_id] = {"count": 1, "last_message_time": current_time}
            else:
                # 5 saniye içinde 5'ten fazla mesaj kontrolü
                time_diff = current_time - self.antispam[user_id]["last_message_time"]
                
                if time_diff < 5:  # 5 saniye içinde
                    self.antispam[user_id]["count"] += 1
                else:
                    # Zaman aşımı, sayacı sıfırla
                    self.antispam[user_id] = {"count": 1, "last_message_time": current_time}
                
                if self.antispam[user_id]["count"] > 5:
                    try:
                        await msg.delete()
                        embed = discord.Embed(
                            title="📵 Spam Engellendi",
                            description=f"{msg.author.mention}\nÇok hızlı mesaj gönderiyorsunuz!",
                            color=0xFF0000
                        )
                        await msg.channel.send(embed=embed, delete_after=5)
                    except:
                        pass
                    return
                
                self.antispam[user_id]["last_message_time"] = current_time


async def setup(bot):
    await bot.add_cog(Security(bot))
