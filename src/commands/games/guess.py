import discord
from discord import app_commands
from discord.ext import commands

import random

from core.classes import Cog
from utils.json_handle import load_json, save_json


class Guess(Cog):
    # 猜數字遊戲
    @app_commands.command(name="guess", description="猜數字遊戲 (1-100)")
    async def guess(self, interaction: discord.Interaction):
        number = random.randint(1, 100)

        embed = discord.Embed(
            title="🎮 猜數字遊戲",
            description="我已經想好了一個 1-100 之間的數字！你有 5 次機會猜中它！",
            color=discord.Color.green(),
        )
        embed.set_footer(text="輸入 /g [數字] 來猜測")

        # 存儲遊戲數據
        self.bot.games = getattr(self.bot, "games", {})
        self.bot.games[interaction.user.id] = {
            "number": number,
            "attempts": 5,
            "won": False,
        }

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="g", description="猜數字")
    @app_commands.describe(number="你猜的數字 (1-100)")
    async def guess_number(self, interaction: discord.Interaction, number: int):
        user_id = interaction.user.id
        games = getattr(self.bot, "games", {})

        if user_id not in games:
            await interaction.response.send_message(
                "你還沒有開始遊戲！使用 /guess 開始新遊戲。", ephemeral=True
            )
            return

        game = games[user_id]

        if game["won"] or game["attempts"] <= 0:
            await interaction.response.send_message(
                "遊戲已經結束！使用 /guess 開始新遊戲。", ephemeral=True
            )
            return

        # 減少嘗試次數
        game["attempts"] -= 1

        # 檢查猜測
        if number == game["number"]:
            game["won"] = True
            reward = random.randint(20, 50)

            # 更新用戶金幣
            user_data = load_json("user_data.json")

            user_id_str = str(user_id)
            if user_id_str in user_data:
                user_data[user_id_str]["coins"] += reward
                save_json("user_data.json", user_data)

            embed = discord.Embed(
                title="🎉 恭喜！",
                description=f"你猜對了！數字就是 **{game['number']}**！",
                color=discord.Color.gold(),
            )
            embed.add_field(name="獎勵", value=f"🪙 +{reward} 金幣")
            await interaction.response.send_message(embed=embed)
            del games[user_id]
            return

        # 提示大小
        hint = "太小了" if number < game["number"] else "太大了"

        # 檢查遊戲是否結束
        if game["attempts"] <= 0:
            embed = discord.Embed(
                title="遊戲結束",
                description=f"很遺憾，你沒能猜中數字！正確數字是 **{game['number']}**",
                color=discord.Color.red(),
            )
            del games[user_id]
        else:
            embed = discord.Embed(
                title="繼續猜！",
                description=f"你的猜測 **{number}** {hint}！",
                color=discord.Color.orange(),
            )
            embed.add_field(name="剩餘嘗試次數", value=f"**{game['attempts']}** 次")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Guess(bot))
