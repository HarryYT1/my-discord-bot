import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class HelpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Botun komutlarını gösterir")
    @app_commands.describe(gizli="Sadece siz görecek misiniz? (Evet/Hayır)")
    async def help_command(self, interaction: discord.Interaction, gizli: bool = True):
        
        class HelpView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.current_page = "ana"

            @discord.ui.button(label="🏠 Ana Sayfa", style=discord.ButtonStyle.blurple)
            async def ana_sayfa(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = self.get_ana_sayfa_embed(interaction)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="🎵 Müzik", style=discord.ButtonStyle.green)
            async def muzik(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = self.get_muzik_embed(interaction)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="👮 Moderasyon", style=discord.ButtonStyle.red)
            async def moderasyon(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = self.get_moderasyon_embed(interaction)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="🎭 Eğlence", style=discord.ButtonStyle.grey)
            async def eglence(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = self.get_eglence_embed(interaction)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="⚙️ Ayarlar", style=discord.ButtonStyle.secondary)
            async def ayarlar(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = self.get_ayarlar_embed(interaction)
                await interaction.response.edit_message(embed=embed, view=self)

            def get_ana_sayfa_embed(self, interaction):
                embed = discord.Embed(
                    title="📚 𝐁𝐨𝐭 𝐘𝐚𝐫𝐝𝐢𝐦 𝐌𝐞𝐧𝐮𝐬𝐮",
                    description="```Merhaba! Ben çok fonksiyonlu bir Discord botuyum. Aşağıdaki butonlardan kategorilere göz atabilirsiniz!```",
                    color=0x5865F2
                )
                
                embed.add_field(
                    name="🎵 𝐌𝐮𝐳𝐢𝐤",
                    value="```Müzik çalma, kuyruk yönetimi```",
                    inline=True
                )
                embed.add_field(
                    name="👮 𝐌𝐨𝐝𝐞𝐫𝐚𝐬𝐲𝐨𝐧",
                    value="```Ban, kick, mute, warn, clear```",
                    inline=True
                )
                embed.add_field(
                    name="🎭 𝐄𝐠𝐥𝐞𝐧𝐜𝐞",
                    value="```Hug, kiss, slap, pat, şaka```",
                    inline=True
                )
                embed.add_field(
                    name="📊 𝐁𝐢𝐥𝐠𝐢",
                    value="```Kullanıcı, sunucu bilgileri```",
                    inline=True
                )
                embed.add_field(
                    name="🛡️ 𝐆𝐮𝐯𝐞𝐧𝐥𝐢𝐤",
                    value="```Anti-spam, anti-link, whitelist```",
                    inline=True
                )
                embed.add_field(
                    name="⚙️ 𝐀𝐲𝐚𝐫𝐥𝐚𝐫",
                    value="```Log, otorol, otocevap```",
                    inline=True
                )

                embed.set_footer(
                    text=f"{interaction.guild.name} • Toplam Komut: 50+",
                    icon_url=interaction.guild.icon.url if interaction.guild.icon else None
                )
                embed.timestamp = datetime.now(timezone.utc)
                
                return embed

            def get_muzik_embed(self, interaction):
                embed = discord.Embed(
                    title="🎵 𝐌𝐮𝐳𝐢𝐤 𝐊𝐨𝐦𝐮𝐭𝐥𝐚𝐫𝐢",
                    description="```YouTube'dan müzik çalma ve kuyruk yönetimi```",
                    color=0xFF0000
                )
                
                commands_list = [
                    ("🎶 /play", "Şarkı çalar"),
                    ("⏸️ /pause", "Şarkıyı duraklatır"),
                    ("▶️ /resume", "Şarkıyı devam ettirir"),
                    ("⏭️ /skip", "Şarkıyı atlar"),
                    ("🛑 /stop", "Müziği durdurur"),
                    ("📋 /queue", "Kuyruğu gösterir"),
                    ("🎵 /nowplaying", "Çalan şarkıyı gösterir")
                ]
                
                for cmd, desc in commands_list:
                    embed.add_field(name=cmd, value=f"```{desc}```", inline=False)
                
                embed.set_footer(text="Müzik komutları için ses kanalında olmanız gerekir")
                return embed

            def get_moderasyon_embed(self, interaction):
                embed = discord.Embed(
                    title="👮 𝐌𝐨𝐝𝐞𝐫𝐚𝐬𝐲𝐨𝐧 𝐊𝐨𝐦𝐮𝐭𝐥𝐚𝐫𝐢",
                    description="```Sunucu moderasyonu ve güvenlik```",
                    color=0xFF0000
                )
                
                commands_list = [
                    ("🔨 /ban", "Kullanıcıyı yasaklar"),
                    ("✅ /unban", "Yasağı kaldırır"),
                    ("👢 /kick", "Kullanıcıyı atar"),
                    ("🔇 /mute", "Kullanıcıyı susturur"),
                    ("🔊 /unmute", "Susturmayı kaldırır"),
                    ("⚠️ /warn", "Kullanıcıyı uyarır"),
                    ("🗑️ /clear", "Mesaj siler"),
                    ("🛡️ /whitelist", "Filtrelerd en muaf tutar"),
                    ("📋 /filter", "Filtreleri ayarlar")
                ]
                
                for cmd, desc in commands_list:
                    embed.add_field(name=cmd, value=f"```{desc}```", inline=False)
                
                embed.set_footer(text="Moderasyon komutları yönetici yetkisi gerektirir")
                return embed

            def get_eglence_embed(self, interaction):
                embed = discord.Embed(
                    title="🎭 𝐄𝐠𝐥𝐞𝐧𝐜𝐞 𝐊𝐨𝐦𝐮𝐭𝐥𝐚𝐫𝐢",
                    description="```Eğlenceli sosyal interaksiyonlar```",
                    color=0xFF69B4
                )
                
                commands_list = [
                    ("🤗 /hug", "Birini sarılır"),
                    ("💋 /kiss", "Birine öpücük gönderir"),
                    ("👋 /slap", "Birine tokat atar"),
                    ("✋ /pat", "Başını okşar"),
                    ("😂 /joke", "Rastgele şaka"),
                    ("🎱 /sor", "8ball sorusu"),
                    ("💬 /say", "Mesaj tekrarlar"),
                    ("🎉 /giveaway", "Çekiliş başlatır")
                ]
                
                for cmd, desc in commands_list:
                    embed.add_field(name=cmd, value=f"```{desc}```", inline=False)
                
                embed.set_footer(text="Her komutta random GIF gönderilir")
                return embed

            def get_ayarlar_embed(self, interaction):
                embed = discord.Embed(
                    title="⚙️ 𝐀𝐲𝐚𝐫 𝐊𝐨𝐦𝐮𝐭𝐥𝐚𝐫𝐢",
                    description="```Sunucu ayarları ve özelleştirme```",
                    color=0x00FF00
                )
                
                commands_list = [
                    ("📋 /log", "Log sistemini ayarlar"),
                    ("📊 /logstatus", "Log durumunu gösterir"),
                    ("🎭 /otorol", "Otorol ayarlar"),
                    ("💬 /otocevap", "Otocevap ekler"),
                    ("📝 /otocevaplist", "Otocevapları gösterir"),
                    ("⏰ /hatirlatici", "Hatırlatıcı kurar"),
                    ("📊 /userinfo", "Kullanıcı bilgisi"),
                    ("🏰 /serverinfo", "Sunucu bilgisi"),
                    ("🏓 /ping", "Bot gecikmesi")
                ]
                
                for cmd, desc in commands_list:
                    embed.add_field(name=cmd, value=f"```{desc}```", inline=False)
                
                embed.set_footer(text="Ayar komutları yönetici yetkisi gerektirebilir")
                return embed

        view = HelpView()
        embed = view.get_ana_sayfa_embed(interaction)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=gizli)


async def setup(bot):
    await bot.add_cog(HelpSystem(bot))
