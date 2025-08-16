import discord
from discord import app_commands
from discord.ext import commands

from datetime import datetime

from core.classes import Cog
from utils.json_handle import load_json, save_json


class Shop(Cog):
    """
    商店系統
    """

    @app_commands.command(name="shop", description="查看商店物品")
    async def shop(self, interaction: discord.Interaction):
        shop_items = load_json("shop_items.json")
        user_data = load_json("user_data.json")

        embed = discord.Embed(
            title="🛒 商店",
            description="使用 /buy [物品ID] 購買物品",
            color=discord.Color.blue(),
        )

        # 添加物品到商店
        for item in shop_items:
            embed.add_field(
                name=f"{item['name']} (ID: {item['id']})",
                value=f"{item['description']}\n價格: 🪙 {item['price']}",
                inline=False,
            )

        # 顯示用戶金幣餘額
        user_id = str(interaction.user.id)
        coins = user_data[user_id]["coins"] if user_id in user_data else 0
        embed.set_footer(text=f"你的金幣: 🪙 {coins}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="購買商店物品")
    @app_commands.describe(item_id="要購買的物品ID")
    async def buy(self, interaction: discord.Interaction, item_id: str):
        shop_items = load_json("shop_items.json")
        user_data = load_json("user_data.json")

        user_id = str(interaction.user.id)

        # 檢查用戶是否存在
        if user_id not in user_data:
            await interaction.response.send_message(
                "你還沒有帳戶！請先發送一些訊息。", ephemeral=True
            )
            return

        user = user_data[user_id]

        # 查找物品
        item = next((i for i in shop_items if i["id"] == item_id), None)

        if not item:
            await interaction.response.send_message(
                "找不到該物品！請檢查物品ID。", ephemeral=True
            )
            return

        # 檢查金幣是否足夠
        if user["coins"] < item["price"]:
            await interaction.response.send_message(
                f"金幣不足！需要 🪙 {item['price']}，你只有 🪙 {user['coins']}。",
                ephemeral=True,
            )
            return

        # 購買物品
        user["coins"] -= item["price"]

        # 處理不同類型物品
        if item["type"] == "title":
            user["title"] = item["name"]
            result = f"你現在擁有稱號: **{item['name']}**"
        elif item["type"] == "background":
            user["background"] = item["name"]
            result = f"你現在擁有個人背景: **{item['name']}**"
        elif item["type"] == "boost":
            # 雙倍經驗卡
            if item["id"] == "double_xp":
                expire_time = datetime.now().timestamp() + 86400  # 24小時後過期
                user["boosts"]["double_xp"] = expire_time
                result = "你獲得了24小時雙倍經驗加成！"
        elif item["type"] == "perk":
            # 自訂角色顏色
            if item["id"] == "role_color":
                result = "你已解鎖自訂角色顏色權限！請聯繫管理員設定。"
        else:
            # 一般物品
            if item["id"] not in user["inventory"]:
                user["inventory"][item["id"]] = 0
            user["inventory"][item["id"]] += 1
            result = f"你購買了 {item['name']} x1"

        # 保存數據
        save_json("user_data.json", user_data)

        embed = discord.Embed(
            title="🛒 購買成功", description=result, color=discord.Color.green()
        )
        embed.add_field(name="物品", value=item["name"])
        embed.add_field(name="花費", value=f"🪙 {item['price']}")
        embed.add_field(name="餘額", value=f"🪙 {user['coins']}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="查看你的背包")
    async def inventory(self, interaction: discord.Interaction):
        shop_items = load_json("shop_items.json")
        user_data = load_json("user_data.json")

        user_id = str(interaction.user.id)

        if user_id not in user_data or not user_data[user_id].get("inventory"):
            await interaction.response.send_message("你的背包是空的！", ephemeral=True)
            return

        user = user_data[user_id]
        inventory = user["inventory"]

        embed = discord.Embed(
            title="🎒 背包", description="你擁有的物品", color=discord.Color.blue()
        )

        # 添加物品
        for item_id, quantity in inventory.items():
            item = next((i for i in shop_items if i["id"] == item_id), None)
            if item:
                embed.add_field(
                    name=f"{item['name']} x{quantity}",
                    value=item["description"],
                    inline=False,
                )

        # 添加稱號和背景
        if user.get("title"):
            embed.add_field(name="稱號", value=user["title"], inline=False)
        if user.get("background"):
            embed.add_field(name="個人背景", value=user["background"], inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
