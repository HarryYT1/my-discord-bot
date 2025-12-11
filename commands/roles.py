import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========== ROLLER (SAYFALI) ==========
    @app_commands.command(name="roller", description="Sunucudaki rolleri sayfa sayfa gösterir")
    async def roller(self, interaction: discord.Interaction):
        guild = interaction.guild
        roles = sorted(guild.roles[1:], key=lambda r: r.position, reverse=True)

        class RolePaginationView(discord.ui.View):
            def __init__(self, roles_list, page_size=15):
                super().__init__(timeout=180)
                self.roles_list = roles_list
                self.page_size = page_size
                self.current_page = 0
                self.total_pages = (len(roles_list) + page_size - 1) // page_size
                self.filter_type = "all"

            def update_buttons(self):
                self.children[0].label = f"Sayfa {self.current_page + 1}/{self.total_pages}"

            @discord.ui.button(label="Sayfa 1/1", style=discord.ButtonStyle.grey, disabled=True)
            async def page_indicator(self, interaction: discord.Interaction, button): pass

            @discord.ui.button(label="◀️", style=discord.ButtonStyle.blurple)
            async def prev_page(self, interaction: discord.Interaction, button):
                if self.current_page > 0:
                    self.current_page -= 1
                    await self.update_message(interaction)

            @discord.ui.button(label="▶️", style=discord.Button.ButtonStyle.blurple)
            async def next_page(self, interaction: discord.Interaction, button):
                if self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    await self.update_message(interaction)

            @discord.ui.button(label="🗑️", style=discord.ButtonStyle.red)
            async def delete_msg(self, interaction: discord.Interaction, button):
                await interaction.message.delete()

            async def update_message(self, interaction: discord.Interaction):
                start = self.current_page * self.page_size
                end = min(start + self.page_size, len(self.roles_list))
                page_roles = self.roles_list[start:end]

                embed = discord.Embed(
                    title=f"📋 Roller [{start+1}-{end}]",
                    color=0x5865F2,
                    timestamp=datetime.now(timezone.utc)
                )

                desc = "\n".join(f"{role.mention} (`{len(role.members)}`)" for role in page_roles)
                embed.description = desc or "`Rol bulunamadı.`"
                self.update_buttons()
                await interaction.response.edit_message(embed=embed, view=self)

        view = RolePaginationView(roles)
        embed = discord.Embed(
            title=f"📋 Roller [1-{min(15, len(roles))}]",
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc)
        )

        embed.description = "\n".join(f"{role.mention} (`{len(role.members)}`)" for role in roles[:15])
        await interaction.response.send_message(embed=embed, view=view)

    # ========== ROL VER ==========
    @app_commands.command(name="rolver", description="Bir kullanıcıya rol verir")
    async def rolver(self, interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)

        try:
            await kullanici.add_roles(rol)
            embed = discord.Embed(color=rol.color)
            embed.set_author(name="🎭 Rol Verildi")
            embed.add_field(name="Kullanıcı", value=kullanici.mention)
            embed.add_field(name="Rol", value=rol.mention)
            embed.timestamp = datetime.now(timezone.utc)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    # ========== ROL AL ==========
    @app_commands.command(name="rolal", description="Bir kullanıcıdan rol alır")
    async def rolal(self, interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)

        try:
            await kullanici.remove_roles(rol)
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="❌ Rol Alındı")
            embed.add_field(name="Kullanıcı", value=kullanici.mention)
            embed.add_field(name="Rol", value=rol.mention)
            embed.timestamp = datetime.now(timezone.utc)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    # ========== ROLE INFO ==========
    @app_commands.command(name="roleinfo", description="Rol hakkında bilgi verir")
    async def roleinfo(self, interaction: discord.Interaction, rol: discord.Role):
        embed = discord.Embed(color=rol.color)
        embed.set_author(name=f"{rol.name} Rol Bilgileri")
        embed.add_field(name="ID", value=rol.id)
        embed.add_field(name="Üye Sayısı", value=len(rol.members))
        embed.add_field(name="Sıralama", value=rol.position)
        embed.add_field(
            name="Oluşturulma",
            value=f"{rol.created_at.strftime('%d %B %Y')} ({(datetime.now(timezone.utc) - rol.created_at).days} gün önce)"
        )
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Roles(bot))
