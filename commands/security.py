import discord
from discord.ext import commands
from discord import app_commands
import re
from datetime import datetime


class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam = {}
        self.enabled_filters = {
            "antilink": True,
            "antikufur": True,
            "antispam": True,
            "reklam": True
        }

        self.kufur_listesi = [
            "amk", "aq", "orospu", "yarrak", "piç", "göt", "sik", "amına", "salak"
        ]

        self.reklam_pattern = r"(discord\.gg|invite|boost|nitro|takipçi|instagram\.com)"

    @app_commands.command(name="filter", description="Filtreleri açıp kapatır")
    async def filter(self, interaction: discord.Interaction, filtre: str, durum: str):
        filtre = filtre.lower()
        if filtre not in self.enabled_filters:
            return await interaction.response.send_message("❌ Böyle bir filtre yok!", ephemeral=True)

        if durum not in ["aç", "kapat"]:
            return await interaction.response.send_message("❌ 'aç' veya 'kapat' yazmalısın.", ephemeral=True)

        self.enabled_filters[filtre] = (durum == "aç")

        await interaction.response.send_message(
            f"🔧 `{filtre}` filtresi başarıyla **{durum}ıldı**."
        )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        if self.enabled_filters["antilink"]:
            if "http://" in msg.content or "https://" in msg.content:
                await msg.delete()
                return await msg.channel.send(f"❌ {msg.author.mention} Link paylaşmak yasak!", delete_after=5)

        if self.enabled_filters["antikufur"]:
            if any(k in msg.content.lower() for k in self.kufur_listesi):
                await msg.delete()
                return await msg.channel.send(f"❌ {msg.author.mention} Küfür yasak!", delete_after=5)

        if self.enabled_filters["reklam"]:
            if re.search(self.reklam_pattern, msg.content.lower()):
                await msg.delete()
                return await msg.channel.send(f"📣 {msg.author.mention} Reklam yasak!", delete_after=5)

        if self.enabled_filters["antispam"]:
            user_id = msg.author.id
            if user_id not in self.antispam:
                self.antispam[user_id] = {"count": 1}
            else:
                self.antispam[user_id]["count"] += 1

            if self.antispam[user_id]["count"] > 5:
                await msg.delete()
                return await msg.channel.send(
                    f"⛔ {msg.author.mention} Spam yapmayı bırak!", delete_after=5
                )

    @app_commands.command(name="filterstatus", description="Filtrelerin açık/kapalı durumunu gösterir")
    async def filterstatus(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡 Filtre Durumu",
            color=0x5865F2,
            timestamp=datetime.now()
        )

        for filtre, acik in self.enabled_filters.items():
            durum = "🟢 Açık" if acik else "🔴 Kapalı"
            embed.add_field(name=filtre, value=durum, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Security(bot))
