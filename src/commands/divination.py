import discord
from discord import app_commands
from discord.ext import commands

import random
from datetime import datetime

from core.classes import Cog
from utils.json_handle import save_json, load_json


class Divination(Cog):
    """
    占卜系統
    """

    @app_commands.command(name="fortune", description="每日塔羅牌占卜")
    async def fortune(self, interaction: discord.Interaction):

        user_data = load_json("user_data.json")
        tarot_cards = load_json("tarot_cards.json")

        user_id = str(interaction.user.id)

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
        current_time = datetime.now().timestamp()

        # 檢查冷卻時間 (24小時)
        if current_time - user["last_fortune"] < 86400:
            remaining = int(86400 - (current_time - user["last_fortune"]))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.response.send_message(
                f"每日占卜冷卻中！請等待 {hours}小時 {minutes}分鐘 後再試。",
                ephemeral=True,
            )
            return

        # 更新最後占卜時間
        user["last_fortune"] = current_time

        # 檢查是否有幸運加成
        fortune_boost = "fortune_boost" in user.get("inventory", {})

        # 抽取塔羅牌
        cards = []
        meanings = []

        # 抽取3張牌
        for _ in range(3):
            card = random.choice(tarot_cards)
            cards.append(card)

            # 有加成時增加正面解讀機率
            if fortune_boost and random.random() > 0.3:
                meaning = card["meaning"] + " (正面)"
            else:
                # 隨機正負面解讀
                if random.random() > 0.5:
                    meaning = card["meaning"] + " (正面)"
                else:
                    meaning = card["meaning"] + " (負面)"

            meanings.append(meaning)

        # 創建占卜結果
        embed = discord.Embed(
            title="🔮 塔羅牌占卜結果",
            description=f"為 {interaction.user.display_name} 的今日運勢",
            color=discord.Color.purple(),
        )

        # 添加牌面
        card_display = " ".join(card["image"] for card in cards)
        embed.add_field(name="抽到的牌", value=card_display, inline=False)

        # 添加解讀
        for i, meaning in enumerate(meanings):
            embed.add_field(
                name=f"牌 {i+1} - {cards[i]['name']}", value=meaning, inline=False
            )

        # 整體運勢
        positive_count = sum(1 for m in meanings if "正面" in m)
        if positive_count == 3:
            overall = "大吉！今天事事順利！"
        elif positive_count == 2:
            overall = "吉！今天運氣不錯！"
        elif positive_count == 1:
            overall = "平！保持平常心面對。"
        else:
            overall = "凶！今天需謹慎行事。"

        embed.add_field(name="整體運勢", value=overall, inline=False)

        # 獎勵金幣
        reward = random.randint(5, 15)
        user["coins"] += reward
        save_json("user_data.json", user_data)

        embed.set_footer(text=f"獲得每日獎勵: 🪙 {reward} 金幣")

        # 消耗幸運加成
        if fortune_boost:
            user["inventory"]["fortune_boost"] -= 1
            if user["inventory"]["fortune_boost"] <= 0:
                del user["inventory"]["fortune_boost"]
            save_json("user_data.json", user_data)
            embed.add_field(
                name="幸運水晶", value="已消耗一個幸運水晶提升占卜品質", inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Divination(bot))
