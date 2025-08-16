import discord
from discord import app_commands
from discord.ext import commands

import random

from core.classes import Cog
from utils.json_handle import load_json, save_json


class Dice(Cog):
    # 擲骰子遊戲
    @app_commands.command(name="dice", description="擲骰子遊戲 (花費 5 金幣)")
    async def dice(self, interaction: discord.Interaction):
        # 加載用戶數據
        user_data = load_json("user_data.json")

        user_id = str(interaction.user.id)

        if user_id not in user_data or user_data[user_id]["coins"] < 5:
            await interaction.response.send_message(
                "金幣不足或沒有帳戶！最少需要 5 金幣才能玩。", ephemeral=True
            )
            return

        # 扣除金幣
        user_data[user_id]["coins"] -= 5
        save_json("user_data.json", user_data)

        # 生成骰子結果
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2

        # 計算獎勵
        win_amount = 0
        if total == 7:
            win_amount = 20
            win_text = "幸運7！"
        elif total >= 10:
            win_amount = 10
            win_text = "高點數！"
        elif total <= 4:
            win_amount = 10
            win_text = "低點數！"
        else:
            win_text = "普通點數"

        # 發送結果
        embed = discord.Embed(
            title="🎲 擲骰子遊戲",
            description=f"你擲出了：**{dice1}** 和 **{dice2}** (總和: {total})",
            color=discord.Color.blue(),
        )
        embed.add_field(name="結果", value=win_text)

        if win_amount > 0:
            user_data[user_id]["coins"] += win_amount
            save_json("user_data.json", user_data)
            embed.add_field(name="獎金", value=f"🪙 +{win_amount} 金幣")

        embed.set_footer(text=f"餘額: {user_data[user_id]['coins']} 金幣")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Dice(bot))
