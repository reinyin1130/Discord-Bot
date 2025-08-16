import discord
from discord import app_commands
from discord.ext import commands

from datetime import timedelta

from core.classes import Cog


class Admin(Cog):
    """
    管理命令
    """

    @app_commands.command(name="clear", description="清除指定數量的訊息")
    @app_commands.describe(amount="要清除的訊息數量 (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 10):
        # 限制清除數量
        amount = min(max(amount, 1), 100)

        # 清除訊息
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)

        # 發送結果
        await interaction.followup.send(
            f"已清除 {len(deleted)} 條訊息！", ephemeral=True
        )

    @app_commands.command(name="mute", description="禁言指定成員")
    @app_commands.describe(
        member="要禁言的成員", duration="禁言時長 (分鐘)", reason="禁言原因"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: int = 10,
        reason: str = "違反伺服器規則",
    ):
        # 限制禁言時間
        duration = min(max(duration, 1), 1440)  # 1分鐘到24小時

        # 執行禁言
        await member.timeout(timedelta(minutes=duration), reason=reason)

        embed = discord.Embed(title="⛔ 成員已被禁言", color=discord.Color.red())
        embed.add_field(name="成員", value=member.mention, inline=True)
        embed.add_field(name="時長", value=f"{duration} 分鐘", inline=True)
        embed.add_field(name="原因", value=reason, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="解除成員禁言")
    @app_commands.describe(member="要解除禁言的成員")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        # 解除禁言
        await member.timeout(None)

        embed = discord.Embed(
            title="✅ 成員禁言已解除",
            description=f"{member.mention} 的禁言已被解除",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="踢出成員")
    @app_commands.describe(member="要踢出的成員", reason="原因")
    @app_commands.default_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "違反伺服器規則",
    ):
        # 踢出成員
        await member.kick(reason=reason)

        embed = discord.Embed(title="👢 成員已被踢出", color=discord.Color.orange())
        embed.add_field(name="成員", value=member.mention, inline=True)
        embed.add_field(name="原因", value=reason, inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
