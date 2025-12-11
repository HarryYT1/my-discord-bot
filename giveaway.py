import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta


class Giveaway(commands.Cog)
    def __init__(self, bot)
        self.bot = bot
        self.giveaways = {}  # giveaway_id { message msg, end timestamp, prize str, channel channel }

    # ========== GIVEAWAY ==========
    @app_commands.command(name=giveaway, description=Bir çekiliş başlatır)
    @app_commands.describe(
        sure=Süre (örnek 10s, 10m, 1h, 1d),
        kazanan_sayisi=Kaç kişi kazanacak,
        odul=Ödül nedir
    )
    async def giveaway(self, interaction discord.Interaction, sure str, kazanan_sayisi int, , odul str)

        # Süre dönüştürme
        multipliers = {s 1, m 60, h 3600, d 86400}
        try
            time_multiplier = multipliers[sure[-1]]
            duration = int(sure[-1])  time_multiplier
        except
            return await interaction.response.send_message(❌ Süre formatı hatalı! (Ör 10s, 5m, 1h), ephemeral=True)

        end_time = datetime.utcnow() + timedelta(seconds=duration)

        embed = discord.Embed(
            title=🎁 Çekiliş Başladı!,
            description=fÖdül {odul}n
                        fKazanan Sayısı {kazanan_sayisi}n
                        fBitiş t{int(end_time.timestamp())}R,
            color=0x00FF6A,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=Katılmak için 🎉 emojisine tıklayın!)

        await interaction.response.send_message(🎉 Çekiliş başlatıldı!, ephemeral=True)

        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction(🎉)

        self.giveaways[msg.id] = {
            message msg,
            end end_time,
            prize odul,
            winners kazanan_sayisi,
            channel interaction.channel
        }

        # Otomatik bitirme
        asyncio.create_task(self.giveaway_end(msg.id))

    # Çekilişi otomatik bitiren fonksiyon
    async def giveaway_end(self, giveaway_id)
        data = self.giveaways[giveaway_id]
        msg = data[message]
        end = data[end]
        prize = data[prize]
        winners = data[winners]
        channel = data[channel]

        now = datetime.utcnow()
        await asyncio.sleep(max(0, (end - now).total_seconds()))

        updated_msg = await channel.fetch_message(msg.id)

        reaction = discord.utils.get(updated_msg.reactions, emoji=🎉)
        users = await reaction.users().flatten()
        users = [u for u in users if not u.bot]

        if len(users) == 0
            return await channel.send(❌ Çekiliş iptal edildi. Katılım yoktu.)

        kazananlar = random.sample(users, min(winners, len(users)))

        embed = discord.Embed(
            title=🎉 Çekiliş Sonuçlandı!,
            description=fÖdül {prize}nn
                        fKazanan(lar) {', '.join(u.mention for u in kazananlar)},
            color=0xFFD700,
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

        del self.giveaways[giveaway_id]

    # ========== REROLL ==========
    @app_commands.command(name=reroll, description=Çekilişi yeniden çeker)
    async def reroll(self, interaction discord.Interaction, mesaj_id str)

        try
            mesaj_id = int(mesaj_id)
            msg = await interaction.channel.fetch_message(mesaj_id)
        except
            return await interaction.response.send_message(❌ Mesaj bulunamadı!, ephemeral=True)

        reaction = discord.utils.get(msg.reactions, emoji=🎉)
        users = await reaction.users().flatten()
        users = [u for u in users if not u.bot]

        if len(users) == 0
            return await interaction.response.send_message(❌ Katılım yok!, ephemeral=True)

        kazanan = random.choice(users)

        embed = discord.Embed(
            title=🔁 Reroll Sonucu,
            description=fYeni kazanan {kazanan.mention},
            color=0xFFD700,
            timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    # ========== GSTOP ==========
    @app_commands.command(name=gstop, description=Devam eden bir çekilişi durdurur)
    async def gstop(self, interaction discord.Interaction, mesaj_id str)

        try
            mesaj_id = int(mesaj_id)
        except
            return await interaction.response.send_message(❌ Mesaj ID hatalı!, ephemeral=True)

        if mesaj_id not in self.giveaways
            return await interaction.response.send_message(❌ Bu ID ile aktif çekiliş yok!, ephemeral=True)

        data = self.giveaways[mesaj_id]
        del self.giveaways[mesaj_id]

        await i
