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
    @app_commands.command(name="giveaway", description="Bir çekiliş başlatır")
    @app_commands.describe(
        sure="Süre (örnek: 10s, 10m, 1h, 1d)",
        kazanan_sayisi="Kaç kişi kazanacak",
        odul="Ödül nedir"
    )
    async def giveaway(self, interaction: discord.Interaction, sure: str, kazanan_sayisi: int, odul: str):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 '𝐒𝐮𝐧𝐮𝐜𝐮𝐲𝐮 𝐘𝐨𝐧𝐞𝐭' 𝐲𝐞𝐭𝐤𝐢𝐬𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
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
                title="❌ 𝐇𝐚𝐭𝐚𝐥𝐢 𝐒𝐮𝐫𝐞 𝐅𝐨𝐫𝐦𝐚𝐭𝐢",
                description="```Örnek: 10s, 5m, 2h, 1d```",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        end_time = datetime.utcnow() + timedelta(seconds=duration)

        embed = discord.Embed(
            title="🎉 𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐁𝐚𝐬𝐥𝐚𝐝𝐢!",
            description=f"```{odul}```",
            color=0xFF69B4
        )
        embed.add_field(name="🏆 𝐎𝐝𝐮𝐥", value=f"```{odul}```", inline=True)
        embed.add_field(name="👥 𝐊𝐚𝐳𝐚𝐧𝐚𝐧 𝐒𝐚𝐲𝐢𝐬𝐢", value=f"```{kazanan_sayisi}```", inline=True)
        embed.add_field(name="⏰ 𝐁𝐢𝐭𝐢𝐬", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(
            name="📋 𝐍𝐚𝐬𝐢𝐥 𝐊𝐚𝐭𝐢𝐥𝐢𝐧𝐢𝐫?",
            value="```🎉 Emojisine tıklayarak çekilişe katılabilirsiniz!```",
            inline=False
        )
        embed.set_footer(text=f"Başlatan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.set_thumbnail(url="https://i.imgur.com/giveaway_icon.gif")
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message("🎉 **𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐨𝐥𝐮𝐬𝐭𝐮𝐫𝐮𝐥𝐮𝐲𝐨𝐫...**", ephemeral=True)

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
                title="❌ 𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐈𝐩𝐭𝐚𝐥",
                description="```Katılım olmadığı için çekiliş iptal edildi```",
                color=0xFF0000
            )
            await channel.send(embed=embed)
            del self.giveaways[giveaway_id]
            return

        users = [user async for user in reaction.users() if not user.bot]

        if len(users) == 0:
            embed = discord.Embed(
                title="❌ 𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐈𝐩𝐭𝐚𝐥",
                description="```Katılım olmadığı için çekiliş iptal edildi```",
                color=0xFF0000
            )
            embed.set_footer(text=f"Ödül: {prize}")
            await channel.send(embed=embed)
            del self.giveaways[giveaway_id]
            return

        kazananlar = random.sample(users, min(winners_count, len(users)))

        # Kazananlara bildirim
        kazanan_mentions = " ".join([u.mention for u in kazananlar])

        embed = discord.Embed(
            title="🎊 𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐒𝐨𝐧𝐮𝐜𝐥𝐚𝐧𝐝𝐢!",
            description=f"```🎉 Tebrikler kazananlara! 🎉```",
            color=0xFFD700
        )
        embed.add_field(name="🏆 𝐎𝐝𝐮𝐥", value=f"```{prize}```", inline=False)
        embed.add_field(
            name="👑 𝐊𝐚𝐳𝐚𝐧𝐚𝐧𝐥𝐚𝐫",
            value=kazanan_mentions,
            inline=False
        )
        embed.add_field(name="👥 𝐊𝐚𝐭𝐢𝐥𝐢𝐦𝐜𝐢", value=f"```{len(users)} kişi```", inline=True)
        embed.add_field(name="🎯 𝐁𝐚𝐬𝐥𝐚𝐭𝐚𝐧", value=host.mention, inline=True)
        embed.set_footer(text="Çekilişimize katıldığınız için teşekkürler!")
        embed.set_thumbnail(url="https://i.imgur.com/winner_icon.gif")
        embed.timestamp = datetime.utcnow()

        await channel.send(f"🎉 {kazanan_mentions}", embed=embed)

        # Mesajı güncelle
        final_embed = discord.Embed(
            title="🎊 𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐁𝐢𝐭𝐭𝐢!",
            description=f"```{prize}```",
            color=0x808080
        )
        final_embed.add_field(name="👑 𝐊𝐚𝐳𝐚𝐧𝐚𝐧𝐥𝐚𝐫", value=kazanan_mentions, inline=False)
        final_embed.set_footer(text="Çekiliş sona erdi")
        
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
                title="✅ 𝐂𝐞𝐤𝐢𝐥𝐢𝐬𝐞 𝐊𝐚𝐭𝐢𝐥𝐝𝐢𝐧𝐢𝐳!",
                description=f"```{guild.name} sunucusundaki çekilişe başarıyla katıldınız!```",
                color=0x00FF00
            )
            
            data = self.giveaways[payload.message_id]
            embed.add_field(name="🏆 𝐎𝐝𝐮𝐥", value=f"```{data['prize']}```", inline=False)
            embed.add_field(name="⏰ 𝐁𝐢𝐭𝐢𝐬", value=f"<t:{int(data['end'].timestamp())}:R>", inline=True)
            embed.add_field(name="👥 𝐊𝐚𝐳𝐚𝐧𝐚𝐧", value=f"```{data['winners']} kişi```", inline=True)
            embed.add_field(
                name="🍀 𝐈𝐲𝐢 𝐒𝐚𝐧𝐬𝐥𝐚𝐫!",
                value="```Kazanan olmanız için size bol şans diliyoruz!```",
                inline=False
            )
            embed.set_footer(text=f"Sunucu: {guild.name}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.timestamp = datetime.utcnow()

            await member.send(embed=embed)
        except discord.Forbidden:
            # DM kapalı, sessizce geç
            pass
        except Exception as e:
            print(f"DM gönderme hatası: {e}")

    # ========== REROLL ==========
    @app_commands.command(name="reroll", description="Çekilişi yeniden çeker")
    @app_commands.describe(mesaj_id="Çekiliş mesajının ID'si")
    async def reroll(self, interaction: discord.Interaction, mesaj_id: str):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 𝐲𝐞𝐭𝐤𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            mesaj_id = int(mesaj_id)
            msg = await interaction.channel.fetch_message(mesaj_id)
        except:
            embed = discord.Embed(
                description="❌ **𝐌𝐞𝐬𝐚𝐣 𝐛𝐮𝐥𝐮𝐧𝐚𝐦𝐚𝐝𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        
        if not reaction:
            embed = discord.Embed(
                description="❌ **𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐫𝐞𝐚𝐤𝐬𝐢𝐲𝐨𝐧𝐮 𝐛𝐮𝐥𝐮𝐧𝐚𝐦𝐚𝐝𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        users = [user async for user in reaction.users() if not user.bot]

        if len(users) == 0:
            embed = discord.Embed(
                description="❌ **𝐊𝐚𝐭𝐢𝐥𝐢𝐦𝐜𝐢 𝐲𝐨𝐤!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        kazanan = random.choice(users)

        embed = discord.Embed(
            title="🔄 𝐑𝐞𝐫𝐨𝐥𝐥 𝐒𝐨𝐧𝐮𝐜𝐮",
            description=f"```🎉 Yeni kazanan belirlendi! 🎉```",
            color=0xFFD700
        )
        embed.add_field(name="👑 𝐘𝐞𝐧𝐢 𝐊𝐚𝐳𝐚𝐧𝐚𝐧", value=kazanan.mention, inline=False)
        embed.set_thumbnail(url=kazanan.avatar.url if kazanan.avatar else kazanan.default_avatar.url)
        embed.set_footer(text=f"Reroll yapan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message(f"🎊 {kazanan.mention}", embed=embed)

    # ========== GSTOP ==========
    @app_commands.command(name="gstop", description="Devam eden bir çekilişi durdurur")
    @app_commands.describe(mesaj_id="Çekiliş mesajının ID'si")
    async def gstop(self, interaction: discord.Interaction, mesaj_id: str):
        if not interaction.user.guild_permissions.manage_guild:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐤𝐨𝐦𝐮𝐭𝐮 𝐤𝐮𝐥𝐥𝐚𝐧𝐦𝐚𝐤 𝐢𝐜𝐢𝐧 𝐲𝐞𝐭𝐤𝐢 𝐠𝐞𝐫𝐞𝐤𝐥𝐢!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            mesaj_id = int(mesaj_id)
        except:
            embed = discord.Embed(
                description="❌ **𝐆𝐞𝐜𝐞𝐫𝐬𝐢𝐳 𝐦𝐞𝐬𝐚𝐣 𝐈𝐃!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if mesaj_id not in self.giveaways:
            embed = discord.Embed(
                description="❌ **𝐁𝐮 𝐈𝐃 𝐢𝐥𝐞 𝐚𝐤𝐭𝐢𝐟 𝐜𝐞𝐤𝐢𝐥𝐢𝐬 𝐲𝐨𝐤!**",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        data = self.giveaways[mesaj_id]
        del self.giveaways[mesaj_id]

        embed = discord.Embed(
            title="🛑 𝐂𝐞𝐤𝐢𝐥𝐢𝐬 𝐃𝐮𝐫𝐝𝐮𝐫𝐮𝐥𝐝𝐮",
            description=f"```{data['prize']} ödüllü çekiliş durduruldu```",
            color=0xFF0000
        )
        embed.set_footer(text=f"Durduran: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.utcnow()

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
