import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Kullanıcı bilgilerini gösterir")
    @app_commands.describe(kullanici="Bilgilerini görmek istediğiniz kullanıcı", gizli="Sadece siz görecek misiniz?")
    async def userinfo(self, interaction: discord.Interaction, kullanici: discord.Member = None, gizli: bool = False):
        kullanici = kullanici or interaction.user
        now = datetime.now(timezone.utc)
        hesap_yasi = (now - kullanici.created_at).days
        sunucu_yasi = (now - kullanici.joined_at).days if kullanici.joined_at else 0

        durum_emoji = {
            discord.Status.online: "🟢 Çevrimiçi",
            discord.Status.idle: "🟡 Boşta",
            discord.Status.dnd: "🔴 Rahatsız Etmeyin",
            discord.Status.offline: "⚫ Çevrimdışı"
        }

        banner_url = None
        try:
            user = await self.bot.fetch_user(kullanici.id)
            if user.banner:
                banner_url = user.banner.url
        except:
            pass

        voice_channel = kullanici.voice.channel if kullanici.voice else None
        activity = None
        if kullanici.activities:
            for act in kullanici.activities:
                if isinstance(act, discord.Game):
                    activity = f"🎮 {act.name}"
                elif isinstance(act, discord.Streaming):
                    activity = f"📺 {act.name}"
                elif isinstance(act, discord.Spotify):
                    activity = f"🎵 {act.title} - {act.artist}"
                elif isinstance(act, discord.CustomActivity):
                    activity = f"💭 {act.name}"

        embed = discord.Embed(
            title="═════════════════════════",
            description=f"# 👤 {kullanici.name}",
            color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2
        )
        
        embed.add_field(
            name="📌 𝗞𝘂𝗹𝗹𝗮𝗻𝗶𝗰𝗶 𝗕𝗶𝗹𝗴𝗶𝗹𝗲𝗿𝗶",
            value=f"```ansi\n"
                  f"──────────────────────\n"
                  f"📛 Takma Adı: {kullanici.display_name}\n"
                  f"🆔 Kullanıcı ID: {kullanici.id}\n"
                  f"🟢 Durum: {durum_emoji.get(kullanici.status, '⚫ Bilinmiyor')}\n"
                  f"🎮 Oynadığı Oyun: {activity if activity else 'Yok'}\n"
                  f"📅 Discord'a Katılım: {kullanici.created_at.strftime('%d/%m/%Y')}\n"
                  f"```",
            inline=False
        )
        
        embed.add_field(
            name="🏰 𝗦𝘂𝗻𝘂𝗰𝘂 𝗜̇𝘀𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗸𝗹𝗲𝗿𝗶",
            value=f"```ansi\n"
                  f"──────────────────────\n"
                  f"📥 Sunucuya Katılım: {kullanici.joined_at.strftime('%d/%m/%Y') if kullanici.joined_at else 'Bilinmiyor'}\n"
                  f"📅 Giriş Tarihi: {sunucu_yasi} gün önce\n"
                  f"🚀 Boost Sayısı: {kullanici.premium_since.strftime('%d/%m/%Y') if kullanici.premium_since else 'Yok'}\n"
                  f"🔊 Bulunduğu Ses Kanalı: {voice_channel.name if voice_channel else 'Yok'}\n"
                  f"🛡 Yetki: {'Yönetici' if kullanici.guild_permissions.administrator else 'Üye'}\n"
                  f"```",
            inline=False
        )

        if len(kullanici.roles) > 1:
            roles = [role.mention for role in sorted(kullanici.roles[1:], key=lambda r: r.position, reverse=True)[:10]]
            roles_text = ", ".join(roles)
            if len(kullanici.roles) > 11:
                roles_text += f" +{len(kullanici.roles) - 11} daha"
            embed.add_field(
                name=f"🎭 𝗥𝗼𝗹𝗹𝗲𝗿 ({len(kullanici.roles) - 1})",
                value=roles_text,
                inline=False
            )

        if banner_url:
            embed.add_field(
                name="🖼️ 𝗕𝗮𝗻𝗻𝗲𝗿",
                value=f"[Görüntüle]({banner_url})",
                inline=True
            )
            embed.set_image(url=banner_url)

        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    @app_commands.command(name="serverinfo", description="Sunucu bilgilerini gösterir")
    @app_commands.describe(gizli="Sadece siz görecek misiniz?")
    async def serverinfo(self, interaction: discord.Interaction, gizli: bool = False):
        guild = interaction.guild

        online = sum(1 for m in guild.members if m.status == discord.Status.online)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
        bot_count = sum(1 for m in guild.members if m.bot)

        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            description="═════════════════════════",
            color=0x5865F2
        )
        
        embed.add_field(
            name="📊 𝗚𝗲𝗻𝗲𝗹 𝗕𝗶𝗹𝗴𝗶𝗹𝗲𝗿",
            value=f"```ansi\n"
                  f"🆔 Sunucu ID: {guild.id}\n"
                  f"👑 Sunucu Sahibi: {guild.owner.name}\n"
                  f"📅 Oluşturulma: {guild.created_at.strftime('%d/%m/%Y')} ({(datetime.now(timezone.utc) - guild.created_at).days} gün)\n"
                  f"💎 Boost Seviye: {guild.premium_tier}\n"
                  f"🚀 Boost Sayısı: {guild.premium_subscription_count}\n"
                  f"```",
            inline=False
        )

        embed.add_field(
            name=f"👥 𝗨̈𝘆𝗲𝗹𝗲𝗿 ({guild.member_count})",
            value=f"```ansi\n"
                  f"🟢 Çevrimiçi: {online}\n"
                  f"🟡 Boşta: {idle}\n"
                  f"🔴 Rahatsız: {dnd}\n"
                  f"⚫ Çevrim Dışı: {offline}\n"
                  f"🤖 Bot: {bot_count}\n"
                  f"```",
            inline=True
        )

        embed.add_field(
            name=f"📁 𝗞𝗮𝗻𝗮𝗹𝗹𝗮𝗿 ({len(guild.channels)})",
            value=f"```ansi\n"
                  f"💬 Metin: {len(guild.text_channels)}\n"
                  f"🔊 Sesli: {len(guild.voice_channels)}\n"
                  f"📂 Kategori: {len(guild.categories)}\n"
                  f"📢 Duyuru: {len([c for c in guild.channels if isinstance(c, discord.TextChannel) and c.is_news()])}\n"
                  f"🧵 Forum: {len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])}\n"
                  f"```",
            inline=True
        )
        
        embed.add_field(
            name=f"🎭 𝗗𝗶𝗴̆𝗲𝗿",
            value=f"```ansi\n"
                  f"🎭 Roller: {len(guild.roles)}\n"
                  f"😀 Emojiler: {len(guild.emojis)}\n"
                  f"🎨 Stickerlar: {len(guild.stickers)}\n"
                  f"```",
            inline=False
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    @app_commands.command(name="ping", description="Bot gecikmesini gösterir")
    @app_commands.describe(gizli="Sadece siz görecek misiniz?")
    async def ping(self, interaction: discord.Interaction, gizli: bool = False):
        latency = round(self.bot.latency * 1000)
        
        if latency < 100:
            color = 0x00FF00
            emoji = "🟢"
            status = "Mükemmel"
        elif latency < 200:
            color = 0xFFFF00
            emoji = "🟡"
            status = "İyi"
        else:
            color = 0xFF0000
            emoji = "🔴"
            status = "Yavaş"
        
        embed = discord.Embed(
            title="🏓 𝗣𝗼𝗻𝗴!",
            color=color
        )
        embed.add_field(
            name="⚡ 𝗚𝗲𝗰𝗶𝗸𝗺𝗲",
            value=f"```{latency} ms```",
            inline=True
        )
        embed.add_field(
            name=f"{emoji} 𝗗𝘂𝗿𝘂𝗺",
            value=f"```{status}```",
            inline=True
        )
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    @app_commands.command(name="avatar", description="Kullanıcının avatarını gösterir")
    @app_commands.describe(kullanici="Avatarını görmek istediğiniz kullanıcı", gizli="Sadece siz görecek misiniz?")
    async def avatar(self, interaction: discord.Interaction, kullanici: discord.Member = None, gizli: bool = False):
        kullanici = kullanici or interaction.user

        embed = discord.Embed(
            title=f"🖼️ {kullanici.name}",
            description="═════════════════════════",
            color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2
        )
        
        avatar_url = kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url
        
        embed.set_image(url=avatar_url)
        embed.add_field(
            name="🔗 𝗟𝗶𝗻𝗸",
            value=f"[Avatar URL]({avatar_url})",
            inline=False
        )
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed, ephemeral=gizli)

    @app_commands.command(name="banner", description="Kullanıcının banner'ını gösterir")
    @app_commands.describe(kullanici="Banner'ını görmek istediğiniz kullanıcı", gizli="Sadece siz görecek misiniz?")
    async def banner(self, interaction: discord.Interaction, kullanici: discord.Member = None, gizli: bool = False):
        kullanici = kullanici or interaction.user
        
        try:
            user = await self.bot.fetch_user(kullanici.id)
            if user.banner:
                embed = discord.Embed(
                    title=f"🎨 {kullanici.name}",
                    description="═════════════════════════",
                    color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2
                )
                embed.set_image(url=user.banner.url)
                embed.add_field(
                    name="🔗 𝗟𝗶𝗻𝗸",
                    value=f"[Banner URL]({user.banner.url})",
                    inline=False
                )
                embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                embed.timestamp = datetime.now(timezone.utc)
                
                return await interaction.response.send_message(embed=embed, ephemeral=gizli)
            else:
                embed = discord.Embed(
                    description=f"❌ **{kullanici.mention} kullanıcısında banner yok!**",
                    color=0xFF0000
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **Hata:** ```{str(e)}```",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Info(bot))
