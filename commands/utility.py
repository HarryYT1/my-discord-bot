import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio
import json
import os

# Ayar dosyaları
AUTOROLE_FILE = "autorole_settings.json"
AUTOREPLY_FILE = "autoreply_settings.json"


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autorole_settings = self.load_json(AUTOROLE_FILE)
        self.autoreply_settings = self.load_json(AUTOREPLY_FILE)

    def load_json(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_json(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ========== HATIRLATICI ==========
    @app_commands.command(name="hatirlatici", description="Belirli bir süre sonra sizi hatırlatır")
    @app_commands.describe(
        sure="Süre (örnek: 10s, 5m, 2h, 1d)",
        mesaj="Hatırlatma mesajı",
        gizli="Sadece siz görecek misiniz? (Evet/Hayır)"
    )
    async def hatirlatici(self, interaction: discord.Interaction, sure: str, mesaj: str, gizli: bool = True):
        # Süre dönüştürme
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            time_multiplier = multipliers[sure[-1]]
            duration = int(sure[:-1]) * time_multiplier
        except:
            embed = discord.Embed(
                title="❌ 𝐇𝐚𝐭𝐚𝐥𝐢 𝐒𝐮𝐫𝐞 𝐅𝐨𝐫𝐦𝐚𝐭𝐢",
                description="```Örnek: 10s, 5m, 2h, 1d```",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if duration > 604800:  # 7 gün
            embed = discord.Embed(
                description="❌ **𝐌𝐚𝐤𝐬𝐢𝐦𝐮𝐦 𝟕 𝐠𝐮𝐧 𝐨𝐥𝐚𝐛𝐢𝐥𝐢𝐫!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        end_time = datetime.now(timezone.utc) + timedelta(seconds=duration)

        embed = discord.Embed(
            title="⏰ 𝐇𝐚𝐭𝐢𝐫𝐥𝐚𝐭𝐢𝐜𝐢 𝐊𝐮𝐫𝐮𝐥𝐝𝐮",
            color=0x00FF00
        )
        embed.add_field(name="📝 𝐌𝐞𝐬𝐚𝐣", value=f"```{mesaj}```", inline=False)
        embed.add_field(name="⏱️ 𝐒𝐮𝐫𝐞", value=f"```{sure}```", inline=True)
        embed.add_field(name="📅 𝐁𝐢𝐭𝐢𝐬", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.set_footer(text=f"Hatırlatıcı • {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed, ephemeral=gizli)

        # Hatırlatma görevini başlat
        await asyncio.sleep(duration)

        # Hatırlatma mesajı
        reminder_embed = discord.Embed(
            title="🔔 𝐇𝐚𝐭𝐢𝐫𝐥𝐚𝐭𝐦𝐚!",
            description=f"```{mesaj}```",
            color=0xFFD700
        )
        reminder_embed.add_field(name="⏰ 𝐊𝐮𝐫𝐮𝐥𝐮𝐦 𝐙𝐚𝐦𝐚𝐧𝐢", value=f"<t:{int((end_time - timedelta(seconds=duration)).timestamp())}:R>", inline=True)
        reminder_embed.set_footer(text=f"Hatırlatıcı Sistemi", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        reminder_embed.timestamp = datetime.now(timezone.utc)

        try:
            if interaction.channel:
                await interaction.channel.send(f"{interaction.user.mention}", embed=reminder_embed)
        except:
            # Kanal bulunamazsa DM gönder
            try:
                await interaction.user.send(embed=reminder_embed)
            except:
                pass

    # ========== OTOROL ==========
    @app_commands.command(name="otorol", description="Yeni üyelere otomatik rol verir")
    @app_commands.describe(
        rol="Verilecek rol (boş bırakırsanız kapatılır)",
        gizli="Sadece siz görecek misiniz? (Evet/Hayır)"
    )
    async def otorol(self, interaction: discord.Interaction, rol: discord.Role = None, gizli: bool = True):
        if not interaction.user.guild_permissions.manage_roles:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐑𝐨𝐥𝐥𝐞𝐫𝐢 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id_str = str(interaction.guild.id)

        if rol:
            self.autorole_settings[guild_id_str] = rol.id
            status = "✅ 𝐀𝐤𝐭𝐢𝐟"
            rol_info = rol.mention
            color = 0x00FF00
        else:
            if guild_id_str in self.autorole_settings:
                del self.autorole_settings[guild_id_str]
            status = "❌ 𝐊𝐚𝐩𝐚𝐥𝐢"
            rol_info = "```Kapatıldı```"
            color = 0xFF0000

        self.save_json(AUTOROLE_FILE, self.autorole_settings)

        embed = discord.Embed(
            title="🎭 𝐎𝐭𝐨𝐫𝐨𝐥 𝐀𝐲𝐚𝐫𝐥𝐚𝐧𝐝𝐢",
            color=color
        )
        embed.add_field(name="📊 𝐃𝐮𝐫𝐮𝐦", value=status, inline=True)
        embed.add_field(name="🎭 𝐑𝐨𝐥", value=rol_info, inline=True)
        embed.add_field(
            name="📋 𝐁𝐢𝐥𝐠𝐢",
            value="```Yeni üyeler bu rolü otomatik alacak```" if rol else "```Otorol sistemi kapatıldı```",
            inline=False
        )
        embed.set_footer(text=f"Ayarlayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    # ========== OTOROL EVENT ==========
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id_str = str(member.guild.id)
        
        if guild_id_str not in self.autorole_settings:
            return

        role_id = self.autorole_settings[guild_id_str]
        role = member.guild.get_role(role_id)
        
        if role:
            try:
                await member.add_roles(role)
                print(f"✅ {member.name} üyesine {role.name} rolü verildi")
            except Exception as e:
                print(f"❌ Otorol hatası: {e}")

    # ========== OTOCEVAP ==========
    @app_commands.command(name="otocevap", description="Belirli kelimelere otomatik cevap verir")
    @app_commands.describe(
        anahtar="Tetikleyici kelime",
        cevap="Verilecek cevap (boş bırakırsanız silinir)",
        gizli="Sadece siz görecek misiniz? (Evet/Hayır)"
    )
    async def otocevap(self, interaction: discord.Interaction, anahtar: str, cevap: str = None, gizli: bool = True):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐒𝐮𝐧𝐮𝐜𝐮𝐲𝐮 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.autoreply_settings:
            self.autoreply_settings[guild_id_str] = {}

        anahtar_lower = anahtar.lower()

        if cevap:
            self.autoreply_settings[guild_id_str][anahtar_lower] = cevap
            status = "✅ 𝐄𝐤𝐥𝐞𝐧𝐝𝐢"
            color = 0x00FF00
        else:
            if anahtar_lower in self.autoreply_settings[guild_id_str]:
                del self.autoreply_settings[guild_id_str][anahtar_lower]
            status = "🗑️ 𝐒𝐢𝐥𝐢𝐧𝐝𝐢"
            color = 0xFF0000

        self.save_json(AUTOREPLY_FILE, self.autoreply_settings)

        embed = discord.Embed(
            title="💬 𝐎𝐭𝐨𝐜𝐞𝐯𝐚𝐩 𝐀𝐲𝐚𝐫𝐥𝐚𝐧𝐝𝐢",
            color=color
        )
        embed.add_field(name="🔑 𝐀𝐧𝐚𝐡𝐭𝐚𝐫", value=f"```{anahtar}```", inline=True)
        embed.add_field(name="📊 𝐃𝐮𝐫𝐮𝐦", value=status, inline=True)
        
        if cevap:
            embed.add_field(name="💬 𝐂𝐞𝐯𝐚𝐩", value=f"```{cevap}```", inline=False)
        
        embed.set_footer(text=f"Ayarlayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    # ========== OTOCEVAP LİSTE ==========
    @app_commands.command(name="otocevaplist", description="Tüm otocevapları gösterir")
    async def otocevap_list(self, interaction: discord.Interaction, gizli: bool = True):
        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.autoreply_settings or not self.autoreply_settings[guild_id_str]:
            embed = discord.Embed(
                description="📋 **𝐇𝐢𝐜 𝐨𝐭𝐨𝐜𝐞𝐯𝐚𝐩 𝐭𝐚𝐧𝐢𝐦𝐥𝐚𝐧𝐦𝐚𝐦𝐢𝐬!**",
                color=0x5865F2
            )
            return await interaction.response.send_message(embed=embed, ephemeral=gizli)

        embed = discord.Embed(
            title="💬 𝐎𝐭𝐨𝐜𝐞𝐯𝐚𝐩 𝐋𝐢𝐬𝐭𝐞𝐬𝐢",
            description="```Sunucudaki otomatik cevaplar```",
            color=0x5865F2
        )

        for i, (anahtar, cevap) in enumerate(self.autoreply_settings[guild_id_str].items(), 1):
            embed.add_field(
                name=f"{i}. {anahtar}",
                value=f"```{cevap[:100]}```",
                inline=False
            )

        embed.set_footer(text=f"Toplam {len(self.autoreply_settings[guild_id_str])} otocevap", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.timestamp = datetime.now(timezone.utc)

        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    # ========== OTOCEVAP EVENT ==========
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id_str = str(message.guild.id)
        
        if guild_id_str not in self.autoreply_settings:
            return

        content_lower = message.content.lower()

        for anahtar, cevap in self.autoreply_settings[guild_id_str].items():
            if anahtar in content_lower:
                try:
                    await message.channel.send(cevap)
                except:
                    pass
                break


async def setup(bot):
    await bot.add_cog(Utility(bot))
