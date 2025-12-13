import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}

    # ================== GIVEAWAY ==================
    @app_commands.command(name="giveaway", description="🎉 Muhteşem bir çekiliş başlatır")
    @app_commands.describe(
        sure="Süre (10s, 10m, 1h, 1d)",
        kazanan_sayisi="Kazanan kişi sayısı",
        odul="Çekiliş ödülü"
    )
    async def giveaway(self, interaction: discord.Interaction, sure: str, kazanan_sayisi: int, odul: str):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 **Bu komut için `Sunucuyu Yönet` yetkisi gerekli!**",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            duration = int(sure[:-1]) * multipliers[sure[-1]]
        except:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⚠️ Hatalı Süre Formatı",
                    description="```Örnek kullanım: 10s | 5m | 2h | 1d```",
                    color=0xFF4D4D
                ),
                ephemeral=True
            )

        end_time = datetime.utcnow() + timedelta(seconds=duration)

        embed = discord.Embed(
            title="🎉✨ ÇEKİLİŞ BAŞLADI!",
            description=f"```🎁 {odul}```",
            color=0xFF69B4
        )
        embed.add_field(name="🏆 ÖDÜL", value=f"```{odul}```", inline=True)
        embed.add_field(name="👥 KAZANAN", value=f"```{kazanan_sayisi} kişi```", inline=True)
        embed.add_field(name="⏰ BİTİŞ", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(
            name="📌 NASIL KATILINIR?",
            value="```🎉 emojisine tıklayarak katılabilirsiniz```",
            inline=False
        )
        embed.set_footer(
            text=f"🎤 Başlatan: {interaction.user.name}",
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.set_thumbnail(url="https://i.imgur.com/giveaway_icon.gif")
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message(
            "✨ **Çekiliş hazırlanıyor...**",
            ephemeral=True
        )

        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🎉")

        self.giveaways[msg.id] = {
            "message": msg,
            "end": end_time,
            "prize": odul,
            "winners": kazanan_sayisi,
            "channel": interaction.channel,
            "host": interaction.user
        }

        asyncio.create_task(self.giveaway_end(msg.id))

    # ================== GIVEAWAY END ==================
    async def giveaway_end(self, giveaway_id):
        if giveaway_id not in self.giveaways:
            return

        data = self.giveaways[giveaway_id]
        msg = data["message"]

        await asyncio.sleep(max(0, (data["end"] - datetime.utcnow()).total_seconds()))

        try:
            updated_msg = await data["channel"].fetch_message(msg.id)
        except:
            del self.giveaways[giveaway_id]
            return

        reaction = discord.utils.get(updated_msg.reactions, emoji="🎉")
        users = [u async for u in reaction.users() if not u.bot] if reaction else []

        if not users:
            embed = discord.Embed(
                title="❌ ÇEKİLİŞ İPTAL",
                description="```Katılım olmadığı için iptal edildi```",
                color=0xFF0000
            )
            await data["channel"].send(embed=embed)
            del self.giveaways[giveaway_id]
            return

        kazananlar = random.sample(users, min(data["winners"], len(users)))
        mentions = " ".join(u.mention for u in kazananlar)

        embed = discord.Embed(
            title="🎊✨ ÇEKİLİŞ SONUÇLANDI!",
            description="```🎉 Tebrikler kazananlar! 🎉```",
            color=0xFFD700
        )
        embed.add_field(name="🏆 ÖDÜL", value=f"```{data['prize']}```", inline=False)
        embed.add_field(name="👑 KAZANANLAR", value=mentions, inline=False)
        embed.add_field(name="👥 KATILIMCI", value=f"`{len(users)} kişi`", inline=True)
        embed.add_field(name="🎤 BAŞLATAN", value=data["host"].mention, inline=True)
        embed.set_thumbnail(url="https://i.imgur.com/winner_icon.gif")
        embed.set_footer(text="💖 Katıldığınız için teşekkürler")
        embed.timestamp = datetime.utcnow()

        await data["channel"].send(f"🎉 {mentions}", embed=embed)

        final = discord.Embed(
            title="🏁 ÇEKİLİŞ BİTTİ",
            description=f"```{data['prize']}```",
            color=0x808080
        )
        final.add_field(name="👑 Kazananlar", value=mentions, inline=False)
        final.set_footer(text="🎁 Çekiliş sona erdi")

        try:
            await updated_msg.edit(embed=final)
        except:
            pass

        del self.giveaways[giveaway_id]

    # ================== REROLL ==================
    @app_commands.command(name="reroll", description="🔄 Çekilişi yeniden çeker")
    async def reroll(self, interaction: discord.Interaction, mesaj_id: str):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="🚫 Yetkin yok!",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        try:
            msg = await interaction.channel.fetch_message(int(mesaj_id))
        except:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="❌ Mesaj bulunamadı!",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        users = [u async for u in reaction.users() if not u.bot] if reaction else []

        if not users:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="❌ Katılımcı yok!",
                    color=0xFF0000
                ),
                ephemeral=True
            )

        kazanan = random.choice(users)

        embed = discord.Embed(
            title="🔄 REROLL SONUCU",
            description="```🎉 Yeni kazanan belirlendi```",
            color=0xFFD700
        )
        embed.add_field(name="👑 Kazanan", value=kazanan.mention)
        embed.set_thumbnail(url=kazanan.avatar.url if kazanan.avatar else kazanan.default_avatar.url)
        embed.set_footer(text=f"Yapan: {interaction.user.name}")
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message(f"🎊 {kazanan.mention}", embed=embed)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
