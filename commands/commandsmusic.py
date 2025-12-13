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

    @app_commands.command(name="play", description="🎶 Bir şarkı çalar")
    @app_commands.describe(arama="YouTube linki veya şarkı adı")
    async def play(self, interaction: discord.Interaction, arama: str):
        voice_channel = interaction.user.voice.channel if interaction.user.voice else None

        if not voice_channel:
            embed = discord.Embed(
                description="🚫 **Bir ses kanalına katılman gerekiyor!**",
                color=0xFF4D4D
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guild_id = interaction.guild.id
        self.queue.setdefault(guild_id, [])

        loading = discord.Embed(
            title="🔎 𝗠𝘂̈𝘇𝗶𝗸 𝗔𝗿𝗮𝗻𝗶𝘆𝗼𝗿...",
            description="```⏳ Şarkı hazırlanıyor, lütfen bekleyin...```",
            color=0x5865F2
        )
        loading.set_footer(text=f"🎧 İsteyen: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=loading, ephemeral=True)

        try:
            player = await YTDLSource.from_url(arama, stream=True)
        except Exception as e:
            return await interaction.followup.send(
                embed=discord.Embed(
                    description=f"❌ **Hata oluştu:** ```{e}```",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        self.queue[guild_id].append(player)

        if not interaction.guild.voice_client:
            await voice_channel.connect()

        if not interaction.guild.voice_client.is_playing():
            await self.oynat(interaction.guild)
            embed = discord.Embed(
                title="▶️ 𝗦̧𝗶𝗺𝗱𝗶 𝗖̧𝗮𝗹𝗶𝘆𝗼𝗿",
                description=f"🎵 **{player.title}**",
                color=0x1DB954
            )
            embed.add_field(name="🙋‍♂️ Ekleyen", value=interaction.user.mention)
            embed.add_field(name="📀 Kuyruk", value=f"`{len(self.queue[guild_id])} şarkı`")
            embed.set_footer(text="✨ Keyifli dinlemeler!")
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="➕ 𝗞𝘂𝘆𝗿𝘂𝗴̆𝗮 𝗘𝗸𝗹𝗲𝗻𝗱𝗶",
                description=f"🎶 **{player.title}**",
                color=0xFFD700
            )
            embed.add_field(name="📍 Sıra", value=f"`{len(self.queue[guild_id])}`")
            embed.add_field(name="👤 Ekleyen", value=interaction.user.mention)
            embed.set_footer(text="🎼 Müzik kuyruğa eklendi")
            await interaction.followup.send(embed=embed)

    async def oynat(self, guild):
        guild_id = guild.id
        vc = guild.voice_client

        if not self.queue.get(guild_id):
            self.now_playing.pop(guild_id, None)
            return await vc.disconnect()

        player = self.queue[guild_id].pop(0)
        self.now_playing[guild_id] = player

        def after_playing(error):
            coro = self.oynat(guild)
            asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

        vc.play(player, after=after_playing)

    @app_commands.command(name="skip", description="⏭️ Şarkıyı atlar")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏭️ Şarkı Geçildi",
                    description="```Bir sonraki şarkıya geçiliyor...```",
                    color=0x00FF99
                )
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 **Çalan şarkı yok!**",
                    color=0xFF0000
                ),
                ephemeral=True
            )

    @app_commands.command(name="queue", description="📜 Şarkı kuyruğunu gösterir")
    async def queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if not self.queue.get(guild_id) and guild_id not in self.now_playing:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="📭 **Kuyruk tamamen boş!**",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        embed = discord.Embed(title="🎶 𝗠𝘂̈𝘇𝗶𝗸 𝗞𝘂𝘆𝗿𝘂𝗴̆𝘂", color=0x9B59B6)

        if guild_id in self.now_playing:
            embed.add_field(
                name="▶️ Şimdi Çalıyor",
                value=f"**{self.now_playing[guild_id].title}**",
                inline=False
            )

        if self.queue.get(guild_id):
            text = ""
            for i, song in enumerate(self.queue[guild_id][:10], start=1):
                text += f"`{i}.` {song.title}\n"
            embed.add_field(name="📀 Sıradaki Şarkılar", value=text, inline=False)

        embed.set_footer(text=f"👀 Görüntüleyen: {interaction.user.name}")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
