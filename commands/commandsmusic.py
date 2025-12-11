import discord
from discord.ext import commands
from discord import app_commands
from utils.music import YTDLSource
import asyncio


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}

    # ========== PLAY ==========
    @app_commands.command(name="play", description="Bir şarkı çalar")
    async def play(self, interaction: discord.Interaction, *, arama: str):
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None

        if not voice_channel:
            embed = discord.Embed(
                description="❌ **𝐁𝐢𝐫 𝐬𝐞𝐬 𝐤𝐚𝐧𝐚𝐥𝐢𝐧𝐚 𝐤𝐚𝐭𝐢𝐥𝐦𝐚𝐥𝐢𝐬𝐢𝐧!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id

        if guild_id not in self.queue:
            self.queue[guild_id] = []

        # Şarkıyı indir
        embed = discord.Embed(
            title="🎧 𝐌𝐮𝐳𝐢𝐤 𝐀𝐫𝐚𝐧𝐢𝐲𝐨𝐫",
            description="```Lütfen bekleyin, şarkı yükleniyor...```",
            color=0x5865F2
        )
        embed.set_footer(text=f"Arayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed)
        
        try:
            player = await YTDLSource.from_url(arama, stream=True)
        except Exception as e:
            error_embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=error_embed)

        # Kuyruğa ekle
        self.queue[guild_id].append(player)

        if not interaction.guild.voice_client:
            await voice_channel.connect()

        if not interaction.guild.voice_client.is_playing():
            await self.oynat(interaction.guild)
            embed = discord.Embed(
                title="🎶 𝐒𝐢𝐦𝐝𝐢 𝐂𝐚𝐥𝐢𝐧𝐢𝐲𝐨𝐫",
                description=f"```{player.title}```",
                color=0x00FF00
            )
            embed.set_thumbnail(url="https://i.imgur.com/placeholder_music.gif")
            embed.add_field(name="🎤 𝐀𝐫𝐚𝐲𝐚𝐧", value=f"{interaction.user.mention}", inline=True)
            embed.add_field(name="📊 𝐊𝐮𝐲𝐫𝐮𝐤", value=f"```{len(self.queue[guild_id])}```", inline=True)
            embed.set_footer(text="Müzik keyfini çıkarın! 🎵")
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="➕ 𝐊𝐮𝐲𝐫𝐮𝐠𝐚 𝐄𝐤𝐥𝐞𝐧𝐝𝐢",
                description=f"```{player.title}```",
                color=0xFFD700
            )
            embed.add_field(name="📍 𝐒𝐢𝐫𝐚𝐝𝐚", value=f"```{len(self.queue[guild_id])}```", inline=True)
            embed.add_field(name="🎤 𝐄𝐤𝐥𝐞𝐲𝐞𝐧", value=f"{interaction.user.mention}", inline=True)
            embed.set_footer(text=f"Toplam {len(self.queue[guild_id])} şarkı kuyrukta bekliyor")
            await interaction.followup.send(embed=embed)

    async def oynat(self, guild):
        guild_id = guild.id
        vc = guild.voice_client

        if not self.queue[guild_id]:
            self.now_playing.pop(guild_id, None)
            embed = discord.Embed(
                description="👋 **𝐊𝐮𝐲𝐫𝐮𝐤 𝐛𝐢𝐭𝐭𝐢, 𝐠𝐨𝐫𝐮𝐬𝐦𝐞𝐤 𝐮𝐳𝐞𝐫𝐞!**",
                color=0xFF6B6B
            )
            return await vc.disconnect()

        player = self.queue[guild_id].pop(0)
        self.now_playing[guild_id] = player

        def after_playing(error):
            if error:
                print(f"Oynatma hatası: {error}")
            asyncio.run_coroutine_threadsafe(self.oynat(guild), self.bot.loop)

        vc.play(player, after=after_playing)

    # ========== SKIP ==========
    @app_commands.command(name="skip", description="Çalan şarkıyı geçer")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            embed = discord.Embed(
                title="⏭️ 𝐒𝐚𝐫𝐤𝐢 𝐀𝐭𝐥𝐚𝐧𝐝𝐢",
                description="```Sonraki şarkıya geçiliyor...```",
                color=0x00FF00
            )
            embed.set_footer(text=f"Atlayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ **𝐒𝐮 𝐚𝐧𝐝𝐚 𝐜𝐚𝐥𝐚𝐧 𝐛𝐢𝐫 𝐬𝐚𝐫𝐤𝐢 𝐲𝐨𝐤!**",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== STOP ==========
    @app_commands.command(name="stop", description="Müziği durdurur ve bot çıkar")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            self.queue[interaction.guild.id] = []
            self.now_playing.pop(interaction.guild.id, None)
            embed = discord.Embed(
                title="🛑 𝐌𝐮𝐳𝐢𝐤 𝐃𝐮𝐫𝐝𝐮𝐫𝐮𝐥𝐝𝐮",
                description="```Bot ses kanalından ayrıldı```",
                color=0xFF0000
            )
            embed.set_footer(text=f"Durduran: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ **𝐁𝐨𝐭 𝐬𝐞𝐬 𝐤𝐚𝐧𝐚𝐥𝐢𝐧𝐝𝐚 𝐝𝐞𝐠𝐢𝐥!**",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== PAUSE ==========
    @app_commands.command(name="pause", description="Şarkıyı duraklatır")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            embed = discord.Embed(
                title="⏸️ 𝐒𝐚𝐫𝐤𝐢 𝐃𝐮𝐫𝐚𝐤𝐥𝐚𝐭𝐢𝐥𝐝𝐢",
                description="```Müzik duraklatıldı```",
                color=0xFFA500
            )
            embed.set_footer(text=f"Durakl atan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ **𝐒𝐮 𝐚𝐧𝐝𝐚 𝐜𝐚𝐥𝐚𝐧 𝐛𝐢𝐫 𝐬𝐚𝐫𝐤𝐢 𝐲𝐨𝐤!**",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== RESUME ==========
    @app_commands.command(name="resume", description="Şarkıyı devam ettirir")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            embed = discord.Embed(
                title="▶️ 𝐒𝐚𝐫𝐤𝐢 𝐃𝐞𝐯𝐚𝐦 𝐄𝐝𝐢𝐲𝐨𝐫",
                description="```Müzik devam ediyor```",
                color=0x00FF00
            )
            embed.set_footer(text=f"Devam ettiren: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ **𝐒𝐚𝐫𝐤𝐢 𝐝𝐮𝐫𝐚𝐤𝐥𝐚𝐭𝐢𝐥𝐦𝐚𝐦𝐢𝐬!**",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # ========== QUEUE ==========
    @app_commands.command(name="queue", description="Kuyruktaki şarkıları gösterir")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id not in self.queue or not self.queue[guild_id]:
            embed = discord.Embed(
                description="❌ **𝐊𝐮𝐲𝐫𝐮𝐤 𝐛𝐨𝐬!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="🎶 𝐒𝐚𝐫𝐤𝐢 𝐊𝐮𝐲𝐫𝐮𝐠𝐮",
            color=0x9B59B6
        )

        # Şu an çalan
        if guild_id in self.now_playing:
            embed.add_field(
                name="▶️ 𝐒𝐢𝐦𝐝𝐢 𝐂𝐚𝐥𝐢𝐲𝐨𝐫",
                value=f"```{self.now_playing[guild_id].title}```",
                inline=False
            )

        # Kuyruk
        if self.queue[guild_id]:
            queue_text = ""
            for i, song in enumerate(self.queue[guild_id][:10], start=1):
                queue_text += f"`{i}.` {song.title}\n"
            
            embed.add_field(
                name=f"📋 𝐒𝐢𝐫𝐚𝐝𝐚𝐤𝐢 𝐒𝐚𝐫𝐤𝐢𝐥𝐚𝐫 ({len(self.queue[guild_id])})",
                value=queue_text,
                inline=False
            )

        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed)

    # ========== NOW PLAYING ==========
    @app_commands.command(name="nowplaying", description="Şu an çalan şarkıyı gösterir")
    async def nowplaying(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id not in self.now_playing:
            embed = discord.Embed(
                description="❌ **𝐒𝐮 𝐚𝐧𝐝𝐚 𝐜𝐚𝐥𝐚𝐧 𝐛𝐢𝐫 𝐬𝐚𝐫𝐤𝐢 𝐲𝐨𝐤!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        player = self.now_playing[guild_id]
        embed = discord.Embed(
            title="🎵 𝐒𝐢𝐦𝐝𝐢 𝐂𝐚𝐥𝐢𝐧𝐢𝐲𝐨𝐫",
            description=f"```{player.title}```",
            color=0x1DB954
        )
        embed.set_footer(text="Müziğin tadını çıkarın! 🎧")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
