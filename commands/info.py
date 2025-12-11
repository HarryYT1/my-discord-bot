import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== USERINFO ==========
    @app_commands.command(name="userinfo", description="Kullanıcı bilgilerini gösterir")
    @app_commands.describe(kullanici="Bilgilerini görmek istediğiniz kullanıcı")
    async def userinfo(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        now = datetime.now(timezone.utc)
        hesap_yasi = (now - kullanici.created_at).days
        sunucu_yasi = (now - kullanici.joined_at).days if kullanici.joined_at else 0

        durum_emoji = {
            discord.Status.online: "🟢 𝐂𝐞𝐯𝐫𝐢𝐦𝐢𝐜𝐢",
            discord.Status.idle: "🟡 𝐁𝐨𝐬𝐭𝐚",
            discord.Status.dnd: "🔴 𝐑𝐚𝐡𝐚𝐭𝐬𝐢𝐳 𝐄𝐭𝐦𝐞𝐲𝐢𝐧",
            discord.Status.offline: "⚫ 𝐂𝐞𝐯𝐫𝐢𝐦𝐝𝐢𝐬𝐢"
        }

        # Banner al
        banner_url = None
        try:
            user = await self.bot.fetch_user(kullanici.id)
            if user.banner:
                banner_url = user.banner.url
        except:
            pass

        embed = discord.Embed(
            title=f"👤 {kullanici.name} 𝐁𝐢𝐥𝐠𝐢𝐥𝐞𝐫𝐢",
            color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2
        )
        
        # Genel Bilgiler
        embed.add_field(
            name="📛 𝐓𝐚𝐤𝐦𝐚 𝐀𝐝",
            value=f"```{kullanici.display_name}```",
            inline=True
        )
        embed.add_field(
            name="🆔 𝐊𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢 𝐈𝐃",
            value=f"```{kullanici.id}```",
            inline=True
        )
        embed.add_field(
            name="🌐 𝐃𝐮𝐫𝐮𝐦",
            value=durum_emoji.get(kullanici.status, "⚫ 𝐁𝐢𝐥𝐢𝐧𝐦𝐢𝐲𝐨𝐫"),
            inline=True
        )

        # Tarihler
        embed.add_field(
            name="📅 𝐒𝐮𝐧𝐮𝐜𝐮𝐲𝐚 𝐊𝐚𝐭𝐢𝐥𝐦𝐚",
            value=f"<t:{int(kullanici.joined_at.timestamp())}:D>\n```{sunucu_yasi} gün önce```",
            inline=True
        )
        embed.add_field(
            name="🎂 𝐇𝐞𝐬𝐚𝐩 𝐎𝐥𝐮𝐬𝐭𝐮𝐫𝐦𝐚",
            value=f"<t:{int(kullanici.created_at.timestamp())}:D>\n```{hesap_yasi} gün önce```",
            inline=True
        )
        
        # Roller
        if len(kullanici.roles) > 1:
            roles = [role.mention for role in kullanici.roles[1:][:10]]  # İlk 10 rol
            roles_text = ", ".join(roles)
            if len(kullanici.roles) > 11:
                roles_text += f" +{len(kullanici.roles) - 11} daha"
            embed.add_field(
                name=f"🎭 𝐑𝐨𝐥𝐥𝐞𝐫 ({len(kullanici.roles) - 1})",
                value=roles_text,
                inline=False
            )

        # Banner
        if banner_url:
            embed.add_field(
                name="🖼️ 𝐁𝐚𝐧𝐧𝐞𝐫",
                value=f"[Görüntüle]({banner_url})",
                inline=True
            )
            embed.set_image(url=banner_url)

        embed.set_thumbnail(url=kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url)
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== SERVERINFO ==========
    @app_commands.command(name="serverinfo", description="Sunucu bilgilerini gösterir")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        online = sum(1 for m in guild.members if m.status == discord.Status.online)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
        bot_count = sum(1 for m in guild.members if m.bot)

        embed = discord.Embed(
            title=f"🏰 {guild.name} 𝐒𝐮𝐧𝐮𝐜𝐮 𝐁𝐢𝐥𝐠𝐢𝐥𝐞𝐫𝐢",
            color=0x5865F2
        )
        
        embed.add_field(
            name="🆔 𝐒𝐮𝐧𝐮𝐜𝐮 𝐈𝐃",
            value=f"```{guild.id}```",
            inline=True
        )
        embed.add_field(
            name="👑 𝐒𝐮𝐧𝐮𝐜𝐮 𝐒𝐚𝐡𝐢𝐛𝐢",
            value=f"{guild.owner.mention}\n```{guild.owner.name}```",
            inline=True
        )
        embed.add_field(
            name="📅 𝐎𝐥𝐮𝐬𝐭𝐮𝐫𝐮𝐥𝐦𝐚",
            value=f"<t:{int(guild.created_at.timestamp())}:D>\n```{(datetime.now(timezone.utc) - guild.created_at).days} gün```",
            inline=True
        )

        embed.add_field(
            name=f"👥 𝐔𝐲𝐞𝐥𝐞𝐫 ({guild.member_count})",
            value=f"```🟢 Çevrimiçi: {online}\n🟡 Boşta: {idle}\n🔴 Rahatsız: {dnd}\n⚫ Çevrim Dışı: {offline}\n🤖 Bot: {bot_count}```",
            inline=True
        )

        embed.add_field(
            name=f"📝 𝐊𝐚𝐧𝐚𝐥𝐥𝐚𝐫 ({len(guild.channels)})",
            value=f"```💬 Metin: {len(guild.text_channels)}\n🔊 Sesli: {len(guild.voice_channels)}\n📂 Kategori: {len(guild.categories)}```",
            inline=True
        )
        
        embed.add_field(
            name=f"🎭 𝐑𝐨𝐥𝐥𝐞𝐫",
            value=f"```{len(guild.roles)} rol```",
            inline=True
        )
        
        # Boost bilgisi
        embed.add_field(
            name="💎 𝐁𝐨𝐨𝐬𝐭",
            value=f"```Seviye: {guild.premium_tier}\nBoost: {guild.premium_subscription_count}```",
            inline=True
        )
        
        # Emoji sayısı
        embed.add_field(
            name="😀 𝐄𝐦𝐨𝐣𝐢𝐥𝐞𝐫",
            value=f"```{len(guild.emojis)} emoji```",
            inline=True
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== PING ==========
    @app_commands.command(name="ping", description="Bot gecikmesini gösterir")
    async def ping(self, interaction: discord.Interaction):
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
            title="🏓 𝐏𝐨𝐧𝐠!",
            color=color
        )
        embed.add_field(
            name="⚡ 𝐆𝐞𝐜𝐢𝐤𝐦𝐞",
            value=f"```{latency} ms```",
            inline=True
        )
        embed.add_field(
            name=f"{emoji} 𝐃𝐮𝐫𝐮𝐦",
            value=f"```{status}```",
            inline=True
        )
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== AVATAR ==========
    @app_commands.command(name="avatar", description="Kullanıcının avatarını gösterir")
    @app_commands.describe(kullanici="Avatarını görmek istediğiniz kullanıcı")
    async def avatar(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user

        embed = discord.Embed(
            title=f"🖼️ {kullanici.name} 𝐀𝐯𝐚𝐭𝐚𝐫𝐢",
            color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2
        )
        
        avatar_url = kullanici.avatar.url if kullanici.avatar else kullanici.default_avatar.url
        
        embed.set_image(url=avatar_url)
        embed.add_field(
            name="🔗 𝐋𝐢𝐧𝐤",
            value=f"[Avatar URL]({avatar_url})",
            inline=False
        )
        embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = datetime.now(timezone.utc)
        
        await interaction.response.send_message(embed=embed)

    # ========== BANNER ==========
    @app_commands.command(name="banner", description="Kullanıcının banner'ını gösterir")
    @app_commands.describe(kullanici="Banner'ını görmek istediğiniz kullanıcı")
    async def banner(self, interaction: discord.Interaction, kullanici: discord.Member = None):
        kullanici = kullanici or interaction.user
        
        try:
            user = await self.bot.fetch_user(kullanici.id)
            if user.banner:
                embed = discord.Embed(
                    title=f"🎨 {kullanici.name} 𝐁𝐚𝐧𝐧𝐞𝐫𝐢",
                    color=kullanici.color if kullanici.color != discord.Color.default() else 0x5865F2
                )
                embed.set_image(url=user.banner.url)
                embed.add_field(
                    name="🔗 𝐋𝐢𝐧𝐤",
                    value=f"[Banner URL]({user.banner.url})",
                    inline=False
                )
                embed.set_footer(text=f"Sorgulayan: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                embed.timestamp = datetime.now(timezone.utc)
                
                return await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(
                    description=f"❌ **{kullanici.mention} 𝐤𝐮𝐥𝐥𝐚𝐧𝐢𝐜𝐢𝐬𝐢𝐧𝐝𝐚 𝐛𝐚𝐧𝐧𝐞𝐫 𝐲𝐨𝐤!**",
                    color=0xFF0000
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ **𝐇𝐚𝐭𝐚:** ```{str(e)}```",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Info(bot))
