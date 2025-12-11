import discord
from discord.ext import commands
from discord import app_commands
from utils.music import YTDLSource
import asyncio


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}

    @app_commands.command(name="play", description="Bir şarkı çalar")
    async def play(self, interaction: discord.Interaction, arama: str):
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None

        if not voice_channel:
            return await interaction.response.send_message("❌ Bir ses kanalına katılmalısın!", ephemeral=True)

        guild_id = interaction.guild.id

        if guild_id not in self.queue:
            self.queue[guild_id] = []

        await interaction.response.send_message("🎧 Şarkı aranıyor, lütfen bekleyin...")
        
        try:
            player = await YTDLSource.from_url(arama, stream=True)
        except Exception as e:
            return await interaction.followup.send(f"❌ Şarkı yüklenirken hata oluştu: {e}")

        self.queue[guild_id].append(player)

        if not interaction.guild.voice_client:
            await voice_channel.connect()

        if not interaction.guild.voice_client.is_playing():
            await self.oynat(interaction.guild)

        await interaction.followup.send(f"🎶 Kuyruğa eklendi: **{player.title}**")

    async def oynat(self, guild):
        guild_id = guild.id
        vc = guild.voice_client

        if guild_id not in self.queue or not self.queue[guild_id]:
            return await vc.disconnect()

        player = self.queue[guild_id].pop(0)

        def after_playing(error):
            coro = self.oynat(guild)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

        vc.play(player, after=after_playing)

    @app_commands.command(name="skip", description="Çalan şarkıyı geçer")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏭️ Şarkı geçildi!")
        else:
            await interaction.response.send_message("⛔ Şu anda çalan bir şarkı yok!")

    @app_commands.command(name="stop", description="Müziği durdurur ve bot çıkar")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            if interaction.guild.id in self.queue:
                self.queue[interaction.guild.id] = []
            await vc.disconnect()
            await interaction.response.send_message("🛑 Müzik durduruldu ve bot kanaldan ayrıldı.")
        else:
            await interaction.response.send_message("❌ Bot ses kanalında değil!")

    @app_commands.command(name="pause", description="Şarkıyı duraklatır")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Şarkı duraklatıldı.")
        else:
            await interaction.response.send_message("❌ Şu anda çalan bir şarkı yok!")

    @app_commands.command(name="resume", description="Şarkıyı devam ettirir")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Şarkı devam ediyor.")
        else:
            await interaction.response.send_message("❌ Şarkı duraklatılmış değil!")

    @app_commands.command(name="queue", description="Kuyruktaki şarkıları gösterir")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.queue or not self.queue[guild_id]:
            return await interaction.response.send_message("❌ Kuyruk boş!")

        embed = discord.Embed(title="🎶 Şarkı Kuyruğu", color=0x5865F2)

        for i, song in enumerate(self.queue[guild_id], start=1):
            embed.add_field(name=f"{i}.", value=song.title, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
