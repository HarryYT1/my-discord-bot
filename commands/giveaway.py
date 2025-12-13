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

    # ========== GIVEAWAY ==========
    @app_commands.command(name="giveaway", description="🎉 Bir çekiliş başlatır")
    @app_commands.describe(
        sure="Süre (örnek: 10s, 10m, 1h, 1d)",
        kazanan_sayisi="Kaç kişi kazanacak",
        odul="Ödül nedir"
    )
    async def giveaway(self, interaction: discord.Interaction, sure: str, kazanan_sayisi: int, odul: str):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için 'Sunucuyu Yönet' yetkisi gerekli!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

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

        end_time = datetime.utcnow() + timedelta(seconds=duration)

        embed = discord.Embed(
            title="🎉 Çekiliş Başladı!",
            description=f"**Ödül:** {odul}",
            color=0xFF69B4
        )
        embed.add_field(name="🏆 Ödül", value=odul, inline=True)
        embed.add_field(name="👥 Kazanan Sayısı", value=f"{kazanan_sayisi}", inline=True)
        embed.add_field(name="⏰ Bitiş", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(
            name="📋 Nasıl Katılınır?",
            value="🎉 Emojisine tıklayarak çekilişe katılabilirsiniz!",
            inline=False
        )

        await interaction.response.send_message("🎉 **Çekiliş oluşturuluyor...**", ephemeral=True)

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

        # Otomatik bitirme
        asyncio.create_task(self.giveaway_end(msg.id))

    # ========== ÇEKİLİŞ OTOMATİK BİTİRME ==========
    async def giveaway_end(self, giveaway_id):
        if giveaway_id not in self.giveaways:
            return

        data = self.giveaways[giveaway_id]
        msg = data["message"]
        end = data["end"]
        prize = data["prize"]
        winners_count = data["winners"]
        channel = data["channel"]
        host = data["host"]

        now = datetime.utcnow()
        await asyncio.sleep(max(0, (end - now).total_seconds()))

        try:
            updated_msg = await channel.fetch_message(msg.id)
        except:
            del self.giveaways[giveaway_id]
            return

        reaction = discord.utils.get(updated_msg.reactions, emoji="🎉")
        
        if not reaction:
            embed = discord.Embed(
                title="❌ Çekiliş İptal",
                description="Katılım olmadığı için çekiliş iptal edildi",
                color=0xFF0000
            )
            await channel.send(embed=embed)
            del self.giveaways[giveaway_id]
            return

        users = [user async for user in reaction.users() if not user.bot]

        if len(users) == 0:
            embed = discord.Embed(
                title="❌ Çekiliş İptal",
                description="Katılım olmadığı için çekiliş iptal edildi",
                color=0xFF0000
            )
            await channel.send(embed=embed)
            del self.giveaways[giveaway_id]
            return

        kazananlar = random.sample(users, min(winners_count, len(users)))

        # Kazananlara bildirim
        kazanan_mentions = " ".join([u.mention for u in kazananlar])

        embed = discord.Embed(
            title="🎊 Çekiliş Sonuçlandı!",
            description="🎉 Tebrikler kazananlara! 🎉",
            color=0xFFD700
        )
        embed.add_field(name="🏆 Ödül", value=prize, inline=False)
        embed.add_field(
            name="👑 Kazananlar",
            value=kazanan_mentions,
            inline=False
        )
        embed.add_field(name="👥 Katılımcı", value=f"{len(users)} kişi", inline=True)
        embed.add_field(name="🎯 Başlatan", value=host.mention, inline=True)

        await channel.send(f"🎉 {kazanan_mentions}", embed=embed)

        # Mesajı güncelle
        final_embed = discord.Embed(
            title="🎊 Çekiliş Bitti!",
            description=f"**Ödül:** {prize}",
            color=0x808080
        )
        final_embed.add_field(name="👑 Kazananlar", value=kazanan_mentions, inline=False)
        
        try:
            await updated_msg.edit(embed=final_embed)
        except:
            pass

        del self.giveaways[giveaway_id]

    # ========== REACTİON EVENT - KATILIM BİLDİRİMİ ==========
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id not in self.giveaways:
            return

        if str(payload.emoji) != "🎉":
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if member.bot:
            return

        # Kullanıcıya DM gönder
        try:
            embed = discord.Embed(
                title="✅ Çekilişe Katıldınız!",
                description=f"{guild.name} sunucusundaki çekilişe başarıyla katıldınız!",
                color=0x00FF00
            )
            
            data = self.giveaways[payload.message_id]
            embed.add_field(name="🏆 Ödül", value=data['prize'], inline=False)
            embed.add_field(name="⏰ Bitiş", value=f"<t:{int(data['end'].timestamp())}:R>", inline=True)
            embed.add_field(name="👥 Kazanan", value=f"{data['winners']} kişi", inline=True)
            embed.add_field(
                name="🍀 İyi Şanslar!",
                value="Kazanan olmanız için size bol şans diliyoruz!",
                inline=False
            )

            await member.send(embed=embed)
        except discord.Forbidden:
            # DM kapalı, sessizce geç
            pass
        except Exception as e:
            print(f"DM gönderme hatası: {e}")

    # ========== REROLL ==========
    @app_commands.command(name="reroll", description="🔄 Çekilişi yeniden çeker")
    @app_commands.describe(mesaj_id="Çekiliş mesajının ID'si")
    async def reroll(self, interaction: discord.Interaction, mesaj_id: str):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için yetki gerekli!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            mesaj_id = int(mesaj_id)
            msg = await interaction.channel.fetch_message(mesaj_id)
        except:
            embed = discord.Embed(
                description="❌ Mesaj bulunamadı!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        
        if not reaction:
            embed = discord.Embed(
                description="❌ Çekiliş reaksiyonu bulunamadı!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        users = [user async for user in reaction.users() if not user.bot]

        if len(users) == 0:
            embed = discord.Embed(
                description="❌ Katılımcı yok!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        kazanan = random.choice(users)

        embed = discord.Embed(
            title="🔄 Reroll Sonucu",
            description="🎉 Yeni kazanan belirlendi! 🎉",
            color=0xFFD700
        )
        embed.add_field(name="👑 Yeni Kazanan", value=kazanan.mention, inline=False)

        await interaction.response.send_message(f"🎊 {kazanan.mention}", embed=embed)

    # ========== GSTOP ==========
    @app_commands.command(name="gstop", description="🛑 Devam eden bir çekilişi durdurur")
    @app_commands.describe(mesaj_id="Çekiliş mesajının ID'si")
    async def gstop(self, interaction: discord.Interaction, mesaj_id: str):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ Bu komutu kullanmak için yetki gerekli!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            mesaj_id = int(mesaj_id)
        except:
            embed = discord.Embed(
                description="❌ Geçersiz mesaj ID!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if mesaj_id not in self.giveaways:
            embed = discord.Embed(
                description="❌ Bu ID ile aktif çekiliş yok!",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        data = self.giveaways[mesaj_id]
        del self.giveaways[mesaj_id]

        embed = discord.Embed(
            title="🛑 Çekiliş Durduruldu",
            description=f"{data['prize']} ödüllü çekiliş durduruldu",
            color=0xFF0000
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
