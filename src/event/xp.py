import discord
from discord.ext import commands

import random
from datetime import datetime

from core.classes import Cog
from utils.json_handle import load_json, save_json

from config.const import LEVEL_MULTIPLIER


class XP(Cog):
    """
    等級系統 - 用戶發言時觸發
    """

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        # 忽略機器人自己的消息
        if message.author.bot:
            return

        user_data = load_json("user_data.json")

        user_id = str(message.author.id)

        # 初始化用戶數據
        if user_id not in user_data:
            user_data[user_id] = {
                "exp": 0,
                "level": 1,
                "last_message": 0,
                "coins": 0,
                "inventory": {},
                "title": "",
                "background": "",
                "last_fortune": 0,
                "boosts": {},
            }

        user = user_data[user_id]

        # 防止刷消息 (每60秒獲得一次經驗)
        current_time = datetime.now().timestamp()
        if current_time - user["last_message"] > 60:
            # 計算經驗加成
            exp_multiplier = 1.0
            if "double_xp" in user["boosts"]:
                if current_time < user["boosts"]["double_xp"]:
                    exp_multiplier = 2.0

            # 隨機獲得經驗
            exp_gained = random.randint(5, 15) * exp_multiplier
            user["exp"] += exp_gained
            user["coins"] += random.randint(1, 3)
            user["last_message"] = current_time

            # 檢查升級
            current_level = user["level"]
            exp_needed = current_level * LEVEL_MULTIPLIER

            if user["exp"] >= exp_needed:
                user["level"] += 1
                user["coins"] += current_level * 10  # 升級獎勵金幣

                # 發送升級通知
                embed = discord.Embed(
                    title="🎉 升級了！",
                    description=f"{message.author.mention} 升到了 **{user['level']}級**！",
                    color=discord.Color.gold(),
                )
                embed.add_field(name="金幣獎勵", value=f"🪙 {current_level * 10} 金幣")
                await message.channel.send(embed=embed)

            # 保存數據
            save_json("user_data.json", user_data)

        # 處理命令
        await self.bot.process_commands(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(XP(bot))
