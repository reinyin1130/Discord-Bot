import discord
from discord.ext import commands, tasks

import os
import json
import random
import subprocess

from dotenv import load_dotenv

from utils.json_init import init_json

# 設定機器人
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 啟動事件
@bot.event
async def on_ready():
    print(f"登入身份：{bot.user}")

    paths = [
        "./src/commands",
        "./src/commands/games",
        "./src/event",
    ]

    success = 0
    for path in paths:
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.endswith(".py") and not filename.startswith("__"):
                    try:
                        moudle = path.split("./src/")[-1].replace("/", ".")
                        module_name = f"src.{moudle}.{filename[:-3]}"
                        await bot.load_extension(module_name)
                        success += 1
                    except Exception as e:
                        print(f"❌ 載入擴展 {filename[:-3]} 失敗: {e}")
    print(f"已載入 {success} 個擴展")

    # 載入完所有擴展後再同步
    try:
        synced = await bot.tree.sync()
        print(f"已同步 {len(synced)} 個斜線命令")
    except Exception as e:
        print(f"同步錯誤: {e}")

    # 啟動狀態循環
    change_status.start()


# 狀態循環任務
@tasks.loop(minutes=5)
async def change_status():
    with open("user_data.json", "r") as file:
        user_data = json.load(file)

    statuses = [
        f"/help | {len(bot.guilds)} 個伺服器",
        f"等級系統 | {len(user_data)} 位用戶",
        "小遊戲 | /game",
        "占卜 | /fortune",
        "商店 | /shop",
        "音樂 | /play",
    ]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("錯誤：找不到 Discord Token！請確認 .env 文件設置。")
        exit(1)

    # 檢查FFmpeg是否可用
    try:
        subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("FFmpeg 已安裝，音樂功能可用")
    except FileNotFoundError:
        print("警告: FFmpeg 未安裝，音樂功能可能無法正常運作")

    # 安裝yt-dlp（如果尚未安裝）
    try:
        import yt_dlp

        print("yt-dlp 已安裝")
    except ImportError:
        print("安裝 yt-dlp...")
        try:
            subprocess.run(["pip", "install", "yt-dlp"], check=True)
            print("yt-dlp 安裝成功")
        except Exception as e:
            print(f"安裝 yt-dlp 失敗: {e}")

    init_json()
    bot.run(TOKEN)
