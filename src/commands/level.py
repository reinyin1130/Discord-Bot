import discord
from discord import app_commands
from discord.ext import commands

from datetime import datetime

from core.classes import Cog
from utils.json_handle import load_json
from config.const import LEVEL_MULTIPLIER


class Level(Cog):
    """
    等級系統命令
    """

    @app_commands.command(name="level", description="查看你的等級和經驗值")
    async def level(self, interaction: discord.Interaction):
        user_data = load_json("user_data.json")

        user_id = str(interaction.user.id)

        if user_id not in user_data:
            await interaction.response.send_message(
                "你還沒有任何等級數據！開始聊天來獲得經驗值吧！", ephemeral=True
            )
            return

        data = user_data[user_id]
        exp_needed = data["level"] * LEVEL_MULTIPLIER
        progress = (data["exp"] / exp_needed) * 100

        embed = discord.Embed(
            title=f"{interaction.user.display_name} 的等級", color=discord.Color.blue()
        )

        # 添加稱號和背景
        if data.get("title"):
            embed.title = f"{data['title']} {embed.title}"
        if data.get("background"):
            embed.description = f"個人背景: {data['background']}"

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="等級", value=f"**{data['level']}**", inline=True)
        embed.add_field(
            name="經驗值", value=f"{int(data['exp'])}/{exp_needed}", inline=True
        )
        embed.add_field(name="金幣", value=f"🪙 {data['coins']}", inline=True)
        embed.add_field(
            name="進度",
            value=f"`{'█' * int(progress/10)}{'░' * (10 - int(progress/10))}` {progress:.1f}%",
            inline=False,
        )

        # 顯示加成效果
        boosts = []
        if "double_xp" in data.get("boosts", {}):
            if datetime.now().timestamp() < data["boosts"]["double_xp"]:
                time_left = int(
                    (data["boosts"]["double_xp"] - datetime.now().timestamp()) / 60
                )
                boosts.append(f"雙倍經驗 ({time_left}分鐘)")

        if boosts:
            embed.add_field(name="加成效果", value="\n".join(boosts), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="查看伺服器等級排行榜")
    async def leaderboard(self, interaction: discord.Interaction):
        user_data = load_json("user_data.json")

        # 獲取伺服器成員ID
        member_ids = [str(member.id) for member in interaction.guild.members]

        # 篩選出在伺服器中的用戶數據
        server_users = {
            uid: data for uid, data in user_data.items() if uid in member_ids
        }

        if not server_users:
            await interaction.response.send_message(
                "還沒有任何等級數據！", ephemeral=True
            )
            return

        # 排序取前10名
        top_users = sorted(
            server_users.items(), key=lambda x: x[1]["level"], reverse=True
        )[:10]

        embed = discord.Embed(
            title="🏆 等級排行榜",
            description=f"**{interaction.guild.name}** 的頂尖玩家",
            color=discord.Color.gold(),
        )

        for i, (user_id, data) in enumerate(top_users):
            member = interaction.guild.get_member(int(user_id))
            if member:
                title = data.get("title", "")
                embed.add_field(
                    name=(
                        f"{i+1}. {title}{member.display_name}"
                        if title
                        else f"{i+1}. {member.display_name}"
                    ),
                    value=f"等級: {data['level']} | 經驗: {int(data['exp'])} | 金幣: {data['coins']}",
                    inline=False,
                )

        embed.set_footer(text=f"總共 {len(server_users)} 位用戶參與")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Level(bot))
