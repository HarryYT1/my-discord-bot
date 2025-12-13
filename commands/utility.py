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
    @app_commands.command(name="hatirlatici", description="⏰ Belirli bir süre sonra sizi hatırlatır")
    @app_commands.describe(
        sure="Süre (örnek: 10s, 5m, 2h, 1d)",
        mesaj="Hatırlatma mesajı",
        gizli="Sadece siz görecek misiniz?"
    )
    async def hatirlatici(self, interaction: discord.Interaction, sure: str, mesaj: str, gizli: bool = True):
        # Süre dönüştürme
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            time_multiplier = multipliers[sure[-1]]
            duration = int(sure[:-1]) * time_multiplier
        except:
            embed = discord.Embed(
                title="❌ Hatalı Süre Formatı",
                description="Örnek: 10s, 5m, 2h, 1d",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if duration > 604800:  # 7 gün
            embed = discord.Embed(
                description="❌ Maksimum 7 gün olabilir!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        end_time = datetime.now(timezone.utc) + timedelta(seconds=duration)

        embed = discord.Embed(
            title="⏰ Hatırlatıcı Kuruldu",
            color=0x00FF00
        )
        embed.add_field(name="📝 Mesaj", value=mesaj, inline=False)
        embed.add_field(name="⏱️ Süre", value=sure, inline=True)
        embed.add_field(name="📅 Bitiş", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=gizli)

        # Hatırlatma görevini başlat
        await asyncio.sleep(duration)

        # Hatırlatma mesajı
        reminder_embed = discord.Embed(
            title="🔔 Hatırlatma!",
            description=mesaj,
            color=0xFFD700
        )

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
    @app_commands.command(name="otorol", description="🎭 Yeni üyelere otomatik rol verir")
    @app_commands.describe(
        rol="Verilecek rol (boş bırakırsanız kapatılır)",
        gizli="Sadece siz görecek misiniz?"
    )
    async def otorol(self, interaction: discord.Interaction, rol: discord.Role = None, gizli: bool = True):
        if not interaction.user.guild_permissions.manage_roles:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için 'Rolleri Yönet' yetkisi gerekli!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id_str = str(interaction.guild.id)

        if rol:
            self.autorole_settings[guild_id_str] = rol.id
            status = "✅ Aktif"
            rol_info = rol.mention
            color = 0x00FF00
            bilgi = "Yeni üyeler bu rolü otomatik alacak"
        else:
            if guild_id_str in self.autorole_settings:
                del self.autorole_settings[guild_id_str]
            status = "❌ Kapalı"
            rol_info = "Kapatıldı"
            color = 0xFF0000
            bilgi = "Otorol sistemi kapatıldı"

        self.save_json(AUTOROLE_FILE, self.autorole_settings)

        embed = discord.Embed(
            title="🎭 Otorol Ayarlandı",
            color=color
        )
        embed.add_field(name="📊 Durum", value=status, inline=True)
        embed.add_field(name="🎭 Rol", value=rol_info, inline=True)
        embed.add_field(name="📋 Bilgi", value=bilgi, inline=False)

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
    @app_commands.command(name="otocevap", description="💬 Belirli kelimelere otomatik cevap verir")
    @app_commands.describe(
        anahtar="Tetikleyici kelime",
        cevap="Verilecek cevap (boş bırakırsanız silinir)",
        gizli="Sadece siz görecek misiniz?"
    )
    async def otocevap(self, interaction: discord.Interaction, anahtar: str, cevap: str = None, gizli: bool = True):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için 'Sunucuyu Yönet' yetkisi gerekli!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.autoreply_settings:
            self.autoreply_settings[guild_id_str] = {}

        anahtar_lower = anahtar.lower()

        if cevap:
            self.autoreply_settings[guild_id_str][anahtar_lower] = cevap
            status = "✅ Eklendi"
            color = 0x00FF00
        else:
            if anahtar_lower in self.autoreply_settings[guild_id_str]:
                del self.autoreply_settings[guild_id_str][anahtar_lower]
            status = "🗑️ Silindi"
            color = 0xFF0000

        self.save_json(AUTOREPLY_FILE, self.autoreply_settings)

        embed = discord.Embed(
            title="💬 Otocevap Ayarlandı",
            color=color
        )
        embed.add_field(name="🔑 Anahtar", value=anahtar, inline=True)
        embed.add_field(name="📊 Durum", value=status, inline=True)
        
        if cevap:
            embed.add_field(name="💬 Cevap", value=cevap, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    # ========== OTOCEVAP LİSTE ==========
    @app_commands.command(name="otocevaplist", description="📝 Tüm otocevapları gösterir")
    async def otocevap_list(self, interaction: discord.Interaction, gizli: bool = True):
        guild_id_str = str(interaction.guild.id)
        
        if guild_id_str not in self.autoreply_settings or not self.autoreply_settings[guild_id_str]:
            embed = discord.Embed(
                description="📋 Hiç otocevap tanımlanmamış!",
                color=0x5865F2
            )
            return await interaction.response.send_message(embed=embed, ephemeral=gizli)

        embed = discord.Embed(
            title="💬 Otocevap Listesi",
            description="Sunucudaki otomatik cevaplar",
            color=0x5865F2
        )

        for i, (anahtar, cevap) in enumerate(self.autoreply_settings[guild_id_str].items(), 1):
            embed.add_field(
                name=f"{i}. {anahtar}",
                value=cevap[:100],
                inline=False
            )

        embed.set_footer(text=f"Toplam {len(self.autoreply_settings[guild_id_str])} otocevap")

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
                    # Mesajı yanıtla
                    await message.reply(cevap, mention_author=True)
                except:
                    pass
                break


async def setup(bot):
    await bot.add_cog(Utility(bot))
