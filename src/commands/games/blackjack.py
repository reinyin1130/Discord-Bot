import discord
from discord import app_commands
from discord.ext import commands

import random

from core.classes import Cog
from utils.json_handle import load_json, save_json


def calculate_hand(hand):
    total = sum(hand)
    # 處理Ace
    aces = hand.count(11)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def format_hand(hand):
    return " ".join(str(card) for card in hand)


class Blackjack(Cog):
    # 21點遊戲
    @app_commands.command(name="blackjack", description="21點遊戲 (花費 15 金幣)")
    async def blackjack(self, interaction: discord.Interaction):
        user_data = load_json("user_data.json")

        user_id = str(interaction.user.id)

        if user_id not in user_data or user_data[user_id]["coins"] < 15:
            await interaction.response.send_message(
                "金幣不足或沒有帳戶！最少需要 15 金幣才能玩。", ephemeral=True
            )
            return

        # 扣除金幣
        user_data[user_id]["coins"] -= 15
        save_json("user_data.json", user_data)

        # 初始化遊戲
        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(deck)

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        # 存儲遊戲狀態
        self.bot.games = getattr(self.bot, "games", {})
        self.bot.games[interaction.user.id] = {
            "deck": deck,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "status": "playing",
        }

        # 顯示初始手牌
        embed = discord.Embed(
            title="🃏 21點遊戲",
            description="輸入 `/hit` 要牌 或 `/stand` 停牌",
            color=discord.Color.dark_green(),
        )
        embed.add_field(
            name="你的手牌",
            value=f"{format_hand(player_hand)} (總和: {calculate_hand(player_hand)})",
            inline=False,
        )
        embed.add_field(name="莊家的手牌", value=f"{dealer_hand[0]} ?", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hit", description="21點要牌")
    async def hit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        games = getattr(self.bot, "games", {})

        if user_id not in games or games[user_id]["status"] != "playing":
            await interaction.response.send_message(
                "你沒有進行中的21點遊戲！使用 /blackjack 開始新遊戲。", ephemeral=True
            )
            return

        game = games[user_id]
        game["player_hand"].append(game["deck"].pop())
        player_total = calculate_hand(game["player_hand"])

        # 檢查是否爆牌
        if player_total > 21:
            game["status"] = "busted"
            result = "爆牌！你輸了"
            color = discord.Color.red()
            win_amount = 0
        else:
            result = "繼續遊戲中..."
            color = discord.Color.green()
            win_amount = None

        embed = discord.Embed(title="🃏 21點遊戲 - 要牌", color=color)
        embed.add_field(
            name="你的手牌",
            value=f"{format_hand(game['player_hand'])} (總和: {player_total})",
            inline=False,
        )
        embed.add_field(
            name="莊家的手牌", value=f"{game['dealer_hand'][0]} ?", inline=False
        )
        embed.add_field(name="結果", value=result, inline=False)

        # 處理遊戲結束
        if game["status"] == "busted":
            # 莊家亮牌
            dealer_total = calculate_hand(game["dealer_hand"])
            embed.add_field(
                name="莊家的手牌",
                value=f"{format_hand(game['dealer_hand'])} (總和: {dealer_total})",
                inline=False,
            )

            del games[user_id]
        else:
            embed.set_footer(text="輸入 /hit 要牌 或 /stand 停牌")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stand", description="21點停牌")
    async def stand(self, interaction: discord.Interaction):
        user_data = load_json("user_data.json")

        user_id = interaction.user.id
        games = getattr(self.bot, "games", {})

        if user_id not in games or games[user_id]["status"] != "playing":
            await interaction.response.send_message(
                "你沒有進行中的21點遊戲！使用 /blackjack 開始新遊戲。", ephemeral=True
            )
            return

        game = games[user_id]
        player_total = calculate_hand(game["player_hand"])
        dealer_total = calculate_hand(game["dealer_hand"])

        # 莊家抽牌直到17點或以上
        while dealer_total < 17:
            game["dealer_hand"].append(game["deck"].pop())
            dealer_total = calculate_hand(game["dealer_hand"])

        # 判斷勝負
        if dealer_total > 21:
            result = "莊家爆牌！你贏了！"
            win_amount = 30
            color = discord.Color.gold()
        elif dealer_total > player_total:
            result = "莊家贏了！"
            win_amount = 0
            color = discord.Color.red()
        elif dealer_total < player_total:
            result = "你贏了！"
            win_amount = 30
            color = discord.Color.gold()
        else:
            result = "平手！"
            win_amount = 15
            color = discord.Color.blue()

        # 更新金幣
        user_id_str = str(user_id)
        if user_id_str in user_data:
            user_data[user_id_str]["coins"] += win_amount
            save_json("user_data.json", user_data)

        # 創建結果嵌入
        embed = discord.Embed(title="🃏 21點遊戲 - 結果", color=color)
        embed.add_field(
            name="你的手牌",
            value=f"{format_hand(game['player_hand'])} (總和: {player_total})",
            inline=False,
        )
        embed.add_field(
            name="莊家的手牌",
            value=f"{format_hand(game['dealer_hand'])} (總和: {dealer_total})",
            inline=False,
        )
        embed.add_field(name="結果", value=result, inline=False)

        if win_amount > 0:
            embed.add_field(name="獎金", value=f"🪙 +{win_amount} 金幣")

        # 刪除遊戲狀態
        del games[user_id]

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Blackjack(bot))
