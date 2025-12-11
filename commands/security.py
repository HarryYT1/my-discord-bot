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
    @app_commands.command(name="whitelist", description="Bir kullanıcıyı güvenlik filtrelerinden muaf tutar")
    @app_commands.describe(kullanici="Muaf tutulacak kullanıcı")
    async def whitelist_add(self, interaction: discord.Interaction, kullanici: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 𝐲𝐨𝐧𝐞𝐭𝐢𝐜𝐢 𝐲𝐞𝐭𝐤𝐢𝐧𝐢𝐳 𝐨𝐥𝐦𝐚𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        
        if guild_id not in self.whitelisted_users:
            self.whitelisted_users[guild_id] = []
        
        if kullanici.id in self.whitelisted_users[guild_id]:
            embed = discord.Embed(
                description=f"⚠️ {kullanici.mention} **𝐳𝐚𝐭𝐞𝐧 𝐦𝐮𝐚𝐟 𝐥𝐢𝐬𝐭𝐞𝐬𝐢𝐧𝐝𝐞!**",
                color=0xFFA500
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        self.whitelisted_users[guild_id].append(kullanici.id)
        
        embed = discord.Embed(
            title="✅ 𝐌𝐮𝐚𝐟 𝐋𝐢𝐬𝐭𝐞𝐬𝐢𝐧𝐞 𝐄𝐤𝐥𝐞𝐧𝐝𝐢",
            color=0x00FF00
        )
        embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"{kullanici.mention}\n```{kullanici.name}```", inline=True)
        embed.add_field(name="🛡️ 𝐃𝐮𝐫𝐮𝐦", value="```Muaf```", inline=True)
        embed.add_field(
            name="📋 𝐃𝐞𝐭𝐚𝐲𝐥𝐚𝐫",
            value="```Bu kullanıcı artık tüm güvenlik filtrelerinden muaf tutulacak```",
            inline=False
        )
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        embed.set_footer(text=f"Ekleyen: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)

    # ====== WHITELIST ÇIKAR ======
    @app_commands.command(name="unwhitelist", description="Bir kullanıcıyı muaf listesinden çıkarır")
    @app_commands.describe(kullanici="Muaf listesinden çıkarılacak kullanıcı")
    async def whitelist_remove(self, interaction: discord.Interaction, kullanici: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 𝐲𝐨𝐧𝐞𝐭𝐢𝐜𝐢 𝐲𝐞𝐭𝐤𝐢𝐧𝐢𝐳 𝐨𝐥𝐦𝐚𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        
        if guild_id not in self.whitelisted_users or kullanici.id not in self.whitelisted_users[guild_id]:
            embed = discord.Embed(
                description=f"⚠️ {kullanici.mention} **𝐦𝐮𝐚𝐟 𝐥𝐢𝐬𝐭𝐞𝐬𝐢𝐧𝐝𝐞 𝐝𝐞𝐠𝐢𝐥!**",
                color=0xFFA500
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        self.whitelisted_users[guild_id].remove(kullanici.id)
        
        embed = discord.Embed(
            title="🗑️ 𝐌𝐮𝐚𝐟 𝐋𝐢𝐬𝐭𝐞𝐬𝐢𝐧𝐝𝐞𝐧 𝐂𝐢𝐤𝐚𝐫𝐢𝐥𝐝𝐢",
            color=0xFF6B6B
        )
        embed.add_field(name="👤 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢", value=f"{kullanici.mention}\n```{kullanici.name}```", inline=True)
        embed.add_field(name="🛡️ 𝐃𝐮𝐫𝐮𝐦", value="```Normal```", inline=True)
        embed.add_field(
            name="📋 𝐃𝐞𝐭𝐚𝐲𝐥𝐚𝐫",
            value="```Bu kullanıcı artık güvenlik filtrelerine tabi olacak```",
            inline=False
        )
        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        embed.set_footer(text=f"Çıkaran: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)

    # ====== WHITELIST LİSTESİ ======
    @app_commands.command(name="whitelistshow", description="Muaf tutulan kullanıcıları gösterir")
    async def whitelist_show(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id not in self.whitelisted_users or not self.whitelisted_users[guild_id]:
            embed = discord.Embed(
                description="📋 **𝐌𝐮𝐚𝐟 𝐥𝐢𝐬𝐭𝐞𝐬𝐢 𝐛𝐨𝐬!**",
                color=0x5865F2
            )
            return await interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(
            title="🛡️ 𝐌𝐮𝐚𝐟 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢𝐥𝐚𝐫",
            description="```Aşağıdaki kullanıcılar güvenlik filtrelerinden muaf tutulmaktadır```",
            color=0x00FF7F
        )
        
        users_text = ""
        for user_id in self.whitelisted_users[guild_id]:
            user = interaction.guild.get_member(user_id)
            if user:
                users_text += f"✅ {user.mention} - `{user.name}`\n"
        
        embed.add_field(name=f"👥 𝐓𝐨𝐩𝐥𝐚𝐦 ({len(self.whitelisted_users[guild_id])})", value=users_text or "```Kimse yok```", inline=False)
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)

    # ====== FİLTRE AÇ/KAPAT ======
    @app_commands.command(name="filter", description="Güvenlik filtrelerini açıp kapatır")
    @app_commands.describe(
        filtre="Filtre türü (antilink, antikufur, antispam, reklam)",
        durum="Durumu (aç veya kapat)"
    )
    async def filter_toggle(self, interaction: discord.Interaction, filtre: str, durum: str):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 𝐲𝐨𝐧𝐞𝐭𝐢𝐜𝐢 𝐲𝐞𝐭𝐤𝐢𝐧𝐢𝐳 𝐨𝐥𝐦𝐚𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        filters = self.get_filters(guild_id)
        
        filtre = filtre.lower()
        if filtre not in filters:
            embed = discord.Embed(
                title="❌ 𝐆𝐞𝐜𝐞𝐫𝐬𝐢𝐳 𝐅𝐢𝐥𝐭𝐫𝐞",
                description="```Geçerli filtreler: antilink, antikufur, antispam, reklam```",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if durum not in ["aç", "kapat"]:
            embed = discord.Embed(
                description="❌ **𝐃𝐮𝐫𝐮𝐦 '𝐚𝐜' 𝐯𝐞𝐲𝐚 '𝐤𝐚𝐩𝐚𝐭' 𝐨𝐥𝐦𝐚𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        filters[filtre] = (durum == "aç")
        
        status_emoji = "🟢" if durum == "aç" else "🔴"
        status_color = 0x00FF00 if durum == "aç" else 0xFF0000
        
        embed = discord.Embed(
            title=f"{status_emoji} 𝐅𝐢𝐥𝐭𝐫𝐞 {durum.upper()}𝐈𝐋𝐃𝐈",
            color=status_color
        )
        embed.add_field(name="🔧 𝐅𝐢𝐥𝐭𝐫𝐞", value=f"```{filtre}```", inline=True)
        embed.add_field(name="📊 𝐃𝐮𝐫𝐮𝐦", value=f"```{durum.upper()}```", inline=True)
        embed.set_footer(text=f"Değiştiren: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)

    # ====== FİLTRE DURUMU ======
    @app_commands.command(name="filterstatus", description="Aktif filtrelerin durumunu gösterir")
    async def filter_status(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        filters = self.get_filters(guild_id)
        
        embed = discord.Embed(
            title="🛡️ 𝐆𝐮𝐯𝐞𝐧𝐥𝐢𝐤 𝐅𝐢𝐥𝐭𝐫𝐞𝐥𝐞𝐫𝐢",
            description="```Sunucudaki güvenlik filtrelerinin durumu```",
            color=0x5865F2
        )
        
        for filtre, acik in filters.items():
            durum = "🟢 𝐀𝐂𝐈𝐊" if acik else "🔴 𝐊𝐀𝐏𝐀𝐋𝐈"
            emoji_map = {
                "antilink": "🔗",
                "antikufur": "🚫",
                "antispam": "📵",
                "reklam": "📢"
            }
            embed.add_field(
                name=f"{emoji_map.get(filtre, '🔧')} {filtre.upper()}",
                value=f"```{durum}```",
                inline=True
            )
        
        # Whitelist sayısı
        whitelist_count = len(self.whitelisted_users.get(guild_id, []))
        embed.add_field(
            name="👥 𝐌𝐮𝐚𝐟 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢",
            value=f"```{whitelist_count} kişi```",
            inline=True
        )
        
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now()
        
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
                        title="🔗 𝐋𝐢𝐧𝐤 𝐄𝐧𝐠𝐞𝐥𝐥𝐞𝐧𝐝𝐢",
                        description=f"{msg.author.mention}\n```Link paylaşmak yasaktır!```",
                        color=0xFF0000
                    )
                    embed.set_footer(text="Güvenlik Sistemi", icon_url=msg.author.avatar.url if msg.author.avatar else None)
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
                        title="🚫 𝐊𝐮𝐟𝐮𝐫 𝐄𝐧𝐠𝐞𝐥𝐥𝐞𝐧𝐝𝐢",
                        description=f"{msg.author.mention}\n```Küfür etmek yasaktır!```",
                        color=0xFF0000
                    )
                    embed.set_footer(text="Güvenlik Sistemi", icon_url=msg.author.avatar.url if msg.author.avatar else None)
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
                        title="📢 𝐑𝐞𝐤𝐥𝐚𝐦 𝐄𝐧𝐠𝐞𝐥𝐥𝐞𝐧𝐝𝐢",
                        description=f"{msg.author.mention}\n```Reklam yapmak yasaktır!```",
                        color=0xFF0000
                    )
                    embed.set_footer(text="Güvenlik Sistemi", icon_url=msg.author.avatar.url if msg.author.avatar else None)
                    await msg.channel.send(embed=embed, delete_after=5)
                except:
                    pass
                return

        # ===== Anti-Spam (Geliştirilmiş) =====
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
                            title="📵 𝐒𝐩𝐚𝐦 𝐄𝐧𝐠𝐞𝐥𝐥𝐞𝐧𝐝𝐢",
                            description=f"{msg.author.mention}\n```Çok hızlı mesaj gönderiyorsunuz!```",
                            color=0xFF0000
                        )
                        embed.set_footer(text="Güvenlik Sistemi", icon_url=msg.author.avatar.url if msg.author.avatar else None)
                        await msg.channel.send(embed=embed, delete_after=5)
                    except:
                        pass
                    return
                
                self.antispam[user_id]["last_message_time"] = current_time


async def setup(bot):
    await bot.add_cog(Security(bot))
