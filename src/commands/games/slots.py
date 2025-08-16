import discord
from discord import app_commands
from discord.ext import commands

import random

from core.classes import Cog
from utils.json_handle import load_json, save_json


class Slot(Cog):
    # 老虎機遊戲
    @app_commands.command(name="slots", description="老虎機小遊戲 (花費 10 金幣)")
    async def slots(self, interaction: discord.Interaction):
        user_data = load_json("user_data.json")

        user_id = str(interaction.user.id)

        if user_id not in user_data or user_data[user_id]["coins"] < 10:
            await interaction.response.send_message(
                "金幣不足或沒有帳戶！最少需要 10 金幣才能玩。", ephemeral=True
            )
            return

        # 扣除金幣
        user_data[user_id]["coins"] -= 10
        save_json("user_data.json", user_data)

        # 生成老虎機結果
        symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "⭐", "7️⃣"]
        result = [random.choice(symbols) for _ in range(3)]

        # 檢查勝利條件
        if result[0] == result[1] == result[2]:
            win_amount = 100
            win_text = "大獎！"
        elif result[0] == result[1] or result[1] == result[2]:
            win_amount = 30
            win_text = "連線獎！"
        else:
            win_amount = 0
            win_text = "沒中獎"

        # 發送結果
        embed = discord.Embed(
            title="🎰 老虎機",
            description=f"**{result[0]} | {result[1]} | {result[2]}**",
            color=discord.Color.purple(),
        )
        embed.add_field(name="結果", value=win_text)

        if win_amount > 0:
            user_data[user_id]["coins"] += win_amount
            save_json("user_data.json", user_data)
            embed.add_field(name="獎金", value=f"🪙 +{win_amount} 金幣")
        else:
            embed.add_field(name="下次運氣更好！", value="再試一次吧！")

        embed.set_footer(text=f"餘額: {user_data[user_id]['coins']} 金幣")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Slot(bot))
