import discord
from discord.ext import commands
from datetime import datetime, timezone


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Sunucuya yeni katılan üyeleri karşılar"""
        
        # DM ile karşılama mesajı
        try:
            embed = discord.Embed(
                title=f"🎉 𝐇𝐨𝐬 𝐆𝐞𝐥𝐝𝐢𝐧 {member.name}!",
                description=f"```{member.guild.name} sunucusuna hoş geldin!```",
                color=0xFF69B4
            )
            
            # Sunucu bilgileri
            embed.add_field(
                name="🏰 𝐒𝐮𝐧𝐮𝐜𝐮",
                value=f"```{member.guild.name}```",
                inline=True
            )
            embed.add_field(
                name="👥 𝐔𝐲𝐞 𝐒𝐚𝐲𝐢𝐬𝐢",
                value=f"```{member.guild.member_count} üye```",
                inline=True
            )
            embed.add_field(
                name="📅 𝐊𝐚𝐭𝐢𝐥𝐦𝐚 𝐓𝐚𝐫𝐢𝐡𝐢",
                value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:F>",
                inline=False
            )
            
            # Hoş geldin mesajı
            embed.add_field(
                name="💝 𝐌𝐞𝐬𝐚𝐣𝐢𝐦𝐢𝐳",
                value="```Aramıza katıldığın için çok mutluyuz! Sunucumuzda iyi vakit geçirmeni dileriz.```",
                inline=False
            )
            
            # Davet linki
            embed.add_field(
                name="🔗 𝐀𝐫𝐤𝐚𝐝𝐚𝐬𝐥𝐚𝐫𝐢𝐧𝐢 𝐃𝐚𝐯𝐞𝐭 𝐄𝐭!",
                value="```Arkadaşlarını da davet et, beraber büyüyelim! Ne kadar çok olursak o kadar eğlenceli olacak! 🚀```",
                inline=False
            )
            
            # Kurallar
            embed.add_field(
                name="📜 𝐊𝐮𝐫𝐚𝐥𝐥𝐚𝐫",
                value="```Sunucu kurallarını okumayı unutma! Herkesin keyifli vakit geçirmesi için kurallara uymamız önemli.```",
                inline=False
            )
            
            # Görsel
            if member.guild.icon:
                embed.set_thumbnail(url=member.guild.icon.url)
            
            embed.set_image(url="https://media1.tenor.com/m/2H9_ncHdTqUAAAAC/welcome.gif")
            
            embed.set_footer(
                text=f"🌟 {member.guild.name} Ekibi",
                icon_url=member.guild.icon.url if member.guild.icon else None
            )
            embed.timestamp = datetime.now(timezone.utc)
            
            await member.send(embed=embed)
            
        except discord.Forbidden:
            # DM kapalı, hata verme
            print(f"⚠️ {member.name} kullanıcısına DM gönderilemedi (DM kapalı)")
        except Exception as e:
            # Diğer hatalar
            print(f"❌ Karşılama mesajı hatası: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Sunucudan ayrılan üyeleri loglar"""
        print(f"👋 {member.name} sunucudan ayrıldı. ({member.guild.name})")


async def setup(bot):
    await bot.add_cog(Welcome(bot))