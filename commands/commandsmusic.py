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

    @app_commands.command(name="play", description="🎵 Bir şarkı çalar")
    @app_commands.describe(arama="YouTube linki veya şarkı adı")
    async def play(self, interaction: discord.Interaction, arama: str):
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None

        if not voice_channel:
            embed = discord.Embed(
                description="❌ Bir ses kanalına katılmalısın!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id

        if guild_id not in self.queue:
            self.queue[guild_id] = []

        embed = discord.Embed(
            title="🔍 Şarkı Aranıyor...",
            description="Lütfen bekleyin, şarkı yükleniyor...",
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        try:
            player = await YTDLSource.from_url(arama, stream=True)
        except Exception as e:
            error_embed = discord.Embed(
                description=f"❌ Hata: {str(e)}",
                color=0xFF0000
            )
            return await interaction.followup.send(embed=error_embed, ephemeral=True)

        self.queue[guild_id].append(player)

        if not interaction.guild.voice_client:
            await voice_channel.connect()

        if not interaction.guild.voice_client.is_playing():
            await self.oynat(interaction.guild)
            embed = discord.Embed(
                title="▶️ Şimdi Çalıyor",
                description=f"{player.title}",
                color=0x1DB954
            )
            embed.add_field(name="👤 Arayan", value=interaction.user.mention, inline=True)
            embed.add_field(name="📊 Kuyruk", value=f"{len(self.queue[guild_id])} şarkı", inline=True)
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="➕ Kuyruğa Eklendi",
                description=f"{player.title}",
                color=0xFFD700
            )
            embed.add_field(name="📝 Sıra", value=f"{len(self.queue[guild_id])}", inline=True)
            embed.add_field(name="👤 Ekleyen", value=interaction.user.mention, inline=True)
            await interaction.followup.send(embed=embed)

    async def oynat(self, guild):
        guild_id = guild.id
        vc = guild.voice_client

        if guild_id not in self.queue or not self.queue[guild_id]:
            self.now_playing.pop(guild_id, None)
            return await vc.disconnect()

        player = self.queue[guild_id].pop(0)
        self.now_playing[guild_id] = player

        def after_playing(error):
            if error:
                print(f"Oynatma hatası: {error}")
            coro = self.oynat(guild)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

        vc.play(player, after=after_playing)

    @app_commands.command(name="skip", description="⏭️ Çalan şarkıyı geçer")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            embed = discord.Embed(
                title="⏭️ Şarkı Atlandı",
                description="Sonraki şarkıya geçiliyor...",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Şu anda çalan bir şarkı yok!",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stop", description="⏹️ Müziği durdurur ve botu çıkarır")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            if interaction.guild.id in self.queue:
                self.queue[interaction.guild.id] = []
            self.now_playing.pop(interaction.guild.id, None)
            await vc.disconnect()
            embed = discord.Embed(
                title="🛑 Müzik Durduruldu",
                description="Bot ses kanalından ayrıldı",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Bot ses kanalında değil!",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="pause", description="⏸️ Şarkıyı duraklatır")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            embed = discord.Embed(
                title="⏸️ Şarkı Duraklatıldı",
                description="Müzik duraklatıldı",
                color=0xFFA500
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Şu anda çalan bir şarkı yok!",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="resume", description="▶️ Şarkıyı devam ettirir")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            embed = discord.Embed(
                title="▶️ Şarkı Devam Ediyor",
                description="Müzik devam ediyor",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Şarkı duraklatılmamış!",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="queue", description="📋 Kuyruktaki şarkıları gösterir")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id not in self.queue or not self.queue[guild_id]:
            if guild_id not in self.now_playing:
                embed = discord.Embed(
                    description="❌ Kuyruk boş ve şu anda çalan şarkı yok!",
                    color=0xFF0000
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="🎶 Şarkı Kuyruğu",
            color=0x9B59B6
        )

        if guild_id in self.now_playing:
            embed.add_field(
                name="▶️ Şimdi Çalıyor",
                value=f"{self.now_playing[guild_id].title}",
                inline=False
            )

        if guild_id in self.queue and self.queue[guild_id]:
            queue_text = ""
            for i, song in enumerate(self.queue[guild_id][:10], start=1):
                queue_text += f"`{i}.` {song.title}\n"
            
            embed.add_field(
                name=f"📋 Sıradaki Şarkılar ({len(self.queue[guild_id])})",
                value=queue_text,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="🎵 Şu an çalan şarkıyı gösterir")
    async def nowplaying(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id not in self.now_playing:
            embed = discord.Embed(
                description="❌ Şu anda çalan bir şarkı yok!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        player = self.now_playing[guild_id]
        embed = discord.Embed(
            title="🎵 Şimdi Çalınıyor",
            description=f"{player.title}",
            color=0x1DB954
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
